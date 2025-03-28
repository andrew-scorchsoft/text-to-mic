import tkinter as tk
from tkinter import ttk, messagebox
from utils.settings_manager import SettingsManager

class AIEditorManager:
    """
    Manages AI copy editing functionality including settings, UI, and text processing.
    """
    
    def __init__(self, app):
        """
        Initialize the AI Editor Manager
        
        Args:
            app: The parent TextToMic application instance
        """
        self.app = app
        self.available_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
        self.default_model = "gpt-4o-mini"
        
    def show_settings(self):
        """Show dialog for AI Editor settings."""
        # Check if API key is available and show info banner if not
        if not self.app.has_api_key:
            messagebox.showinfo(
                "API Key Required",
                "AI copyediting requires an OpenAI API key.\n\n"
                "Please add your API key in Settings first."
            )
            # Optionally, proceed to show settings anyway or return here
            # If you want to stop and not show settings, add: return
        
        # Proceed with showing settings dialog
        settings = self.app.load_settings()
        settings_window = tk.Toplevel(self.app)
        settings_window.title("AI Copy Editing Settings")
        settings_window.grab_set()  # Grab the focus on this toplevel window
        settings_window.geometry("600x420")  # Slightly larger to accommodate explanation text

        main_frame = ttk.Frame(settings_window, padding="10")
        main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        settings_window.columnconfigure(0, weight=1)
        settings_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)  # Make the second column expandable

        # Use the ttk style for uniformity
        style = ttk.Style()
        style.theme_use('clam')

        # Add explanation text at the top
        explanation_text = "This feature allows automatic editing of text using AI. When enabled, text will be refined according to your rules below. Please be aware that enabling this setting will increase the latency of the application."
        
        explanation_label = ttk.Label(main_frame, text=explanation_text, wraplength=550)
        explanation_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # Move the checkbox to the second column to align with other input fields
        enable_completion = tk.BooleanVar(value=settings.get("chat_gpt_completion", False))
        ttk.Label(main_frame, text="Enable AI Copy Editing:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(main_frame, text="", variable=enable_completion).grid(row=1, column=1, sticky=tk.W, pady=2)

        # Model selection
        model_var = tk.StringVar(value=settings.get("model", self.default_model))
        ttk.Label(main_frame, text="Model:").grid(row=2, column=0, sticky=tk.W, pady=2)
        model_menu = ttk.OptionMenu(main_frame, model_var, model_var.get(), *self.available_models)
        model_menu.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

        # Max Tokens selection - expanded options
        max_tokens_var = tk.IntVar(value=settings.get("max_tokens", 750))
        ttk.Label(main_frame, text="Max Tokens:").grid(row=3, column=0, sticky=tk.W, pady=2)
        max_tokens_menu = ttk.OptionMenu(main_frame, max_tokens_var, max_tokens_var.get(), 
                                        100, 250, 500, 750, 1000, 1250, 1500, 2000, 3000, 4000, 5000)
        max_tokens_menu.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)

        # Prompt entry renamed to "Copy Editing Rules" with a Text area
        ttk.Label(main_frame, text="Copy Editing Rules:").grid(row=4, column=0, sticky=tk.NW, pady=2)
        prompt_entry = tk.Text(main_frame, height=8, width=50, background="white", font=("Arial", 10))
        
        # Default prompt example if none exists
        default_prompt = "Edit the text provided to ensure it has a clear, professional tone. Fix any grammatical errors, improve sentence structure, and maintain consistent formatting. Make the language concise and impactful while preserving the original meaning. Make sure to edit text only and do not reply to it."
        
        prompt_entry.insert('1.0', settings.get("prompt", default_prompt))
        prompt_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2)

        # Auto-apply checkbox - moved to second column with clear label
        auto_apply = tk.BooleanVar(value=settings.get("auto_apply_ai_to_recording", False))
        ttk.Label(main_frame, text="Auto Apply to Recordings:").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(main_frame, text="", variable=auto_apply).grid(row=5, column=1, sticky=tk.W, pady=2)

        # Add a label explaining the auto-apply setting
        auto_apply_explanation = "When checked, recordings will be automatically copy edited according to your rules above"
        ttk.Label(main_frame, text=auto_apply_explanation, foreground="#666666", wraplength=450).grid(row=6, column=1, sticky=tk.W, pady=(0, 10))

        # Save Button
        save_btn = ttk.Button(main_frame, text="Save", command=lambda: self.save_settings({
            "chat_gpt_completion": enable_completion.get(),
            "model": model_var.get(),
            "prompt": prompt_entry.get("1.0", tk.END).strip(),
            "auto_apply_ai_to_recording": auto_apply.get(),
            "max_tokens": max_tokens_var.get()
        }))
        save_btn.grid(row=7, column=0, columnspan=2, sticky=tk.E, pady=10)

    def save_settings(self, settings):
        """Save AI copy editing settings and update the UI"""
        SettingsManager.update_settings(settings)
        
        messagebox.showinfo("Settings Updated", "Your settings have been saved successfully.")
        
        # Update the status indicator on the main screen with more specific information
        self.update_status_display()

    def update_status_display(self):
        """Update the status indicator with the current AI editing settings"""
        settings = self.app.load_settings()
        status_text = "AI Copyediting Disabled"
        
        if settings.get("chat_gpt_completion", False):
            if settings.get("auto_apply_ai_to_recording", False):
                status_text = f"AI Copyediting Enabled (Auto) - {settings.get('model', self.default_model)}"
            else:
                status_text = f"AI Copyediting Enabled (Manual) - {settings.get('model', self.default_model)}"
        
        if hasattr(self.app, 'editing_status'):
            self.app.editing_status.config(text=status_text)

    def apply_ai(self, input_text=None, update_ui=False):
        """Apply AI to the given text or the current text in the input box."""
        # Check if API key is available
        if not self.app.has_api_key:
            messagebox.showinfo(
                "API Key Required",
                "AI copyediting requires an OpenAI API key.\n\n"
                "Please add your API key in Settings to use this feature."
            )
            return None
        
        # Get settings to check if AI copy editing is enabled
        settings = self.app.load_settings()
        
        if not settings.get("chat_gpt_completion", False):
            # If called with update_ui=True, we should show a message
            if update_ui:
                messagebox.showinfo(
                    "AI Copy Editing Disabled",
                    "AI copy editing is currently disabled in settings.\n\n"
                    "Please enable it in Settings → AI Copyediting before using this feature."
                )
            # Return the original text unchanged
            return input_text if input_text is not None else self.app.text_input.get("1.0", tk.END).strip()
        
        if input_text is None:
            print("Will apply AI to UI input box")
            text = self.app.text_input.get("1.0", tk.END).strip()
            update_input_box = True
        else:
            print("Will apply AI to input_text")
            text = input_text
            # If update_ui is explicitly set, use that value, otherwise default to False
            update_input_box = update_ui if update_ui is not None else False

        # The rest of the method continues as before
        if settings["max_tokens"]:
            var_max_tokens = settings["max_tokens"]
        else:
            var_max_tokens = 750

        print(f"GPT Settings: {settings}")
        print(f"Max Tokens: {var_max_tokens}")

        # Assuming OpenAI's completion method is configured correctly
        response = self.app.client.chat.completions.create(
            model=settings["model"],
            messages=[
                {"role": "system", "content": settings["prompt"] },
                {"role": "user", "content": "\n\n# Apply to the following (Do not output system prompt or hyphens markup or anything before this line):\n\n-----\n\n" + text + "\n\n-----"}],
            max_tokens=var_max_tokens
        )
        
        processed_text = response.choices[0].message.content
        
        # If we're processing text from the UI directly or update_input_box was specified,
        # update the UI
        if update_input_box:
            self.app.text_input.delete("1.0", tk.END)
            self.app.text_input.insert("1.0", processed_text)
        
        return processed_text 