"""
SME - Login Screen UI (Updated with Custom Domain Support)
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional
from config.constants import COLOR_SUCCESS


class LoginScreen(ctk.CTkFrame):
    """Login screen for Salesforce authentication"""
    
    def __init__(self, parent, on_login_success: Callable):
        """
        Initialize login screen
        
        Args:
            parent: Parent widget
            on_login_success: Callback function when login succeeds
        """
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.columnconfigure(1, weight=1)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup login UI components"""
        # Title
        title_label = ctk.CTkLabel(
            self, 
            text="Salesforce Login", 
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(60, 50))
        
        # Org Type (ROW 1 - moved to top)
        ctk.CTkLabel(
            self, 
            text="Environment:", 
            anchor="w", 
            font=ctk.CTkFont(size=14)
        ).grid(row=1, column=0, padx=15, pady=15, sticky="w")
        
        org_frame = ctk.CTkFrame(self, fg_color="transparent")
        org_frame.grid(row=1, column=1, padx=15, pady=15, sticky="w")
        
        self.org_type_var = ctk.StringVar(value="Production")
        
        ctk.CTkRadioButton(
            org_frame, 
            text="Production", 
            variable=self.org_type_var, 
            value="Production",
            font=ctk.CTkFont(size=13),
            command=self._on_org_type_change
        ).pack(side="left", padx=(0, 30))
        
        ctk.CTkRadioButton(
            org_frame, 
            text="Sandbox/Test", 
            variable=self.org_type_var, 
            value="Sandbox",
            font=ctk.CTkFont(size=13),
            command=self._on_org_type_change
        ).pack(side="left")
        
        # Custom Domain (ROW 2 - right after Environment)
        ctk.CTkLabel(
            self, 
            text="Custom Domain:", 
            anchor="w", 
            font=ctk.CTkFont(size=14)
        ).grid(row=2, column=0, padx=15, pady=15, sticky="w")
        
        custom_domain_frame = ctk.CTkFrame(self, fg_color="transparent")
        custom_domain_frame.grid(row=2, column=1, padx=15, pady=15, sticky="ew")
        custom_domain_frame.columnconfigure(1, weight=1)
        
        # Custom Domain Checkbox
        self.custom_domain_var = ctk.BooleanVar(value=False)
        self.custom_domain_checkbox = ctk.CTkCheckBox(
            custom_domain_frame,
            text="Use Custom Domain",
            variable=self.custom_domain_var,
            font=ctk.CTkFont(size=13),
            command=self._toggle_custom_domain
        )
        self.custom_domain_checkbox.grid(row=0, column=0, sticky="w")
        
        # Custom Domain Entry (initially disabled)
        self.custom_domain_entry = ctk.CTkEntry(
            custom_domain_frame,
            placeholder_text="mycompany.my.salesforce.com",
            height=40,
            font=ctk.CTkFont(size=13),
            state="disabled"
        )
        self.custom_domain_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        # Help text for custom domain
        self.custom_domain_help = ctk.CTkLabel(
            custom_domain_frame,
            text="💡 Enter your org's custom domain (without https://)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.custom_domain_help.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))
        self.custom_domain_help.grid_remove()  # Hide initially
        
        # Username (ROW 3)
        ctk.CTkLabel(
            self, 
            text="Username:", 
            anchor="w", 
            font=ctk.CTkFont(size=14)
        ).grid(row=3, column=0, padx=15, pady=15, sticky="w")
        
        self.username_entry = ctk.CTkEntry(self, width=400, height=40, font=ctk.CTkFont(size=13))
        self.username_entry.grid(row=3, column=1, padx=15, pady=15, sticky="ew")
        
        # Password (ROW 4)
        ctk.CTkLabel(
            self, 
            text="Password:", 
            anchor="w", 
            font=ctk.CTkFont(size=14)
        ).grid(row=4, column=0, padx=15, pady=15, sticky="w")
        
        self.password_entry = ctk.CTkEntry(self, width=400, height=40, show="*", font=ctk.CTkFont(size=13))
        self.password_entry.grid(row=4, column=1, padx=15, pady=15, sticky="ew")
        
        # Security Token (ROW 5)
        ctk.CTkLabel(
            self, 
            text="Security Token:", 
            anchor="w", 
            font=ctk.CTkFont(size=14)
        ).grid(row=5, column=0, padx=15, pady=15, sticky="w")
        
        self.token_entry = ctk.CTkEntry(self, width=400, height=40, show="*", font=ctk.CTkFont(size=13))
        self.token_entry.grid(row=5, column=1, padx=15, pady=15, sticky="ew")
        
        # Login Button (ROW 6)
        self.login_button = ctk.CTkButton(
            self, 
            text="Connect to Salesforce", 
            command=self._handle_login,
            height=50, 
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.login_button.grid(row=6, column=0, columnspan=2, pady=60, sticky="ew", padx=15)
        
        # Bind Enter key to login
        self.username_entry.bind("<Return>", lambda e: self._handle_login())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())
        self.token_entry.bind("<Return>", lambda e: self._handle_login())
        self.custom_domain_entry.bind("<Return>", lambda e: self._handle_login())
    
    def _on_org_type_change(self):
        """Handle org type radio button change"""
        # If user selects Production or Sandbox, uncheck custom domain
        if self.custom_domain_var.get():
            self.custom_domain_var.set(False)
            self._toggle_custom_domain()
    
    def _toggle_custom_domain(self):
        """Toggle custom domain input field"""
        if self.custom_domain_var.get():
            # Enable custom domain entry
            self.custom_domain_entry.configure(state="normal")
            self.custom_domain_help.grid()
            
            # Disable org type radio buttons
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for radio in widget.winfo_children():
                        if isinstance(radio, ctk.CTkRadioButton):
                            radio.configure(state="disabled")
            
            # Focus on custom domain entry
            self.custom_domain_entry.focus()
        else:
            # Disable custom domain entry
            self.custom_domain_entry.configure(state="disabled")
            self.custom_domain_help.grid_remove()
            
            # Re-enable org type radio buttons
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for radio in widget.winfo_children():
                        if isinstance(radio, ctk.CTkRadioButton):
                            radio.configure(state="normal")
    
    def _handle_login(self):
        """Handle login button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        token = self.token_entry.get().strip()
        
        # Validation
        if not all([username, password, token]):
            messagebox.showerror(
                "Input Error", 
                "All fields (Username, Password, Security Token) are required."
            )
            return
        
        # Determine domain
        if self.custom_domain_var.get():
            # Custom domain mode
            custom_domain = self.custom_domain_entry.get().strip()
            
            if not custom_domain:
                messagebox.showerror(
                    "Input Error",
                    "Please enter your custom domain or uncheck 'Use Custom Domain'."
                )
                return
            
            # Clean up the domain input
            custom_domain = custom_domain.replace("https://", "").replace("http://", "")
            custom_domain = custom_domain.rstrip("/")
            
            # Validate domain format
            if not custom_domain or " " in custom_domain:
                messagebox.showerror(
                    "Input Error",
                    "Invalid domain format. Example: mycompany.my.salesforce.com"
                )
                return
            
            domain = custom_domain
        else:
            # Standard mode
            domain = 'test' if self.org_type_var.get() == 'Sandbox' else 'login'
        
        # Show immediate feedback
        self.login_button.configure(
            state="disabled", 
            text="🔄 Connecting...",
            fg_color="#6c757d",  # Gray
            hover_color="#6c757d"
        )
        
        # Disable all inputs
        self.username_entry.configure(state="disabled")
        self.password_entry.configure(state="disabled")
        self.token_entry.configure(state="disabled")
        self.custom_domain_checkbox.configure(state="disabled")
        self.custom_domain_entry.configure(state="disabled")
        
        # Disable radio buttons
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for radio in widget.winfo_children():
                    if isinstance(radio, ctk.CTkRadioButton):
                        radio.configure(state="disabled")
        
        # Force UI update
        self.update_idletasks()
        
        # Call success callback with domain
        self.on_login_success(username, password, token, domain)

    def enable_login_button(self):
        """Re-enable login button after failed attempt"""
        self.login_button.configure(
            state="normal", 
            text="Connect to Salesforce",
            fg_color="#28a745",
            hover_color="#218838"
        )
        
        # Re-enable all inputs
        self.username_entry.configure(state="normal")
        self.password_entry.configure(state="normal")
        self.token_entry.configure(state="normal")
        self.custom_domain_checkbox.configure(state="normal")
        
        # Re-enable custom domain entry if checkbox is checked
        if self.custom_domain_var.get():
            self.custom_domain_entry.configure(state="normal")
        
        # Re-enable radio buttons if custom domain is not checked
        if not self.custom_domain_var.get():
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for radio in widget.winfo_children():
                        if isinstance(radio, ctk.CTkRadioButton):
                            radio.configure(state="normal")