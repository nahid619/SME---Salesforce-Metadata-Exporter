"""
SME - Main Export Screen UI (FIXED)

BUG FIXES:
1. Listboxes now start in dark mode correctly
2. All export buttons disabled during any export operation
3. Proper button state management
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, END
from ui.soql_query_screen import SOQLQueryScreen
from typing import List, Set, Callable, Dict
from datetime import datetime
import time
import threading
from config.constants import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, BUTTON_EXPORT, 
    BUTTON_EXPORT_HOVER, BUTTON_CANCEL, BUTTON_PLACEHOLDER,
    TERMINAL_FONT, APP_NAME, APP_FULL_NAME
)
from utils.helpers import format_runtime, get_timestamp, format_file_timestamp, print_statistics
from exporters.picklist_exporter import PicklistExporter
from exporters.dependency_analyzer import DependencyAnalyzer
from exporters.metadata_exporter import MetadataExporter


class MainScreen(ctk.CTkFrame):
    """Main application screen with export functionality"""
    
    def __init__(self, parent, sf_client, on_logout: Callable):
        """
        Initialize main screen
        
        Args:
            parent: Parent widget
            sf_client: Salesforce client instance
            on_logout: Callback function for logout
        """
        super().__init__(parent)
        self.sf_client = sf_client
        self.on_logout = on_logout
        
        # Initialize state variables
        self.all_org_objects: List[str] = []
        self.selected_objects: Set[str] = set()
        self.current_filter = "all"
        self.export_in_progress = False
        self.picklist_exporter = None
        self.dependency_analyzer = None
        self.metadata_exporter = None

        self.soql_screen = None  # NEW: SOQL screen instance
        
        # Track current theme for listbox colors
        self.current_theme = "Dark"  # Start with Dark
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Setup UI
        self._setup_ui()
        
        # Load objects
        self._load_objects()
    
    def _setup_ui(self):
        """Setup main UI components"""
        # Header
        self._create_header()
        
        # Object Selection Panel
        self._create_selection_panel()
        
        # Export Format Selector
        self._create_format_selector()
        
        # Feature Buttons
        self._create_feature_buttons()
        
        # Status Bar
        self._create_status_bar()
        
        # Progress Bar
        self._create_progress_bar()
        
        # Terminal/Log Area
        self._create_terminal()
    
    def _create_header(self):
        """Create header with title, theme toggle, and logout"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=(5, 5), sticky="ew", padx=15)
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame, 
            text=f"{APP_NAME} - {APP_FULL_NAME}",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Theme Toggle (starts with moon for dark mode)
        self.theme_toggle = ctk.CTkButton(
            header_frame, 
            text="🌙", 
            command=self._toggle_theme,
            width=40, 
            height=40, 
            font=ctk.CTkFont(size=18)
        )
        self.theme_toggle.grid(row=0, column=1, sticky="e", padx=(0, 10))
        
        # Logout Button
        self.logout_button = ctk.CTkButton(
            header_frame, 
            text="Logout",
            command=self._handle_logout,
            width=100, 
            height=40,
            fg_color=COLOR_DANGER,
            hover_color="#b32929",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.logout_button.grid(row=0, column=2, sticky="e")
    
    def _create_selection_panel(self):
        """Create object selection panel with proper proportions (45% - 20% - 35%)"""
        selection_frame = ctk.CTkFrame(self, height=380)
        selection_frame.grid(row=1, column=0, pady=5, sticky="nsew", padx=15)
        selection_frame.grid_propagate(False)
        selection_frame.grid_columnconfigure(0, weight=45)
        selection_frame.grid_columnconfigure(1, weight=20)
        selection_frame.grid_columnconfigure(2, weight=35)
        selection_frame.grid_rowconfigure(0, weight=1)
        
        # LEFT: Available Objects (45%)
        self._create_available_panel(selection_frame)
        
        # MIDDLE: Action Buttons (20%)
        self._create_action_buttons(selection_frame)
        
        # RIGHT: Selected Objects (35%)
        self._create_selected_panel(selection_frame)
    
    def _create_available_panel(self, parent):
        """Create available objects panel"""
        available_frame = ctk.CTkFrame(parent)
        available_frame.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")
        available_frame.grid_rowconfigure(4, weight=1)
        available_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            available_frame, 
            text="Available Objects",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, pady=(8, 2))
        
        # Count
        self.available_count_label = ctk.CTkLabel(
            available_frame,
            text="(0 objects)",
            font=ctk.CTkFont(size=10)
        )
        self.available_count_label.grid(row=1, column=0, pady=(0, 5))
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(available_frame, fg_color="transparent")
        filter_frame.grid(row=2, column=0, pady=3, sticky="ew", padx=5)
        filter_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.filter_all_btn = ctk.CTkButton(
            filter_frame, 
            text="All",
            command=lambda: self._apply_filter("all"),
            height=28,
            font=ctk.CTkFont(size=12)
        )
        self.filter_all_btn.grid(row=0, column=0, padx=2, sticky="ew")
        
        self.filter_standard_btn = ctk.CTkButton(
            filter_frame,
            text="Standard",
            command=lambda: self._apply_filter("standard"),
            height=28,
            fg_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.filter_standard_btn.grid(row=0, column=1, padx=2, sticky="ew")
        
        self.filter_custom_btn = ctk.CTkButton(
            filter_frame,
            text="Custom",
            command=lambda: self._apply_filter("custom"),
            height=28,
            fg_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.filter_custom_btn.grid(row=0, column=2, padx=2, sticky="ew")
        
        # Search
        self.search_entry = ctk.CTkEntry(
            available_frame,
            placeholder_text="Search objects...",
            height=30,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.grid(row=3, column=0, padx=5, pady=3, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._filter_available_objects)
        
        # Listbox - BUG FIX: Start with DARK MODE colors
        self.available_listbox = tk.Listbox(
            available_frame,
            selectmode="extended",
            exportselection=False,
            font=("Segoe UI", 11),
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#1F538D",
            fg="#FFFFFF",  # White text for dark mode
            background="#2B2B2B"  # Dark background
        )
        self.available_listbox.grid(row=4, column=0, padx=5, pady=(0, 5), sticky="nsew")
    
    def _create_action_buttons(self, parent):
        """Create action buttons in the middle (20%)"""
        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.grid(row=0, column=1, padx=5, pady=0, sticky="nsew")
        
        action_frame.grid_rowconfigure(0, weight=1)
        action_frame.grid_rowconfigure(7, weight=1)
        action_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            action_frame,
            text="Actions",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=1, column=0, pady=(0, 10))
        
        ctk.CTkButton(
            action_frame,
            text="Add >>",
            command=self._add_selected_to_export,
            height=32,
            font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, pady=4, sticky="ew", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="<< Remove",
            command=self._remove_selected_from_export,
            height=32,
            font=ctk.CTkFont(size=12)
        ).grid(row=3, column=0, pady=4, sticky="ew", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="Select All",
            command=self._select_all_available,
            height=32,
            font=ctk.CTkFont(size=12)
        ).grid(row=4, column=0, pady=(15, 4), sticky="ew", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="Deselect All",
            command=self._deselect_all_available,
            height=32,
            font=ctk.CTkFont(size=12)
        ).grid(row=5, column=0, pady=4, sticky="ew", padx=5)
    
    def _create_selected_panel(self, parent):
        """Create selected objects panel (35%)"""
        selected_frame = ctk.CTkFrame(parent)
        selected_frame.grid(row=0, column=2, padx=(5, 0), pady=0, sticky="nsew")
        selected_frame.grid_rowconfigure(2, weight=1)
        selected_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            selected_frame,
            text="Selected for Export",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, pady=(8, 2))
        
        # Count
        self.selected_count_label = ctk.CTkLabel(
            selected_frame,
            text="(0 selected)",
            font=ctk.CTkFont(size=10)
        )
        self.selected_count_label.grid(row=1, column=0, pady=(0, 5))
        
        # Listbox - BUG FIX: Start with DARK MODE colors
        self.selected_listbox = tk.Listbox(
            selected_frame,
            selectmode="extended",
            exportselection=False,
            font=("Segoe UI", 11),
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#3366CC",
            fg="#FFFFFF",  # White text for dark mode
            background="#2B2B2B"  # Dark background
        )
        self.selected_listbox.grid(row=2, column=0, padx=5, pady=(0, 5), sticky="nsew")
    
    def _create_format_selector(self):
        """Create export format selector"""
        format_frame = ctk.CTkFrame(self)
        format_frame.grid(row=2, column=0, pady=5, sticky="ew", padx=15)
        
        ctk.CTkLabel(
            format_frame,
            text="Export Format:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(12, 12))
        
        self.export_format_var = ctk.StringVar(value="excel")
        
        ctk.CTkRadioButton(
            format_frame,
            text="Excel (.xlsx)",
            variable=self.export_format_var,
            value="excel",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=8)
        
        ctk.CTkRadioButton(
            format_frame,
            text="CSV (.csv)",
            variable=self.export_format_var,
            value="csv",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=8)
    
    def _create_feature_buttons(self):
        """Create feature buttons row"""
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.grid(row=3, column=0, pady=5, sticky="ew", padx=15)
        buttons_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.picklist_export_btn = ctk.CTkButton(
            buttons_frame,
            text="📋 Export Picklist Data",
            command=self._export_picklist_action,
            height=42,
            fg_color=BUTTON_EXPORT,
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.picklist_export_btn.grid(row=0, column=0, padx=4, sticky="ew")
        
        self.dependency_btn = ctk.CTkButton(
            buttons_frame,
            text="🔗 Dependency Analysis",
            command=self._export_dependency_action,
            height=42,
            fg_color=BUTTON_EXPORT,
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.dependency_btn.grid(row=0, column=1, padx=4, sticky="ew")
        
        self.metadata_btn = ctk.CTkButton(
            buttons_frame,
            text="📦 Metadata Exporter",
            command=self._export_metadata_action,
            height=42,
            fg_color=BUTTON_EXPORT,
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.metadata_btn.grid(row=0, column=2, padx=4, sticky="ew")
        
        # NEW: SOQL Query Runner button (replaces Formula Fields)
        self.soql_btn = ctk.CTkButton(
            buttons_frame,
            text="⚡ SOQL Query Runner",
            command=self._open_soql_query_screen,
            height=42,
            fg_color=BUTTON_EXPORT,
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.soql_btn.grid(row=0, column=3, padx=4, sticky="ew")
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = ctk.CTkLabel(
            self,
            text="Status: Ready",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_SUCCESS,
            height=24,
            anchor="w",
            padx=12
        )
        self.status_bar.grid(row=4, column=0, sticky="ew", padx=15, pady=(5, 0))
    
    def _create_progress_bar(self):
        """Create progress bar with percentage"""
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.grid(row=5, column=0, sticky="ew", padx=15, pady=(3, 0))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=12)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(size=11)
        )
        self.progress_label.grid(row=0, column=1)
    
    def _create_terminal(self):
        """Create terminal/log area"""
        self.status_textbox = ctk.CTkTextbox(
            self,
            height=140,
            font=("Consolas", 11),
            wrap="word"
        )
        self.status_textbox.grid(row=6, column=0, padx=15, pady=(5, 10), sticky="nsew")
        
        # Welcome message
        self.status_textbox.insert("end", "╔" + "═" * 73 + "╗\n")
        self.status_textbox.insert("end", f"  {APP_NAME} - {APP_FULL_NAME} - Ready\n")
        self.status_textbox.insert("end", "╚" + "═" * 73 + "╝\n")
        self.status_textbox.insert("end", "\n✓ Connected successfully. Select objects and click Export.\n")
        self.status_textbox.insert("end", "\n💡 Tips:\n")
        self.status_textbox.insert("end", "   - Press F11 for fullscreen mode\n")
        self.status_textbox.insert("end", "   - Window is resizable for better visualization\n")
        self.status_textbox.configure(state="disabled")
    
    # ==================== Event Handlers ====================
    
    def _toggle_theme(self):
        """Toggle between dark and light mode"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_toggle.configure(text="☀️")
            self.current_theme = "Light"
            # Update listbox colors for light mode
            self.available_listbox.configure(fg="#000000", background="#FFFFFF")
            self.selected_listbox.configure(fg="#000000", background="#FFFFFF")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_toggle.configure(text="🌙")
            self.current_theme = "Dark"
            # Update listbox colors for dark mode
            self.available_listbox.configure(fg="#FFFFFF", background="#2B2B2B")
            self.selected_listbox.configure(fg="#FFFFFF", background="#2B2B2B")
    
    def _handle_logout(self):
        """Handle logout action"""
        if self.export_in_progress:
            messagebox.showwarning(
                "Export in Progress",
                "Cannot logout while export is running. Please cancel or wait for completion."
            )
            return
        
        confirm = messagebox.askyesno("Logout", "Are you sure you want to log out?")
        if confirm:
            self.on_logout()
    
    def _coming_soon(self):
        """Placeholder for future features"""
        messagebox.showinfo(
            "Coming Soon",
            "This feature is under development and will be available in a future release."
        )
    
    def _load_objects(self):
        """Load all org objects"""
        try:
            self.all_org_objects = self.sf_client.fetch_all_objects()
            self._populate_available_objects()
            self._update_object_counts()
        except Exception as e:
            messagebox.showerror("Error Loading Objects", f"Failed to load objects:\n{str(e)}")
            self._update_status(f"❌ Error loading objects: {str(e)}")
    
    def _apply_filter(self, filter_type: str):
        """Apply object filter"""
        self.current_filter = filter_type
        
        # Update button colors
        if filter_type == "all":
            self.filter_all_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.filter_standard_btn.configure(fg_color="gray")
            self.filter_custom_btn.configure(fg_color="gray")
        elif filter_type == "standard":
            self.filter_all_btn.configure(fg_color="gray")
            self.filter_standard_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            self.filter_custom_btn.configure(fg_color="gray")
        else:
            self.filter_all_btn.configure(fg_color="gray")
            self.filter_standard_btn.configure(fg_color="gray")
            self.filter_custom_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        
        self._populate_available_objects()
        self._update_object_counts()
    
    def _get_filtered_objects(self) -> List[str]:
        """Get objects based on current filter and search"""
        search_term = self.search_entry.get().lower()
        
        if self.current_filter == "standard":
            filtered = [obj for obj in self.all_org_objects if not obj.endswith('__c')]
        elif self.current_filter == "custom":
            filtered = [obj for obj in self.all_org_objects if obj.endswith('__c')]
        else:
            filtered = self.all_org_objects
        
        if search_term:
            filtered = [obj for obj in filtered if search_term in obj.lower()]
        
        return filtered
    
    def _populate_available_objects(self):
        """Populate available objects listbox"""
        self.available_listbox.delete(0, END)
        filtered_objects = self._get_filtered_objects()
        
        for obj in filtered_objects:
            self.available_listbox.insert(END, obj)
            if obj in self.selected_objects:
                idx = self.available_listbox.size() - 1
                self.available_listbox.itemconfig(idx, {'fg': '#87CEEB'})
    
    def _populate_selected_objects(self):
        """Populate selected objects listbox"""
        self.selected_listbox.delete(0, END)
        for obj in sorted(list(self.selected_objects)):
            self.selected_listbox.insert(END, obj)
    
    def _filter_available_objects(self, event):
        """Filter when user types in search box"""
        self._populate_available_objects()
        self._update_object_counts()
    
    def _update_object_counts(self):
        """Update count labels"""
        available_count = self.available_listbox.size()
        selected_count = len(self.selected_objects)
        
        self.available_count_label.configure(text=f"({available_count} objects)")
        self.selected_count_label.configure(text=f"({selected_count} selected)")
    
    def _add_selected_to_export(self):
        """Add selected objects to export list"""
        selected_indices = self.available_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning(
                "Selection",
                "Please select one or more objects from the 'Available Objects' list."
            )
            return
        
        added_count = 0
        for i in selected_indices:
            obj_name = self.available_listbox.get(i)
            if obj_name not in self.selected_objects:
                self.selected_objects.add(obj_name)
                added_count += 1
        
        if added_count > 0:
            self._populate_selected_objects()
            self._populate_available_objects()
            self._update_status(f"✓ Added {added_count} object(s) to export list.")
            self._update_object_counts()
    
    def _remove_selected_from_export(self):
        """Remove selected objects from export list"""
        selected_indices = self.selected_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning(
                "Selection",
                "Please select one or more objects from the 'Selected for Export' list."
            )
            return
        
        removed_objects = []
        for i in reversed(selected_indices):
            obj_name = self.selected_listbox.get(i)
            removed_objects.append(obj_name)
        
        for obj_name in removed_objects:
            self.selected_objects.discard(obj_name)
        
        if removed_objects:
            self._populate_selected_objects()
            self._populate_available_objects()
            self._update_status(f"✓ Removed {len(removed_objects)} object(s) from export list.")
            self._update_object_counts()
    
    def _select_all_available(self):
        """Add all visible objects to selected"""
        filtered_objects = self._get_filtered_objects()
        
        if not filtered_objects:
            messagebox.showinfo(
                "No Objects",
                "No objects available to select with current filter."
            )
            return
        
        added_count = 0
        for obj in filtered_objects:
            if obj not in self.selected_objects:
                self.selected_objects.add(obj)
                added_count += 1
        
        if added_count > 0:
            self._populate_selected_objects()
            self._populate_available_objects()
            self._update_status(f"✓ Added ALL {added_count} filtered object(s) to export list.")
            self._update_object_counts()
        else:
            messagebox.showinfo(
                "Already Selected",
                "All visible objects are already in the export list."
            )
    
    def _deselect_all_available(self):
        """Remove all objects from selected"""
        if not self.selected_objects:
            messagebox.showinfo("No Selection", "No objects selected for export.")
            return
        
        count = len(self.selected_objects)
        confirm = messagebox.askyesno(
            "Deselect All",
            f"Remove all {count} selected objects from export list?"
        )
        
        if confirm:
            self.selected_objects.clear()
            self._populate_selected_objects()
            self._populate_available_objects()
            self._update_status(f"✓ Removed ALL {count} object(s) from export list.")
            self._update_object_counts()
    
    def _update_status(self, message: str, verbose: bool = False):
        """Update terminal with status message"""
        timestamp = get_timestamp()
        display_message = f"{timestamp} {message}"
        
        self.status_textbox.configure(state="normal")
        self.status_textbox.insert("end", "\n" + display_message)
        self.status_textbox.see("end")
        
        if not verbose:
            print(display_message)
        
        self.status_textbox.configure(state="disabled")
        self.update_idletasks()
    
    def _update_status_bar(self, message: str, color: str = COLOR_SUCCESS):
        """Update status bar with message and color"""
        self.status_bar.configure(text=f"Status: {message}", fg_color=color)
        self.update_idletasks()
    
    def _update_progress(self, current: int, total: int):
        """Update progress bar"""
        if total > 0:
            progress = current / total
            percentage = int(progress * 100)
            
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"{percentage}% ({current}/{total})")
            self._update_status_bar(f"Processing {current}/{total} - {percentage}% complete", COLOR_WARNING)
        
        self.update_idletasks()
    
    def _disable_ui(self):
        """BUG FIX: Disable ALL export buttons and UI elements during export"""
        self.available_listbox.configure(state="disabled")
        self.selected_listbox.configure(state="disabled")
        self.search_entry.configure(state="disabled")


        # Disable ALL export buttons
        self.picklist_export_btn.configure(state="disabled")
        self.dependency_btn.configure(state="disabled")
        self.metadata_btn.configure(state="disabled")
        self.soql_btn.configure(state="disabled")
        
        self.logout_button.configure(state="disabled")
        self.theme_toggle.configure(state="disabled")
        self.filter_all_btn.configure(state="disabled")
        self.filter_standard_btn.configure(state="disabled")
        self.filter_custom_btn.configure(state="disabled")
    
    def _enable_ui(self):
        """BUG FIX: Re-enable ALL export buttons and UI elements after export"""
        self.available_listbox.configure(state="normal")
        self.selected_listbox.configure(state="normal")
        self.search_entry.configure(state="normal")
        self.soql_btn.configure(state="normal")

        # Re-enable ALL export buttons
        self.picklist_export_btn.configure(state="normal")
        self.dependency_btn.configure(state="normal")
        self.metadata_btn.configure(state="normal")
        self.soql_btn.configure(state="normal")
        
        self.logout_button.configure(state="normal")
        self.theme_toggle.configure(state="normal")
        self.filter_all_btn.configure(state="normal")
        self.filter_standard_btn.configure(state="normal")
        self.filter_custom_btn.configure(state="normal")
    
    
    # ==================== SOQL QUERY SCREEN NAVIGATION ====================

    def _open_soql_query_screen(self):
        """Open SOQL Query Runner screen"""
        # Hide main screen
        self.grid_forget()
        
        # Create and show SOQL screen
        if self.soql_screen is None:
            self.soql_screen = SOQLQueryScreen(
                self.master,
                sf_client=self.sf_client,
                on_back=self._close_soql_query_screen
            )
        
        self.soql_screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def _close_soql_query_screen(self):
        """Close SOQL Query Runner screen and return to main"""
        if self.soql_screen:
            self.soql_screen.grid_forget()
        
        # Show main screen again
        self.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    
    # ==================== PICKLIST EXPORT HANDLERS ====================
    
    def _export_picklist_action(self):
        """Handle picklist export action"""
        if not self.sf_client:
            messagebox.showerror("Error", "Not logged in. Please log in first.")
            return
        
        selected_objects_list = sorted(list(self.selected_objects))
        
        if not selected_objects_list:
            messagebox.showwarning(
                "Warning",
                "Please add objects to the 'Selected for Export' list."
            )
            return
        
        export_format = self.export_format_var.get()
        extension = ".xlsx" if export_format == "excel" else ".csv"
        default_filename = f'Picklist_Export_{format_file_timestamp()}{extension}'
        
        filetypes = [("Excel files", "*.xlsx")] if export_format == "excel" else [("CSV files", "*.csv")]
        
        output_file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            initialfile=default_filename,
            filetypes=filetypes
        )
        
        if not output_file_path:
            return
        
        self.export_in_progress = True
        self._disable_ui()
        self.picklist_export_btn.configure(
            text="⏸️ Cancel Export",
            command=self._cancel_export_action,
            fg_color=BUTTON_CANCEL,
            state="normal"
        )
        self._update_status_bar("Export in progress...", COLOR_WARNING)
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        
        # Create exporter
        self.picklist_exporter = PicklistExporter(self.sf_client, status_callback=self._update_status)
        
        # Start export in thread
        export_thread = threading.Thread(
            target=self._run_export,
            args=(selected_objects_list, output_file_path, export_format),
            daemon=True
        )
        export_thread.start()
    
    def _cancel_export_action(self):
        """Cancel ongoing export"""
        confirm = messagebox.askyesno(
            "Cancel Export",
            "Are you sure you want to cancel the export?\n\nPartial data will be saved."
        )
        if confirm and self.picklist_exporter:
            self.picklist_exporter.cancel_export()
            self.picklist_export_btn.configure(text="Cancelling...", state="disabled")
            self._update_status_bar("Cancelling export...", COLOR_WARNING)
    
    def _run_export(self, selected_objects_list: List[str], output_file_path: str, export_format: str):
        """Background thread for export operation"""
        start_time = time.time()
        output_path = None
        stats = None
        
        try:
            output_path, stats = self.picklist_exporter.export_picklists(
                selected_objects_list,
                output_file_path,
                export_format=export_format,
                progress_callback=self._update_progress
            )
            
            end_time = time.time()
            runtime_seconds = end_time - start_time
            runtime_formatted = format_runtime(runtime_seconds)
            
            if stats.get('cancelled'):
                self.after(0, self._export_complete_cancelled, output_path, stats, runtime_formatted)
            else:
                self.after(0, self._export_complete_success, output_path, stats, runtime_formatted)
        
        except Exception as e:
            self.after(0, self._export_complete_error, str(e))
    
    def _export_complete_success(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when export completes successfully"""
        self._update_status(f"\n{'='*63}")
        self._update_status(f"✅ EXPORT COMPLETED SUCCESSFULLY!")
        self._update_status(f"{'='*63}")
        self._update_status(f"Runtime: {runtime_formatted}")
        self._update_status(f"API Calls: {stats.get('api_calls_made', 0)}")
        self._update_status(f"Objects: {stats['total_objects']} | Success: {stats['successful_objects']} | Failed: {stats['failed_objects']}")
        self._update_status(f"Picklist Fields: {stats['total_picklist_fields']}")
        self._update_status(f"Values: {stats['total_values']} (Active: {stats['total_active_values']}, Inactive: {stats['total_inactive_values']})")
        self._update_status(f"Output: {output_path}")
        self._update_status(f"{'='*63}\n")
        
        self._update_status_bar("Export completed successfully!", COLOR_SUCCESS)
        self.progress_bar.set(1.0)
        
        messagebox.showinfo(
            "Export Complete",
            f"Picklist data successfully exported!\n\nFile: {output_path}\nRuntime: {runtime_formatted}\nAPI Calls: {stats.get('api_calls_made', 0)}"
        )
        
        print_statistics(stats, runtime_formatted, output_path)
        
        self.export_in_progress = False
        self.picklist_exporter = None
        self._enable_ui()
        self.picklist_export_btn.configure(
            text="📋 Export Picklist Data",
            command=self._export_picklist_action,
            fg_color=BUTTON_EXPORT
        )
    
    def _export_complete_cancelled(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when export is cancelled"""
        self._update_status(f"\n{'='*63}")
        self._update_status(f"🛑 EXPORT CANCELLED BY USER")
        self._update_status(f"{'='*63}")
        self._update_status(f"Runtime: {runtime_formatted}")
        self._update_status(f"API Calls: {stats.get('api_calls_made', 0)}")
        self._update_status(f"Processed: {stats['successful_objects']}/{stats['total_objects']} objects")
        self._update_status(f"Partial data saved to: {output_path}")
        self._update_status(f"{'='*63}\n")
        
        self._update_status_bar("Export cancelled", COLOR_WARNING)
        
        messagebox.showwarning(
            "Export Cancelled",
            f"Export was cancelled.\n\nPartial data saved to:\n{output_path}\n\nProcessed: {stats['successful_objects']}/{stats['total_objects']} objects"
        )
        
        print_statistics(stats, runtime_formatted, output_path)
        
        self.export_in_progress = False
        self.picklist_exporter = None
        self._enable_ui()
        self.picklist_export_btn.configure(
            text="📋 Export Picklist Data",
            command=self._export_picklist_action,
            fg_color=BUTTON_EXPORT
        )
    
    def _export_complete_error(self, error_message: str):
        """Called when export fails"""
        self._update_status(f"\n❌ EXPORT ERROR: {error_message}\n")
        self._update_status_bar("Export failed!", COLOR_DANGER)
        
        messagebox.showerror("Export Error", f"Export failed:\n\n{error_message}")
        
        self.export_in_progress = False
        self.picklist_exporter = None
        self._enable_ui()
        self.picklist_export_btn.configure(
            text="📋 Export Picklist Data",
            command=self._export_picklist_action,
            fg_color=BUTTON_EXPORT
        )
    
    # ==================== DEPENDENCY ANALYSIS HANDLERS ====================
    
    def _export_dependency_action(self):
        """Handle dependency analysis export action"""
        if not self.sf_client:
            messagebox.showerror("Error", "Not logged in. Please log in first.")
            return
        
        selected_objects_list = sorted(list(self.selected_objects))
        
        if not selected_objects_list:
            messagebox.showwarning(
                "Warning",
                "Please add objects to the 'Selected for Export' list."
            )
            return
        
        if len(selected_objects_list) < 2:
            messagebox.showinfo(
                "Info",
                "Dependency analysis requires at least 2 objects.\n\nPlease select more objects."
            )
            return
        
        export_format = self.export_format_var.get()
        extension = ".xlsx" if export_format == "excel" else ".csv"
        default_filename = f'Dependency_Analysis_{format_file_timestamp()}{extension}'
        
        filetypes = [("Excel files", "*.xlsx")] if export_format == "excel" else [("CSV files", "*.csv")]
        
        output_file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            initialfile=default_filename,
            filetypes=filetypes
        )
        
        if not output_file_path:
            return
        
        self.export_in_progress = True
        self._disable_ui()
        self.dependency_btn.configure(
            text="⏸️ Cancel Analysis",
            command=self._cancel_dependency_action,
            fg_color=BUTTON_CANCEL,
            state="normal"
        )
        self._update_status_bar("Dependency analysis in progress...", COLOR_WARNING)
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        
        # Create analyzer
        self.dependency_analyzer = DependencyAnalyzer(self.sf_client, status_callback=self._update_status)
        
        # Start analysis in thread
        analysis_thread = threading.Thread(
            target=self._run_dependency_analysis,
            args=(selected_objects_list, output_file_path, export_format),
            daemon=True
        )
        analysis_thread.start()
    
    def _cancel_dependency_action(self):
        """Cancel ongoing dependency analysis"""
        confirm = messagebox.askyesno(
            "Cancel Analysis",
            "Are you sure you want to cancel the dependency analysis?\n\nPartial data will be saved."
        )
        if confirm and self.dependency_analyzer:
            self.dependency_analyzer.cancel_analysis()
            self.dependency_btn.configure(text="Cancelling...", state="disabled")
            self._update_status_bar("Cancelling analysis...", COLOR_WARNING)
    
    def _run_dependency_analysis(self, selected_objects_list: List[str], output_file_path: str, export_format: str):
        """Background thread for dependency analysis operation"""
        start_time = time.time()
        output_path = None
        stats = None
        
        try:
            output_path, stats = self.dependency_analyzer.analyze_dependencies(
                selected_objects_list,
                output_file_path,
                export_format=export_format,
                progress_callback=self._update_progress
            )
            
            end_time = time.time()
            runtime_seconds = end_time - start_time
            runtime_formatted = format_runtime(runtime_seconds)
            
            if stats.get('cancelled'):
                self.after(0, self._dependency_complete_cancelled, output_path, stats, runtime_formatted)
            else:
                self.after(0, self._dependency_complete_success, output_path, stats, runtime_formatted)
        
        except Exception as e:
            self.after(0, self._dependency_complete_error, str(e))
    
    def _dependency_complete_success(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when dependency analysis completes successfully"""
        self._update_status(f"\n{'='*63}")
        self._update_status(f"✅ DEPENDENCY ANALYSIS COMPLETED!")
        self._update_status(f"{'='*63}")
        self._update_status(f"Runtime: {runtime_formatted}")
        self._update_status(f"API Calls: {stats.get('api_calls_made', 0)}")
        self._update_status(f"Objects Analyzed: {stats['analyzed_objects']}/{stats['total_objects']}")
        self._update_status(f"Total Dependencies Found: {stats['total_dependencies']}")
        self._update_status(f"  - Lookup: {stats['lookup_dependencies']}")
        self._update_status(f"  - Master-Detail: {stats['master_detail_dependencies']}")
        self._update_status(f"  - Self-References: {stats['self_references']}")
        self._update_status(f"Max Dependency Level: {stats['max_dependency_level']}")
        self._update_status(f"Output: {output_path}")
        self._update_status(f"{'='*63}\n")
        
        self._update_status_bar("Dependency analysis completed!", COLOR_SUCCESS)
        self.progress_bar.set(1.0)
        
        messagebox.showinfo(
            "Analysis Complete",
            f"Dependency analysis completed!\n\n"
            f"File: {output_path}\n"
            f"Runtime: {runtime_formatted}\n"
            f"Dependencies Found: {stats['total_dependencies']}\n"
            f"Max Level: {stats['max_dependency_level']}"
        )
        
        self.export_in_progress = False
        self.dependency_analyzer = None
        self._enable_ui()
        self.dependency_btn.configure(
            text="🔗 Dependency Analysis",
            command=self._export_dependency_action,
            fg_color=BUTTON_EXPORT
        )
    
    def _dependency_complete_cancelled(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when dependency analysis is cancelled"""
        self._update_status(f"\n{'='*63}")
        self._update_status(f"🛑 DEPENDENCY ANALYSIS CANCELLED")
        self._update_status(f"{'='*63}")
        self._update_status(f"Runtime: {runtime_formatted}")
        self._update_status(f"Analyzed: {stats['analyzed_objects']}/{stats['total_objects']} objects")
        self._update_status(f"Partial data saved to: {output_path}")
        self._update_status(f"{'='*63}\n")
        
        self._update_status_bar("Analysis cancelled", COLOR_WARNING)
        
        messagebox.showwarning(
            "Analysis Cancelled",
            f"Analysis was cancelled.\n\n"
            f"Partial data saved to:\n{output_path}\n\n"
            f"Analyzed: {stats['analyzed_objects']}/{stats['total_objects']} objects"
        )
        
        self.export_in_progress = False
        self.dependency_analyzer = None
        self._enable_ui()
        self.dependency_btn.configure(
            text="🔗 Dependency Analysis",
            command=self._export_dependency_action,
            fg_color=BUTTON_EXPORT
        )
    
    def _dependency_complete_error(self, error_message: str):
        """Called when dependency analysis fails"""
        self._update_status(f"\n❌ ANALYSIS ERROR: {error_message}\n")
        self._update_status_bar("Analysis failed!", COLOR_DANGER)
        
        messagebox.showerror("Analysis Error", f"Analysis failed:\n\n{error_message}")
        
        self.export_in_progress = False
        self.dependency_analyzer = None
        self._enable_ui()
        self.dependency_btn.configure(
            text="🔗 Dependency Analysis",
            command=self._export_dependency_action,
            fg_color=BUTTON_EXPORT
        )
    
    # ==================== METADATA EXPORT HANDLERS ====================
    
    def _export_metadata_action(self):
        """Handle metadata export action"""
        if not self.sf_client:
            messagebox.showerror("Error", "Not logged in. Please log in first.")
            return
        
        selected_objects_list = sorted(list(self.selected_objects))
        
        if not selected_objects_list:
            messagebox.showwarning(
                "Warning",
                "Please add objects to the 'Selected for Export' list."
            )
            return
        
        # Ask for options
        options_dialog = ctk.CTkToplevel(self)
        options_dialog.title("Metadata Export Options")
        options_dialog.geometry("400x200")
        options_dialog.transient(self)
        options_dialog.grab_set()
        
        # Center dialog
        options_dialog.update_idletasks()
        x = (options_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (options_dialog.winfo_screenheight() // 2) - (200 // 2)
        options_dialog.geometry(f"+{x}+{y}")
        
        # Options frame
        opts_frame = ctk.CTkFrame(options_dialog)
        opts_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            opts_frame,
            text="Select Export Options:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(0, 15))
        
        # Custom fields only checkbox
        custom_only_var = ctk.BooleanVar(value=False)
        custom_only_cb = ctk.CTkCheckBox(
            opts_frame,
            text="Export custom fields only",
            variable=custom_only_var,
            font=ctk.CTkFont(size=12)
        )
        custom_only_cb.pack(pady=5, anchor="w")
        
        # Include usage checkbox
        include_usage_var = ctk.BooleanVar(value=False)
        include_usage_cb = ctk.CTkCheckBox(
            opts_frame,
            text="Include field usage analysis (slower)",
            variable=include_usage_var,
            font=ctk.CTkFont(size=12)
        )
        include_usage_cb.pack(pady=5, anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(opts_frame, fg_color="transparent")
        btn_frame.pack(pady=(15, 0))
        
        def on_continue():
            options_dialog.destroy()
            self._start_metadata_export(
                selected_objects_list,
                custom_only_var.get(),
                include_usage_var.get()
            )
        
        def on_cancel():
            options_dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Continue",
            command=on_continue,
            fg_color=BUTTON_EXPORT,
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=on_cancel,
            fg_color="gray",
            width=120
        ).pack(side="left", padx=5)
    
    def _start_metadata_export(self, selected_objects_list: List[str], 
                               custom_only: bool, include_usage: bool):
        """Start the metadata export process"""
        export_format = self.export_format_var.get()
        extension = ".xlsx" if export_format == "excel" else ".csv"
        default_filename = f'Metadata_Export_{format_file_timestamp()}{extension}'
        
        filetypes = [("Excel files", "*.xlsx")] if export_format == "excel" else [("CSV files", "*.csv")]
        
        output_file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            initialfile=default_filename,
            filetypes=filetypes
        )
        
        if not output_file_path:
            return
        
        self.export_in_progress = True
        self._disable_ui()
        self.metadata_btn.configure(
            text="⏸️ Cancel Export",
            command=self._cancel_metadata_action,
            fg_color=BUTTON_CANCEL,
            state="normal"
        )
        self._update_status_bar("Metadata export in progress...", COLOR_WARNING)
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        
        # Create exporter
        self.metadata_exporter = MetadataExporter(self.sf_client, status_callback=self._update_status)
        
        # Start export in thread
        export_thread = threading.Thread(
            target=self._run_metadata_export,
            args=(selected_objects_list, output_file_path, export_format, custom_only, include_usage),
            daemon=True
        )
        export_thread.start()
    
    def _cancel_metadata_action(self):
        """Cancel ongoing metadata export"""
        confirm = messagebox.askyesno(
            "Cancel Export",
            "Are you sure you want to cancel the metadata export?\n\nPartial data will be saved."
        )
        if confirm and self.metadata_exporter:
            self.metadata_exporter.cancel_export()
            self.metadata_btn.configure(text="Cancelling...", state="disabled")
            self._update_status_bar("Cancelling export...", COLOR_WARNING)
    
    def _run_metadata_export(self, selected_objects_list: List[str], output_file_path: str, 
                            export_format: str, custom_only: bool, include_usage: bool):
        """Background thread for metadata export operation"""
        start_time = time.time()
        output_path = None
        stats = None
        
        try:
            output_path, stats = self.metadata_exporter.export_metadata(
                selected_objects_list,
                output_file_path,
                export_format=export_format,
                include_usage=include_usage,
                custom_only=custom_only,
                progress_callback=self._update_progress
            )
            
            end_time = time.time()
            runtime_seconds = end_time - start_time
            runtime_formatted = format_runtime(runtime_seconds)
            
            if stats.get('cancelled'):
                self.after(0, self._metadata_complete_cancelled, output_path, stats, runtime_formatted)
            else:
                self.after(0, self._metadata_complete_success, output_path, stats, runtime_formatted)
        
        except Exception as e:
            self.after(0, self._metadata_complete_error, str(e))
    
    def _metadata_complete_success(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when metadata export completes successfully"""
        self._update_status(f"\n{'='*63}")
        self._update_status(f"✅ METADATA EXPORT COMPLETED!")
        self._update_status(f"{'='*63}")
        self._update_status(f"Runtime: {runtime_formatted}")
        self._update_status(f"API Calls: {stats.get('api_calls_made', 0)}")
        self._update_status(f"Objects Processed: {stats['successful_objects']}/{stats['total_objects']}")
        self._update_status(f"Total Fields: {stats['total_fields']}")
        self._update_status(f"  - Standard Fields: {stats['standard_fields']}")
        self._update_status(f"  - Custom Fields: {stats['custom_fields']}")
        self._update_status(f"  - Formula Fields: {stats['formula_fields']}")
        self._update_status(f"  - Lookup Fields: {stats['lookup_fields']}")
        self._update_status(f"  - Picklist Fields: {stats['picklist_fields']}")
        self._update_status(f"Output: {output_path}")
        self._update_status(f"{'='*63}\n")
        
        self._update_status_bar("Metadata export completed!", COLOR_SUCCESS)
        self.progress_bar.set(1.0)
        
        messagebox.showinfo(
            "Export Complete",
            f"Metadata successfully exported!\n\n"
            f"File: {output_path}\n"
            f"Runtime: {runtime_formatted}\n"
            f"Fields Exported: {stats['total_fields']}"
        )
        
        self.export_in_progress = False
        self.metadata_exporter = None
        self._enable_ui()
        self.metadata_btn.configure(
            text="📦 Metadata Exporter",
            command=self._export_metadata_action,
            fg_color=BUTTON_EXPORT
        )
    
    def _metadata_complete_cancelled(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when metadata export is cancelled"""
        self._update_status(f"\n{'='*63}")
        self._update_status(f"🛑 METADATA EXPORT CANCELLED")
        self._update_status(f"{'='*63}")
        self._update_status(f"Runtime: {runtime_formatted}")
        self._update_status(f"Processed: {stats['successful_objects']}/{stats['total_objects']} objects")
        self._update_status(f"Partial data saved to: {output_path}")
        self._update_status(f"{'='*63}\n")
        
        self._update_status_bar("Export cancelled", COLOR_WARNING)
        
        messagebox.showwarning(
            "Export Cancelled",
            f"Export was cancelled.\n\n"
            f"Partial data saved to:\n{output_path}\n\n"
            f"Processed: {stats['successful_objects']}/{stats['total_objects']} objects"
        )
        
        self.export_in_progress = False
        self.metadata_exporter = None
        self._enable_ui()
        self.metadata_btn.configure(
            text="📦 Metadata Exporter",
            command=self._export_metadata_action,
            fg_color=BUTTON_EXPORT
        )
    
    def _metadata_complete_error(self, error_message: str):
        """Called when metadata export fails"""
        self._update_status(f"\n❌ METADATA EXPORT ERROR: {error_message}\n")
        self._update_status_bar("Export failed!", COLOR_DANGER)
        
        messagebox.showerror("Export Error", f"Metadata export failed:\n\n{error_message}")
        
        self.export_in_progress = False
        self.metadata_exporter = None
        self._enable_ui()
        self.metadata_btn.configure(
            text="📦 Metadata Exporter",
            command=self._export_metadata_action,
            fg_color=BUTTON_EXPORT
        )