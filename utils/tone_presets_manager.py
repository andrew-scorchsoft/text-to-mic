import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
import customtkinter as ctk
import os

class TonePresetsManager:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Spoken Tone Presets")
        self.dialog.geometry("800x650")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Set the dialog background color
        self.dialog.configure(background="#f0f0f0")
        
        # Center the dialog on the screen
        self.center_dialog()
        
        # Add a variable to track the currently selected tone
        self.current_selected_tone = None
        
        # Set style for a cleaner look
        self.setup_styles()
        
        self.create_dialog()
        self.parent.after(100, self.update_content)

    def setup_styles(self):
        """Configure ttk styles for a clean, modern appearance"""
        style = ttk.Style()
        
        # Use namespaced styles with "TonePresets." prefix to avoid affecting global styles
        # Base frame style that will be used by all frames
        style.configure("TonePresets.TFrame", background="#f0f0f0")
        
        # Update labelframe style with bold and centered title
        style.configure("TonePresets.TLabelframe", borderwidth=0, relief="flat", background="#f0f0f0")
        style.configure("TonePresets.TLabelframe.Label", 
                        foreground="#333333", 
                        background="#f0f0f0", 
                        font=("Arial", 10, "bold"),
                        anchor="center")
        
        # Namespaced button style
        style.configure("TonePresets.TButton", foreground="#333333", background="#f0f0f0", font=("Arial", 10))
        style.map("TonePresets.TButton", 
                 background=[("active", "#e0e0e0"), ("pressed", "#d0d0d0")])
        
        # Namespaced label style
        style.configure("TonePresets.TLabel", foreground="#333333", background="#f0f0f0", font=("Arial", 10))
        
        # Listbox and Text widget styling will be applied directly to those widgets

    def center_dialog(self):
        # Get the parent window position and dimensions
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Calculate position for the dialog
        dialog_width = 800  # Width from geometry
        dialog_height = 650  # Height from geometry
        position_x = parent_x + (parent_width - dialog_width) // 2
        position_y = parent_y + (parent_height - dialog_height) // 2

        # Set the position
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{position_x}+{position_y}")

    def create_dialog(self):
        # Main container frame with padding
        main_frame = ttk.Frame(self.dialog, padding="10", style="TonePresets.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create left panel (tone selection)
        self.create_left_panel(main_frame)
        
        # Create right panel (tone content)
        self.create_right_panel(main_frame)

        # Create bottom frame for main action button
        self.create_bottom_frame()

    def create_left_panel(self, main_frame):
        left_panel = ttk.Frame(main_frame, width=200, style="TonePresets.TFrame")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        # Create labelframe with centered title
        select_frame = ttk.LabelFrame(left_panel, text="Tone Selection", padding="5", style="TonePresets.TLabelframe")
        select_frame.pack(fill=tk.BOTH, expand=True)
        
        # Use grid_propagate to ensure the title is properly centered
        for child in select_frame.winfo_children():
            if child.winfo_class() == 'TLabel':
                child.configure(anchor='center')
                child.place(relx=0.5, rely=0, anchor='n')

        # Listbox for tones with scrollbar
        self.tone_list = tk.Listbox(select_frame, height=8, selectmode=tk.BROWSE, 
                                    bg="#f0f0f0", fg="#333333", 
                                    selectbackground="#0078d7", selectforeground="#ffffff",
                                    font=("Arial", 10))
        tone_scrollbar = ttk.Scrollbar(select_frame, orient=tk.VERTICAL, command=self.tone_list.yview)
        self.tone_list.config(yscrollcommand=tone_scrollbar.set)
        
        self.tone_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        tone_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Populate listbox with "None" option plus tone presets
        all_tones = ["None"] + list(self.parent.tone_presets.keys())
        for tone in all_tones:
            self.tone_list.insert(tk.END, tone)
            if tone == self.parent.current_tone_name:
                self.tone_list.selection_set(all_tones.index(tone))

        # Button frame
        button_frame = ttk.Frame(left_panel, style="TonePresets.TFrame")
        button_frame.pack(fill=tk.X, pady=5)

        # Action buttons
        self.new_button = ttk.Button(button_frame, text="New Tone", command=self.create_new_tone, style="TonePresets.TButton")
        self.delete_button = ttk.Button(button_frame, text="Delete", command=self.delete_current_tone, style="TonePresets.TButton")
        
        self.new_button.pack(side=tk.LEFT, padx=2)
        self.delete_button.pack(side=tk.LEFT, padx=2)

        # Bind selection event
        self.tone_list.bind('<<ListboxSelect>>', self.on_tone_select)

    def on_tone_select(self, event):
        """Handle tone selection and update the current selection."""
        selected_indices = self.tone_list.curselection()
        if selected_indices:
            self.current_selected_tone = self.tone_list.get(selected_indices[0])
            self.update_content()

    def create_right_panel(self, main_frame):
        self.right_panel = ttk.Frame(main_frame, style="TonePresets.TFrame")
        self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create labelframe with centered title
        content_frame = ttk.LabelFrame(self.right_panel, text="Tone Description", padding="5", style="TonePresets.TLabelframe")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Use grid_propagate to ensure the title is properly centered
        for child in content_frame.winfo_children():
            if child.winfo_class() == 'TLabel':
                child.configure(anchor='center')
                child.place(relx=0.5, rely=0, anchor='n')

        self.edit_status_label = ttk.Label(content_frame, foreground="blue", style="TonePresets.TLabel")
        self.edit_status_label.pack(anchor=tk.W, padx=5, pady=(5,0))

        # Create a frame to contain the text widget and scrollbar
        text_frame = ttk.Frame(content_frame, style="TonePresets.TFrame")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create vertical scrollbar only
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create the text widget with word wrap and vertical scrollbar
        self.content_text = tk.Text(text_frame, wrap=tk.WORD,
                                  yscrollcommand=v_scrollbar.set,
                                  bg="#f0f0f0", fg="#333333",
                                  font=("Arial", 10),
                                  relief="solid", borderwidth=1)
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure the scrollbar
        v_scrollbar.config(command=self.content_text.yview)

        self.save_changes_button = ttk.Button(self.right_panel, text="Save Changes", 
                                            command=self.save_content_changes, state='disabled', style="TonePresets.TButton")
        self.save_changes_button.pack(pady=(5, 0), anchor=tk.E)

    def create_bottom_frame(self):
        bottom_frame = ttk.Frame(self.dialog, style="TonePresets.TFrame")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)

        save_button = ctk.CTkButton(
            bottom_frame,
            text="Save Selection and Exit",
            corner_radius=20,
            height=35,
            fg_color="#058705",
            hover_color="#046a38",
            font=("Arial", 13, "bold"),
            command=self.save_and_exit
        )
        save_button.pack(side=tk.BOTTOM, fill=tk.X)

    def update_content(self):
        """Update the content area with the selected tone."""
        if not self.current_selected_tone:
            selected_indices = self.tone_list.curselection()
            if selected_indices:
                self.current_selected_tone = self.tone_list.get(selected_indices[0])
            else:
                return

        # Enable content_text before any operations
        self.content_text.config(state='normal')
        self.content_text.delete('1.0', tk.END)
        
        if self.current_selected_tone == "None":
            self.content_text.insert('1.0', "No tone modifier will be applied to the speech.")
            self.content_text.config(state='disabled')
            self.save_changes_button.config(state='disabled')
            self.delete_button.config(state='disabled')
            self.edit_status_label.config(
                text="(No tone modifier)",
                foreground="gray"
            )
        else:
            self.content_text.insert('1.0', self.parent.tone_presets[self.current_selected_tone])
            self.content_text.config(state='normal')
            self.save_changes_button.config(state='normal')
            self.delete_button.config(state='normal')
            self.edit_status_label.config(
                text=f"{self.current_selected_tone}",
                foreground="blue"
            )

    def save_content_changes(self):
        """Save changes to the current tone content."""
        if not self.current_selected_tone or self.current_selected_tone == "None":
            return
        
        new_content = self.content_text.get("1.0", tk.END).strip()
        if not new_content:
            messagebox.showerror("Error", "Tone description cannot be empty")
            return

        self.parent.tone_presets[self.current_selected_tone] = new_content
        self.parent.save_tone_presets(self.parent.tone_presets)
        messagebox.showinfo("Success", "Tone changes saved successfully")

    def create_new_tone(self):
        """Open dialog for creating a new tone preset."""
        tone_dialog = tk.Toplevel(self.dialog)
        tone_dialog.title("Create New Tone Preset")
        tone_dialog.geometry("600x400")
        tone_dialog.transient(self.dialog)
        tone_dialog.grab_set()
        
        # Set background color for a cleaner look
        tone_dialog.configure(background="#f0f0f0")
        
        # Center the new tone dialog
        dialog_width = 600
        dialog_height = 400
        position_x = self.dialog.winfo_x() + (self.dialog.winfo_width() - dialog_width) // 2
        position_y = self.dialog.winfo_y() + (self.dialog.winfo_height() - dialog_height) // 2
        tone_dialog.geometry(f"{dialog_width}x{dialog_height}+{position_x}+{position_y}")
        
        # Name entry
        name_frame = ttk.Frame(tone_dialog, padding="10", style="TonePresets.TFrame")
        name_frame.pack(fill=tk.X)
        ttk.Label(name_frame, text="Tone Name:", style="TonePresets.TLabel").pack(side=tk.LEFT)
        name_entry = ttk.Entry(name_frame)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Tone description with consistent styling
        desc_frame = ttk.LabelFrame(tone_dialog, text="Tone Description", padding="10", style="TonePresets.TLabelframe")
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Ensure the title is centered
        for child in desc_frame.winfo_children():
            if child.winfo_class() == 'TLabel':
                child.configure(anchor='center')
                child.place(relx=0.5, rely=0, anchor='n')
        
        # Create a frame for the text widget and scrollbar
        text_frame = ttk.Frame(desc_frame, style="TonePresets.TFrame")
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Create vertical scrollbar only
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create the text widget with word wrap and vertical scrollbar
        new_tone_text = tk.Text(text_frame, wrap=tk.WORD, height=15,
                                yscrollcommand=v_scrollbar.set,
                                bg="#ffffff", fg="#333333",
                                font=("Arial", 10),
                                relief="solid", borderwidth=1)
        new_tone_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure the scrollbar
        v_scrollbar.config(command=new_tone_text.yview)

        def save_new_tone():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Please enter a tone name")
                return
            if len(new_name) > 25:
                messagebox.showerror("Error", "Tone name must be 25 characters or less")
                return
            
            new_content = new_tone_text.get("1.0", tk.END).strip()
            if not new_content:
                messagebox.showerror("Error", "Please enter a tone description")
                return

            # Save tone
            self.parent.tone_presets[new_name] = new_content
            self.parent.save_tone_presets(self.parent.tone_presets)

            # Update listbox and select the new tone
            self.tone_list.delete(0, tk.END)
            all_tones = ["None"] + list(self.parent.tone_presets.keys())
            for t in all_tones:
                self.tone_list.insert(tk.END, t)
            
            # Find and select the new tone
            new_tone_index = all_tones.index(new_name)
            self.tone_list.selection_clear(0, tk.END)
            self.tone_list.selection_set(new_tone_index)
            self.tone_list.see(new_tone_index)
            
            # Set the current selected tone and update content
            self.current_selected_tone = new_name
            self.update_content()

            tone_dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(tone_dialog, style="TonePresets.TFrame")
        button_frame.pack(fill=tk.X, pady=10, padx=10)
        ttk.Button(button_frame, text="Save", 
                  command=save_new_tone, style="TonePresets.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=tone_dialog.destroy, style="TonePresets.TButton").pack(side=tk.RIGHT)

    def delete_current_tone(self):
        """Delete the currently selected tone."""
        selected_indices = self.tone_list.curselection()
        if not selected_indices:
            return
        
        tone_name = self.tone_list.get(selected_indices[0])
        if tone_name == "None":
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{tone_name}'?"):
            if tone_name == self.parent.current_tone_name:
                self.parent.current_tone_name = "None"
                self.parent.save_current_tone_to_settings()
                self.parent.update_tone_selection()

            del self.parent.tone_presets[tone_name]
            self.parent.save_tone_presets(self.parent.tone_presets)
            
            # Update listbox
            self.tone_list.delete(0, tk.END)
            for t in ["None"] + list(self.parent.tone_presets.keys()):
                self.tone_list.insert(tk.END, t)
            
            # Set current_selected_tone to "None" before selecting it in the listbox
            self.current_selected_tone = "None"
            self.tone_list.selection_set(0)
            self.update_content()

    def save_and_exit(self):
        """Save the selected tone and close the dialog."""
        if not self.current_selected_tone:
            messagebox.showwarning("No Selection", "Please select a tone before saving")
            return
        
        tone_name = self.current_selected_tone
        
        # First save any content changes if it's not "None"
        if tone_name != "None":
            new_content = self.content_text.get("1.0", tk.END).strip()
            if new_content:
                self.parent.tone_presets[tone_name] = new_content
                self.parent.save_tone_presets(self.parent.tone_presets)
        
        # Then save the selection
        self.parent.current_tone_name = tone_name
        self.parent.save_current_tone_to_settings()
        self.parent.update_tone_selection()
        self.dialog.destroy()
        messagebox.showinfo("Success", f"Now using tone: {tone_name}")

    @staticmethod
    def load_tone_presets(app_instance):
        """Load tone presets from JSON file, creating from template if needed."""
        # Create config directory if it doesn't exist
        config_dir = Path("config")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        tone_presets_file = config_dir / "tone_presets.json"
        example_path = app_instance.resource_path("assets/tone_presets.example.json")
        
        # If tone presets file doesn't exist, copy from example
        if not tone_presets_file.exists():
            try:
                # Check if example file exists
                if not os.path.exists(example_path):
                    # Create default tone presets
                    default_presets = {
                        "Cheerful": "Speak in a cheerful, upbeat tone with enthusiasm.",
                        "Angry": "Sound like you're angry and frustrated.",
                        "Bedtime Story": "Say it like you're reading a bedtime story to a child, soft and soothing.",
                        "News Anchor": "Speak in a professional news anchor tone, clear and formal.",
                        "Excited": "Sound extremely excited and enthusiastic."
                    }
                    
                    # Create and save default presets
                    with open(tone_presets_file, "w", encoding="utf-8") as f:
                        json.dump({"tone_presets": default_presets}, f, indent=2)
                else:
                    # Copy example presets to config directory
                    with open(example_path, "r", encoding="utf-8") as example_file:
                        with open(tone_presets_file, "w", encoding="utf-8") as config_file:
                            config_file.write(example_file.read())
                            
            except Exception as e:
                print(f"Failed to create tone presets file: {e}")
                return {}
                
        # Load presets from file
        try:
            with open(tone_presets_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("tone_presets", {})
        except Exception as e:
            print(f"Error loading tone presets: {e}")
            return {}
    
    @staticmethod
    def save_tone_presets(app_instance, tone_presets):
        """Save tone presets to JSON file."""
        config_dir = Path("config")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        tone_presets_file = config_dir / "tone_presets.json"
        data = {"tone_presets": tone_presets}
        
        try:
            with open(tone_presets_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving tone presets: {e}")
            return False 