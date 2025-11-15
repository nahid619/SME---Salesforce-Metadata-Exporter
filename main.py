"""
SME (Salesforce Metadata Exporter)
Main Application Entry Point - SIMPLIFIED (No Logger/Settings Issues)

Author: Nahid Hasan
"""
import sys
import customtkinter as ctk
from tkinter import messagebox
from config.constants import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, APP_NAME
from core.salesforce_client import SalesforceClient
from ui.login_screen import LoginScreen
from ui.main_screen import MainScreen


class SMEApplication(ctk.CTk):
    """Main application class for SME"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # Center window on screen
        self._center_window()
        
        # Enable resizing
        self.resizable(True, True)
        
        # Fullscreen bindings
        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)
        self.fullscreen_state = False
        
        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Salesforce client
        self.sf_client = None
        
        # Create screens
        self.login_screen = LoginScreen(self, on_login_success=self._handle_login_success)
        self.main_screen = None
        
        # Show login screen initially
        self.login_screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.after(100, self._center_window)
    
    def _center_window(self):
        """Center the application window on screen"""
        # Update window to get actual dimensions
        self.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2
        
        # Set position
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        
        # Force update to apply changes
        self.update()
        
    def _toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.fullscreen_state = not self.fullscreen_state
        self.attributes("-fullscreen", self.fullscreen_state)
    
    def _exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        if self.fullscreen_state:
            self.fullscreen_state = False
            self.attributes("-fullscreen", False)
    
    def _handle_login_success(self, username: str, password: str, token: str, domain: str):
        """
        Handle successful login
        
        Args:
            username: Salesforce username
            password: Salesforce password
            token: Security token
            domain: Org type (login/test)
        """
        try:
            print(f"Connecting to Salesforce as {username}...")
            
            # Create Salesforce client
            self.sf_client = SalesforceClient(
                username=username,
                password=password,
                security_token=token,
                domain=domain,
                status_callback=None
            )
            
            messagebox.showinfo("Success", "Successfully connected to Salesforce!")
            
            # Hide login screen
            self.login_screen.grid_forget()
            
            # Create and show main screen
            self.main_screen = MainScreen(
                self,
                sf_client=self.sf_client,
                on_logout=self._handle_logout
            )
            self.main_screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Connection Error: {error_msg}")
            messagebox.showerror("Login Failed", f"Connection Error: {error_msg}")
            self.sf_client = None
            self.login_screen.enable_login_button()
    
    def _handle_logout(self):
        """Handle logout action"""
        # Clear client
        self.sf_client = None
        
        # Destroy main screen
        if self.main_screen:
            self.main_screen.grid_forget()
            self.main_screen.destroy()
            self.main_screen = None
        
        # Recreate and show login screen
        self.login_screen = LoginScreen(self, on_login_success=self._handle_login_success)
        self.login_screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)


def main():
    """Main entry point"""
    try:
        print("=" * 70)
        print(f"Starting {APP_NAME} Application")
        print(f"Python version: {sys.version}")
        print("=" * 70)
        
        # Set appearance to DARK MODE (default)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        print("✅ UI theme set to Dark mode")
        
        # Create and run application
        app = SMEApplication()
        print("✅ Application window created successfully")
        print("=" * 70)
        
        app.mainloop()
        
    except Exception as e:
        print(f"\n❌ Application Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\nSME Application terminated")


if __name__ == "__main__":
    main()