import threading
import requests
import json
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from packaging import version
import time

class VersionChecker:
    def __init__(self, app, version):
        self.app = app
        self.current_version = version
        self.version_url = "https://www.scorchsoft.com/public/blog/text-to-mic/leatest-version.json"
        self.notification_visible = False
        self.notification_window = None
        
    def check_version(self, show_result=True):
        """
        Check if a new version is available.
        If show_result is True, show a message even if no new version is found.
        """
        thread = threading.Thread(target=self._check_version_thread, args=(show_result,))
        thread.daemon = True  # Make thread terminate when main program exits
        thread.start()
        
    def _check_version_thread(self, show_result):
        """Run the version check in a background thread to avoid blocking the UI"""
        try:
            # Add a small timeout to prevent hanging
            response = requests.get(self.version_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("latestVersion")
                download_url = data.get("downloadUrl")
                message = data.get("notificationMessage")
                
                # Ensure these values are present
                if not latest_version or not download_url:
                    if show_result:
                        self.app.after(0, lambda: messagebox.showwarning(
                            "Version Check Failed", 
                            "The update information is incomplete. Please try again later."
                        ))
                    return
                
                # Use packaging.version for proper version comparison
                try:
                    if version.parse(latest_version) > version.parse(self.current_version):
                        # New version available - show notification in UI thread
                        self.app.after(0, lambda: self.show_update_notification(latest_version, download_url, message))
                    elif show_result:
                        # No new version, but user requested check
                        self.app.after(0, lambda: messagebox.showinfo(
                            "Version Check", 
                            f"You have the latest version ({self.current_version})."
                        ))
                except (version.InvalidVersion, TypeError) as e:
                    if show_result:
                        self.app.after(0, lambda: messagebox.showwarning(
                            "Version Check Failed", 
                            f"Could not compare versions: {str(e)}"
                        ))
            else:
                if show_result:
                    self.app.after(0, lambda: messagebox.showwarning(
                        "Version Check Failed", 
                        f"Could not check for updates. Server returned status code: {response.status_code}"
                    ))
        except requests.RequestException as e:
            if show_result:
                self.app.after(0, lambda: messagebox.showwarning(
                    "Version Check Failed", 
                    f"Could not connect to update server: {str(e)}"
                ))
        except json.JSONDecodeError:
            if show_result:
                self.app.after(0, lambda: messagebox.showwarning(
                    "Version Check Failed", 
                    "Invalid update information received."
                ))
        except Exception as e:
            if show_result:
                self.app.after(0, lambda: messagebox.showwarning(
                    "Version Check Failed", 
                    f"Could not check for updates: {str(e)}"
                ))
    
    def show_update_notification(self, latest_version, download_url, message):
        """Display an update notification banner as an overlay"""
        if self.notification_visible:
            return  # Already showing notification
        
        # Create a new toplevel window for the notification
        self.notification_window = tk.Toplevel(self.app)
        self.notification_window.overrideredirect(True)  # Remove window decorations
        self.notification_window.attributes('-topmost', True)  # Keep on top
        
        # Calculate position (aligned with top of main window)
        app_x = self.app.winfo_rootx()
        app_y = self.app.winfo_rooty()
        app_width = self.app.winfo_width()
        
        # Configure the notification window
        bg_color = '#fff3cd'  # Light yellow background
        fg_color = '#856404'  # Darker yellow/brown text
        
        # Create the main frame in the notification window
        self.notification_frame = ttk.Frame(self.notification_window, style='Notification.TFrame')
        self.notification_frame.pack(fill='both', expand=True)
        
        # Configure styles
        self.app.style.configure('Notification.TFrame', background=bg_color)
        self.app.style.configure('Notification.TLabel', background=bg_color, foreground=fg_color)
        self.app.style.map('Notification.TButton',
                          background=[('active', bg_color), ('!active', bg_color)],
                          foreground=[('active', fg_color), ('!active', fg_color)])
        
        # Create notification content
        notification_text = message or f"A new version ({latest_version}) is available. You're currently using version {self.current_version}."
        
        label = ttk.Label(
            self.notification_frame, 
            text=notification_text,
            style='Notification.TLabel',
            wraplength=app_width - 150  # Allow for button width
        )
        label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        
        # Create buttons
        button_frame = ttk.Frame(self.notification_frame, style='Notification.TFrame')
        button_frame.grid(row=0, column=1, padx=5, pady=5)
        
        download_button = ttk.Button(
            button_frame,
            text="Download",
            style='Notification.TButton',
            command=lambda: self.open_download_page(download_url)
        )
        download_button.pack(side='left', padx=5)
        
        close_button = ttk.Button(
            button_frame,
            text="×",
            width=2,
            style='Notification.TButton',
            command=self.dismiss_notification
        )
        close_button.pack(side='left')
        
        # Position the window and set its size
        self.notification_window.update_idletasks()  # Update to get correct dimensions
        notification_height = self.notification_window.winfo_reqheight()
        
        # Mark notification as visible first so _reposition_notification will work
        self.notification_visible = True
        
        # Setup event binding to follow main window if it's moved
        self.app.bind("<Configure>", self._reposition_notification)
        
        # Add bindings for window minimize/restore events
        self.app.bind("<Unmap>", self._handle_window_unmap)
        self.app.bind("<Map>", self._handle_window_map)
        
        # Use the reposition function to set initial position and size
        # This ensures consistent sizing between initial load and repositioning
        self._reposition_notification()
        
    def _handle_window_unmap(self, event=None):
        """Hide the notification when main window is minimized"""
        if self.notification_visible and self.notification_window:
            self.notification_window.withdraw()
            
    def _handle_window_map(self, event=None):
        """Show the notification when main window is restored"""
        if self.notification_visible and self.notification_window:
            self.notification_window.deiconify()
            # Reposition after showing
            self._reposition_notification()
            
    def _reposition_notification(self, event=None):
        """Reposition the notification window to stay at the top of the main window"""
        if self.notification_visible and self.notification_window:
            app_x = self.app.winfo_rootx()
            app_y = self.app.winfo_rooty()
            app_width = self.app.winfo_width()
            
            # Subtract a small amount to ensure it doesn't extend beyond the window
            adjusted_width = app_width - 5  # Adjust by 4 pixels to account for borders
            
            # Update the width and position
            notification_height = self.notification_window.winfo_height()
            self.notification_window.geometry(f"{adjusted_width}x{notification_height}+{app_x}+{app_y}")
        
    def dismiss_notification(self):
        """Remove the notification banner"""
        if self.notification_window:
            # Unbind all the events first
            self.app.unbind("<Configure>")
            self.app.unbind("<Unmap>")
            self.app.unbind("<Map>")
            
            # Destroy the window
            self.notification_window.destroy()
            self.notification_window = None
            
            self.notification_visible = False
            
    def open_download_page(self, url):
        """Open the download URL in a web browser"""
        webbrowser.open(url)
        self.dismiss_notification() 