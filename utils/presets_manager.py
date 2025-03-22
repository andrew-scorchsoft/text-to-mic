import tkinter as tk
from tkinter import ttk, messagebox, Frame, Canvas, Scrollbar
import json
from pathlib import Path
from PIL import Image, ImageTk
import threading
import time

class PresetsManager:
    """
    A class to manage the presets functionality in the Text to Mic application.
    This handles the display, navigation, and interaction with text presets.
    """

    def __init__(self, parent):
        """
        Initialize the PresetsManager.
        
        Args:
            parent: The parent application instance (TextToMic)
        """
        self.parent = parent
        self.presets = self.load_presets()
        self.current_category = "All"
        self.presets_collapsed = True
        self.icon_cache = {}
        
        # Add save debounce variables
        self.save_pending = False
        self.save_timer = None
        self.preset_cards = {}  # Dictionary to store references to preset cards for efficient updates
        
        # Load navigation icons
        self.chevron_right = self.get_icon("assets/icons/chevron-right-black.png", 16)
        self.chevron_down = self.get_icon("assets/icons/chevron-down-black.png", 16)
        self.chevron_left = self.get_icon("assets/icons/chevron-left-black.png", 16)
        self.chevron_right_small = self.get_icon("assets/icons/chevron-right-black.png", 16)
        
        # Store the original row weights to restore when presets are collapsed
        self.original_row_weights = {}
        
        # Initialize the UI components
        self.create_presets_section()
        
        # Bind to window resize for responsive layout
        self.parent.bind("<Configure>", self.on_window_resize)
        
    def create_presets_section(self):
        """Create the presets section UI with accordion behavior."""
        # Accordion frame to show/hide presets section
        self.presets_frame = ttk.Frame(self.parent)
        
        # Create toggle button with icon instead of text
        toggle_frame = ttk.Frame(self.parent)
        toggle_frame.grid(column=0, row=6, columnspan=2, sticky=tk.W)
        
        # Use an icon for the toggle button
        self.presets_button = ttk.Button(
            toggle_frame, 
            image=self.chevron_right,
            compound=tk.LEFT,
            text=" Presets",
            command=self.toggle_presets,
            style="PresetsButton.TButton"
        )
        # Use grid instead of pack for the button to avoid mixing layout managers
        self.presets_button.grid(column=0, row=0, sticky=tk.W, padx=0, pady=2)
        
        # Make presets frame expandable
        self.presets_frame.grid(column=0, row=7, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tabs for categories with scrolling arrows
        self.tab_frame = ttk.Frame(self.presets_frame)
        self.tab_frame.pack(fill=tk.X)

        # Style for flat buttons
        bg_color = self.parent.style.lookup('TFrame', 'background')
        accent_color = "#e0e0e4"  # Slightly darker grey for accents
        
        self.parent.style.configure("Flat.TButton",
                            borderwidth=0,
                            highlightthickness=0,
                            font=("Arial", 12),
                            anchor="center",
                            background=bg_color)
        
        # Create specific style for the presets button with smaller font
        self.parent.style.configure("PresetsButton.TButton",
                            borderwidth=0,
                            highlightthickness=0,
                            font=("Arial", 10),  # Smaller font size
                            anchor="center",
                            background=bg_color)
        
        # Create compact styles for arrow buttons
        self.parent.style.configure("Arrow.TButton",
                            borderwidth=0,
                            highlightthickness=0,
                            padding=2,
                            background=bg_color)
        
        # Create common styles for preset cards
        self.setup_preset_card_styles(bg_color, accent_color)

        # Left arrow with icon
        self.left_arrow = ttk.Button(
            self.tab_frame, 
            image=self.chevron_left,
            command=self.scroll_left, 
            style="Arrow.TButton"
        )
        self.left_arrow.pack(side=tk.LEFT, padx=1)

        # Canvas for scrolling tabs horizontally, removing the horizontal scrollbar
        self.tabs_canvas = Canvas(self.tab_frame, height=30, bg=bg_color, highlightthickness=0)
        self.tabs_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tabs_frame_inner = ttk.Frame(self.tabs_canvas)
        self.tabs_canvas.create_window((0, 0), window=self.tabs_frame_inner, anchor="nw")

        # Right arrow with icon
        self.right_arrow = ttk.Button(
            self.tab_frame, 
            image=self.chevron_right_small,
            command=self.scroll_right, 
            style="Arrow.TButton"
        )
        self.right_arrow.pack(side=tk.RIGHT, padx=1)

        # Presets display area - now using pack with fill=BOTH and expand=True for responsiveness
        self.presets_container = ttk.Frame(self.presets_frame)
        self.presets_container.pack(fill=tk.BOTH, expand=True)
        
        # Presets canvas that will expand with the window
        self.presets_canvas = Canvas(self.presets_container, bg=bg_color, highlightthickness=0)
        self.presets_scrollbar = Scrollbar(self.presets_container, orient="vertical", command=self.presets_canvas.yview)
        self.presets_canvas.configure(yscrollcommand=self.presets_scrollbar.set)

        # Frame inside the canvas to hold presets
        self.presets_scrollable_frame = ttk.Frame(self.presets_canvas)
        self.presets_canvas.create_window((0, 0), window=self.presets_scrollable_frame, anchor="nw")

        # Pack the canvas and scrollbar
        self.presets_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.presets_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the scroll region to update when the frame changes
        self.presets_scrollable_frame.bind("<Configure>", 
                                          lambda e: self.presets_canvas.configure(scrollregion=self.presets_canvas.bbox("all")))

        # Populate tabs and presets
        self.populate_tabs()  # Refresh tabs to show selection
        self.refresh_presets_display()
        # Initially toggle to show/hide based on the default state
        self.toggle_presets()
        self.toggle_presets()
        self.enable_mouse_wheel_scrolling()
        
    def on_window_resize(self, event=None):
        """Handler for window resize events to adjust the presets layout."""
        # Only proceed if event is from the main window and presets are visible
        if event and event.widget == self.parent and not self.presets_collapsed:
            # Schedule a refresh after a short delay to prevent excessive updates during resize
            if hasattr(self, 'resize_timer') and self.resize_timer:
                self.parent.after_cancel(self.resize_timer)
            self.resize_timer = self.parent.after(100, self.refresh_presets_display)
        
    def _adjust_row_weights(self):
        """Adjust row weights to prioritize presets area expansion."""
        # Store current weights if we haven't already
        if not self.original_row_weights:
            for i in range(8):  # Store weights for all relevant rows (0-7)
                self.original_row_weights[i] = self.parent.grid_rowconfigure(i, "weight")
        
        # Set all main content rows to have weight 0 (fixed height)
        for i in range(7):
            self.parent.grid_rowconfigure(i, weight=0)
            
        # Set presets row to have all the weight (expandable)
        self.parent.grid_rowconfigure(7, weight=1)
            
    def _restore_row_weights(self):
        """Restore original row weights when presets are collapsed."""
        if self.original_row_weights:
            for row, weight in self.original_row_weights.items():
                self.parent.grid_rowconfigure(row, weight=weight)
        
        # Reset presets row weight
        self.parent.grid_rowconfigure(7, weight=0)
        
        # Ensure toggle button row is properly weighted
        self.parent.grid_rowconfigure(6, weight=0)

    def setup_preset_card_styles(self, bg_color, accent_color):
        """Set up common styles for preset cards once to avoid recreating them repeatedly."""
        preset_bg_color = "#f0f4f8"  # Light blue-gray that contrasts with the main background
        text_color = self.parent.style.lookup('TLabel', 'foreground')
        
        # Common styles for cards, buttons, and labels
        self.parent.style.configure('PresetCard.TFrame', 
                            background=preset_bg_color,
                            borderwidth=0,
                            relief="flat")
                            
        self.parent.style.configure('PresetBottom.TFrame', 
                            background=preset_bg_color)
                            
        self.parent.style.configure('PresetLabel.TLabel', 
                            background=preset_bg_color,
                            foreground=text_color)
                            
        self.parent.style.configure('PresetButton.TButton',
                            borderwidth=0,
                            highlightthickness=0,
                            background=preset_bg_color)
        
        # Cache common icons
        self.heart_icon = self.get_icon("assets/icons/heart-black.png", 24)
        self.heart_filled_icon = self.get_icon("assets/icons/heart-fill-black.png", 24)
        self.delete_icon = self.get_icon("assets/icons/delete-black.png", 24)

    def scroll_left(self):
        """Scroll the tabs canvas to the left."""
        self.tabs_canvas.xview_scroll(-5, "units")

    def scroll_right(self):
        """Scroll the tabs canvas to the right."""
        self.tabs_canvas.xview_scroll(5, "units")

    def enable_mouse_wheel_scrolling(self):
        """Enable conditional mouse wheel scrolling for the presets canvas and category tabs canvas."""

        def on_vertical_scroll(event):
            # Scroll the presets_canvas vertically
            if event.num == 4:  # macOS scroll up
                self.presets_canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # macOS scroll down
                self.presets_canvas.yview_scroll(1, "units")
            else:  # Windows and Linux
                self.presets_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_horizontal_scroll(event):
            # Scroll the tabs_canvas horizontally
            if event.num == 4:  # macOS scroll left
                self.tabs_canvas.xview_scroll(-1, "units")
            elif event.num == 5:  # macOS scroll right
                self.tabs_canvas.xview_scroll(1, "units")
            else:  # Windows and Linux
                self.tabs_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        # Bind scroll events when mouse enters or leaves the presets canvas area
        self.presets_canvas.bind("<Enter>", lambda e: self.presets_canvas.bind_all("<MouseWheel>", on_vertical_scroll))
        self.presets_canvas.bind("<Leave>", lambda e: self.presets_canvas.unbind_all("<MouseWheel>"))

        # Bind scroll events when mouse enters or leaves the tabs canvas area
        self.tabs_canvas.bind("<Enter>", lambda e: self.tabs_canvas.bind_all("<MouseWheel>", on_horizontal_scroll))
        self.tabs_canvas.bind("<Leave>", lambda e: self.tabs_canvas.unbind_all("<MouseWheel>"))

    def populate_tabs(self):
        """Populate the tabs for different preset categories."""
        # Clear current tabs
        for widget in self.tabs_frame_inner.winfo_children():
            widget.destroy()

        # Add "All" and "Favourites" tabs along with dynamic categories
        for category in ["All", "Favourites"] + [cat["category"] for cat in self.presets if cat["category"] not in ["All", "Favourites"]]:
            btn = ttk.Button(self.tabs_frame_inner, text=category, command=lambda c=category: self.switch_category(c))
            btn.pack(side=tk.LEFT, padx=2)

            # Style selected category
            if category == self.current_category:
                btn.state(['pressed'])  # Visual style for selected tab
            else:
                btn.state(['!pressed'])

    def switch_category(self, category):
        """Switch displayed category."""
        self.current_category = category
        self.populate_tabs()  # Refresh tabs to show selection
        self.refresh_presets_display()

    def refresh_presets_display(self):
        """Refresh displayed presets based on selected category."""
        # Clear existing items in the scrollable frame
        for widget in self.presets_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Clear the preset cards tracking dictionary
        self.preset_cards = {}

        # Debounce - cancel any previous refresh call if pending
        if hasattr(self, 'refresh_handle'):
            self.parent.after_cancel(self.refresh_handle)
        self.refresh_handle = self.parent.after(100, self._populate_presets)

    def _populate_presets(self):
        """Populate presets into grid layout with responsive columns."""
        # Filter presets based on current category
        display_phrases = []
        if self.current_category == "All":
            for cat in self.presets:
                display_phrases.extend(cat["phrases"])
        elif self.current_category == "Favourites":
            for cat in self.presets:
                display_phrases.extend([p for p in cat["phrases"] if p["isFavourite"]])
        else:
            display_phrases = next((cat["phrases"] for cat in self.presets if cat["category"] == self.current_category), [])

        # Clear existing preset layout
        for widget in self.presets_scrollable_frame.winfo_children():
            widget.destroy()
            
        # Calculate number of columns based on available width
        canvas_width = self.presets_canvas.winfo_width()
        # Ensure we have a minimum width to calculate with
        if canvas_width < 50:  # If the canvas is too narrow or not yet realized
            canvas_width = self.parent.winfo_width() - 30  # Estimate canvas width
            
        # Calculate number of columns (minimum 1, maximum 20)
        min_card_width = 140  # Minimum width for each card
        num_columns = max(1, min(20, canvas_width // min_card_width))
        
        # Dynamically adjust card width based on available space
        preset_width = max(min_card_width, canvas_width // num_columns - 8)
        preset_height = 100
        
        # Configure columns to fill available space
        for col in range(num_columns):
            self.presets_scrollable_frame.columnconfigure(col, weight=1)

        # Populate filtered presets in grid layout
        for i, phrase in enumerate(display_phrases):
            # Create a unique identifier for the card
            card_id = f"{phrase['text']}"
            
            # Calculate row and column based on the dynamic column count
            row = i // num_columns
            col = i % num_columns
            
            # Create a frame with no border for cleaner look
            frame = ttk.Frame(self.presets_scrollable_frame, width=preset_width, height=preset_height)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            frame.grid_propagate(False)
            
            # Create inner frame with distinct background and no border - use common style
            inner_frame = ttk.Frame(frame, style='PresetCard.TFrame')
            inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

            # Make sure all rows are expandable too
            self.presets_scrollable_frame.grid_rowconfigure(row, weight=1)
            
            # Text label with truncation for long text - use common style
            wrapped_text = self.wrap_text(phrase["text"], max_lines=3, max_chars_per_line=20)
            label = ttk.Label(inner_frame, text=wrapped_text, anchor="center", justify="center", 
                            width=20, style='PresetLabel.TLabel')
            label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            label.bind("<Button-1>", lambda e, t=phrase["text"]: self.insert_text(t))
            label.bind("<Double-Button-1>", lambda e, t=phrase["text"]: self.play_preset(t))
            
            # Bottom frame for icons - use common style
            bottom_frame = ttk.Frame(inner_frame, style='PresetBottom.TFrame')
            bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

            # Choose correct heart icon based on favorite status
            fav_img = self.heart_filled_icon if phrase["isFavourite"] else self.heart_icon
            
            # Favourite button with image - use common style and command that includes card_id
            fav_btn = ttk.Button(bottom_frame, image=fav_img, 
                              command=lambda p=phrase, c_id=card_id: self.toggle_favourite(p, c_id), 
                              style='PresetButton.TButton')
            fav_btn.pack(side=tk.RIGHT, padx=2)

            # Delete button with image - use common style
            del_btn = ttk.Button(bottom_frame, image=self.delete_icon, 
                             command=lambda t=phrase["text"]: self.delete_preset(self.current_category, t), 
                             style='PresetButton.TButton')
            del_btn.pack(side=tk.RIGHT, padx=2)
            
            # Store references to the card components for efficient updates
            self.preset_cards[card_id] = {
                'frame': frame,
                'inner_frame': inner_frame,
                'label': label,
                'bottom_frame': bottom_frame,
                'fav_btn': fav_btn,
                'del_btn': del_btn,
                'phrase': phrase
            }

        # Update scroll region after populating all items
        self.presets_canvas.configure(scrollregion=self.presets_canvas.bbox("all"))

    def update_preset_card(self, card_id):
        """Update a single preset card without refreshing the entire display."""
        if card_id not in self.preset_cards:
            return
            
        card = self.preset_cards[card_id]
        phrase = card['phrase']
        
        # Update the favorite button image based on current state
        fav_img = self.heart_filled_icon if phrase["isFavourite"] else self.heart_icon
        card['fav_btn'].configure(image=fav_img)

    def get_icon(self, icon_path, size=24):
        """
        Load and resize an icon, caching the result for later use.
        
        Args:
            icon_path: Path to the icon file
            size: Size to resize the icon to (square)
            
        Returns:
            A PhotoImage object with the icon
        """
        # Create a cache key based on path and size
        cache_key = f"{icon_path}_{size}"
        
        # Check if icon is already in cache
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        # Load and resize the icon
        try:
            # Use resource_path to get the correct path
            full_path = self.parent.resource_path(icon_path)
            
            # Use PIL to open and resize the image
            img = Image.open(full_path)
            img = img.resize((size, size), Image.LANCZOS)
            
            # Convert to PhotoImage
            photo_img = ImageTk.PhotoImage(img)
            
            # Store in cache
            self.icon_cache[cache_key] = photo_img
            
            return photo_img
        except Exception as e:
            print(f"Error loading icon {icon_path}: {e}")
            # Return a default empty image
            return tk.PhotoImage(width=size, height=size)

    def wrap_text(self, text, max_lines=3, max_chars_per_line=20):
        """
        Wrap text to fit within a limited number of lines and characters.
        
        Args:
            text: The text to wrap
            max_lines: Maximum number of lines to display
            max_chars_per_line: Maximum characters per line
            
        Returns:
            The wrapped text with ellipsis if truncated
        """
        words = text.split()
        wrapped_text = ""
        line = ""
        line_count = 0

        for word in words:
            if len(line + word) <= max_chars_per_line:
                line += word + " "
            else:
                wrapped_text += line.strip() + "\n"
                line = word + " "
                line_count += 1
                if line_count >= max_lines - 1:  # Leave space for ellipsis
                    break

        # Add final line and handle overflow with ellipsis
        wrapped_text += line.strip()
        if line_count >= max_lines - 1 and len(wrapped_text.splitlines()) >= max_lines:
            wrapped_text = "\n".join(wrapped_text.splitlines()[:max_lines - 1]) + "\n..."

        return wrapped_text

    def insert_text(self, text):
        """Insert preset text into the text area."""
        self.parent.text_input.delete("1.0", tk.END)
        self.parent.text_input.insert("1.0", text)

    def play_preset(self, text):
        """Insert text and play audio immediately."""
        self.insert_text(text)
        self.parent.submit_text()

    def toggle_favourite(self, phrase, card_id=None):
        """Toggle the favourite status of a preset."""
        phrase["isFavourite"] = not phrase["isFavourite"]
        
        # If we have the card_id, update just that card - much faster than refreshing everything
        if card_id and card_id in self.preset_cards:
            self.update_preset_card(card_id)
        else:
            # Otherwise, refresh the entire display (fallback, should rarely happen)
            self.refresh_presets_display()
        
        # Debounce the save operation to avoid writing to disk on every toggle
        self.debounced_save()

    def debounced_save(self):
        """Save presets with debouncing to avoid frequent disk writes."""
        # Cancel any pending save
        if self.save_timer:
            self.parent.after_cancel(self.save_timer)
        
        # Schedule a new save operation
        self.save_timer = self.parent.after(1000, self._perform_save)
        
    def _perform_save(self):
        """Actually perform the save operation after debounce."""
        # Use threading to avoid blocking the UI
        threading.Thread(target=self.save_presets, daemon=True).start()
        self.save_timer = None

    def toggle_presets(self):
        """Toggle the visibility of the presets panel."""
        if self.presets_collapsed:
            # EXPANDING presets
            self.presets_frame.grid()
            # Update button icon to down chevron while preserving text
            self.presets_button.configure(image=self.chevron_down, text=" Presets")
            
            # Use parent's class constants for geometry instead of old properties
            banner_hidden = self.parent.banner_var.get() if hasattr(self.parent, 'banner_var') else False
            
            # Calculate a width that preserves the current width if it's larger than default
            current_width = self.parent.winfo_width()
            width_to_use = max(current_width, self.parent.BASE_WIDTH)
            
            if banner_hidden:
                self.parent.geometry(f"{width_to_use}x{self.parent.BASE_HEIGHT_NO_BANNER}")
            else:
                self.parent.geometry(f"{width_to_use}x{self.parent.BASE_HEIGHT_WITH_BANNER}")
            
            # Adjust row weights to give all expansion space to presets
            self._adjust_row_weights()
            
            # Refresh the presets display to adjust for the new window size
            self.refresh_presets_display()
        else:
            # COLLAPSING presets
            self.presets_frame.grid_remove()
            # Update button icon to right chevron while preserving text
            self.presets_button.configure(image=self.chevron_right, text=" Presets")
            
            # Use parent's class constants for geometry
            banner_hidden = self.parent.banner_var.get() if hasattr(self.parent, 'banner_var') else False
            
            # Calculate a width that preserves the current width if it's larger than default
            current_width = self.parent.winfo_width()
            width_to_use = max(current_width, self.parent.BASE_WIDTH)
            
            # Always ensure minimum height based on constants regardless of previous manual resizing
            if banner_hidden:
                # Ensure the minimum height without banner
                minimum_height = self.parent.COLLAPSED_HEIGHT_NO_BANNER
                self.parent.geometry(f"{width_to_use}x{minimum_height}")
            else:
                # Ensure the minimum height with banner
                minimum_height = self.parent.COLLAPSED_HEIGHT_WITH_BANNER
                self.parent.geometry(f"{width_to_use}x{minimum_height}")
            
            # Restore original row weights
            self._restore_row_weights()
            
            # Force re-grid of toggle button to ensure it's properly positioned
            if hasattr(self, 'presets_button') and self.presets_button.winfo_exists():
                self.presets_button.grid_configure(column=0, row=0, sticky=tk.W, padx=0, pady=2)
        
        # Update tracking of collapsed state
        self.presets_collapsed = not self.presets_collapsed
        
        # Update parent's tracking variable
        if hasattr(self.parent, 'presets_collapsed'):
            self.parent.presets_collapsed = self.presets_collapsed

    def save_current_text_as_preset(self):
        """Save current text to the selected category as a preset."""
        text = self.parent.text_input.get("1.0", tk.END).strip()
        category = self.parent.category_var.get()
        if text and category != "Select Category":
            self.add_preset(category, text, is_favourite=False)
            # Show success message with category information
            messagebox.showinfo("Save Successful", f"The text has been successfully saved to the category: '{category}'.")
        else:
            messagebox.showinfo("Error", "Please enter text and select a category before saving.")

    def show_save_preset_dialog(self):
        """Show a dialog to save the current text as a preset."""
        text = self.parent.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Error", "Please enter some text before saving as a preset.")
            return

        # Create dialog window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Save As Preset")
        dialog.geometry("300x200")
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.focus_set()

        # Add widgets to the dialog
        ttk.Label(dialog, text="Enter preset category:").pack(pady=(15, 5))
        
        # Add existing categories dropdown
        categories = ["Select Category"] + list(set([cat["category"] for cat in self.presets]))
        category_var = tk.StringVar(value="Select Category")
        
        category_combo = ttk.Combobox(dialog, textvariable=category_var, values=categories)
        category_combo.pack(pady=5, padx=20, fill=tk.X)
        
        ttk.Label(dialog, text="Or enter a new category:").pack(pady=(10, 5))
        
        new_category_entry = ttk.Entry(dialog)
        new_category_entry.pack(pady=5, padx=20, fill=tk.X)

        def save_preset():
            new_category = new_category_entry.get().strip()
            selected_category = category_var.get()
            
            # Use new category if provided, otherwise use the dropdown selection
            category = new_category if new_category else selected_category
            
            if category and category != "Select Category":
                self.add_preset(category, text, is_favourite=False)
                messagebox.showinfo("Save Successful", f"The text has been successfully saved to the category: '{category}'.")
                dialog.destroy()
            else:
                messagebox.showinfo("Error", "Please select an existing category or enter a new one.")
        
        # Add save button
        save_button = ttk.Button(dialog, text="Save", command=save_preset)
        save_button.pack(pady=15)
        
        # Center the dialog on the parent window
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

    def load_presets(self):
        """
        Load presets from the JSON file, copying from example if necessary.
        
        Returns:
            List of preset categories with their phrases
        """
        presets_path = Path("config/presets.json")
        example_path = self.parent.resource_path("assets/presets.example.json")  # Path for the example file

        # Check if presets.json exists, and if not, copy presets.example.json to config
        if not presets_path.exists():
            try:
                # Ensure config directory exists
                presets_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy example presets to config directory
                with open(example_path, "r", encoding="utf-8") as example_file:
                    with open(presets_path, "w", encoding="utf-8") as config_file:
                        config_file.write(example_file.read())
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy example presets: {e}")
                return []  # Return empty if unable to load or copy presets

        # Load presets.json as usual
        try:
            with open(presets_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("presets", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", f"Error loading presets: {e}")
            return []  # Default to empty if load fails

    def save_presets(self):
        """Save presets to the JSON file."""
        data = {"presets": self.presets}
        with open("config/presets.json", "w") as f:
            json.dump(data, f, indent=2)

    def add_preset(self, category, text, is_favourite=False):
        """
        Add a new preset and save it.
        
        Args:
            category: The category to add the preset to
            text: The text of the preset
            is_favourite: Whether the preset is a favorite
        """
        for cat in self.presets:
            if cat["category"] == category:
                cat["phrases"].append({"text": text, "isFavourite": is_favourite})
                break
        else:
            # Add a new category if not found
            self.presets.append({"category": category, "phrases": [{"text": text, "isFavourite": is_favourite}]})
        
        # Save and refresh
        self.debounced_save()
        self.refresh_presets_display()

    def delete_preset(self, category, text):
        """
        Delete a preset by category and text.
        
        Args:
            category: The category of the preset
            text: The text of the preset to delete
        """
        for cat in self.presets:
            if cat["category"] == category:
                cat["phrases"] = [p for p in cat["phrases"] if p["text"] != text]
                break
                
        # Save and refresh 
        self.debounced_save()
        self.refresh_presets_display() 