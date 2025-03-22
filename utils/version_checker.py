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
        self.notification_frame = None
        
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
        """Display an update notification banner in the app"""
        if self.notification_visible:
            return  # Already showing notification
            
        # Create notification frame
        self.notification_frame = ttk.Frame(self.app, style='Notification.TFrame')
        
        # Configure notification style (light yellow background)
        self.app.style.configure('Notification.TFrame', background='#fff3cd')
        self.app.style.configure('Notification.TLabel', background='#fff3cd', foreground='#856404')
        self.app.style.configure('Notification.TButton', background='#fff3cd')
        
        # Create notification content
        notification_text = message or f"A new version ({latest_version}) is available. You're currently using version {self.current_version}."
        
        label = ttk.Label(
            self.notification_frame, 
            text=notification_text,
            style='Notification.TLabel',
            wraplength=400
        )
        label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        
        # Create buttons
        download_button = ttk.Button(
            self.notification_frame,
            text="Download",
            command=lambda: self.open_download_page(download_url)
        )
        download_button.grid(row=0, column=1, padx=5, pady=10)
        
        close_button = ttk.Button(
            self.notification_frame,
            text="×",
            width=2,
            command=self.dismiss_notification
        )
        close_button.grid(row=0, column=2, padx=(0, 5), pady=10)
        
        # Insert at the top of the application, below menu
        self.notification_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        # Move other content down
        self.app.main_frame.grid(row=1, column=0, sticky="nsew")
        
        self.notification_visible = True
        
    def dismiss_notification(self):
        """Remove the notification banner"""
        if self.notification_frame:
            self.notification_frame.grid_forget()
            self.notification_frame = None
            
            # Move main frame back to top position
            self.app.main_frame.grid(row=0, column=0, sticky="nsew")
            
            self.notification_visible = False
            
    def open_download_page(self, url):
        """Open the download URL in a web browser"""
        webbrowser.open(url)
        self.dismiss_notification() 