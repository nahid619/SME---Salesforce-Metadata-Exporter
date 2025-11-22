"""
SME - Main Export Screen UI (COMPLETE FIX - NO FREEZING)

CRITICAL FIXES APPLIED:
1. ✅ Added missing SOQLQueryScreen import
2. ✅ Removed ALL health checks that block UI
3. ✅ Implemented missing export methods
4. ✅ Added comprehensive error handling
5. ✅ Reduced progress throttling to 1% (from 5%)
6. ✅ Added emergency UI recovery
7. ✅ All blocking operations in background threads
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, END
from typing import List, Set, Callable, Dict
import time
import threading

# Import constants
from config.constants import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, BUTTON_EXPORT, 
    BUTTON_EXPORT_HOVER, BUTTON_CANCEL, BUTTON_PLACEHOLDER,
    TERMINAL_FONT, APP_NAME, APP_FULL_NAME
)

# Import utilities
from utils.helpers import format_runtime, get_timestamp, format_file_timestamp, print_statistics

# Import exporters
from exporters.picklist_exporter import PicklistExporter
from exporters.dependency_analyzer import DependencyAnalyzer
from exporters.metadata_exporter import MetadataExporter
from exporters.metadata_switch_manager import MetadataSwitchManager
from ui.salesforce_switch_frame import SalesforceSwitchFrame

# ✅ CRITICAL FIX: Import SOQLQueryScreen
# This was missing and caused NameError when clicking SOQL Query Runner button
try:
    from ui.soql_query_screen import SOQLQueryScreen
    SOQL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: SOQLQueryScreen not available: {e}")
    SOQL_AVAILABLE = False
    SOQLQueryScreen = None


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
        self.soql_screen = None
        self.sf_switch_screen = None
        
        # CRITICAL: Lazy loading flags
        self.objects_loaded = False
        self.objects_loading = False
        
        # Track current theme for listbox colors
        self.current_theme = "Dark"
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Setup UI FIRST (no blocking operations)
        self._setup_ui()
        
        # Start background loading SILENTLY (no UI blocking)
        self.after(100, self._start_background_load)
    
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
            text="(Click to load)",
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
        
        # Listbox - Start EMPTY
        self.available_listbox = tk.Listbox(
            available_frame,
            selectmode="extended",
            exportselection=False,
            font=("Segoe UI", 11),
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#1F538D",
            fg="#FFFFFF",
            background="#2B2B2B"
        )
        self.available_listbox.grid(row=4, column=0, padx=5, pady=(0, 5), sticky="nsew")
        
        # Load objects when user clicks
        self.available_listbox.bind("<Button-1>", self._on_listbox_interaction)
        self.available_listbox.bind("<FocusIn>", self._on_listbox_interaction)
    
    def _on_listbox_interaction(self, event=None):
        """Trigger object load when user interacts with listbox"""
        if not self.objects_loaded and not self.objects_loading:
            self._load_objects_on_demand()
    
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
        
        # Listbox
        self.selected_listbox = tk.Listbox(
            selected_frame,
            selectmode="extended",
            exportselection=False,
            font=("Segoe UI", 11),
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#3366CC",
            fg="#FFFFFF",
            background="#2B2B2B"
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
        buttons_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        self.picklist_export_btn = ctk.CTkButton(
            buttons_frame,
            text="📋 Export Picklist Data",
            command=self._export_picklist_action,
            height=42,
            fg_color="#FFA200",
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.picklist_export_btn.grid(row=0, column=0, padx=4, sticky="ew")
        
        self.dependency_btn = ctk.CTkButton(
            buttons_frame,
            text="🔗 Dependency Analysis",
            command=self._export_dependency_action,
            height=42,
            fg_color="#3564FF",
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.dependency_btn.grid(row=0, column=1, padx=4, sticky="ew")
        
        self.metadata_btn = ctk.CTkButton(
            buttons_frame,
            text="📦 Metadata Exporter",
            command=self._export_metadata_action,
            height=42,
            fg_color="#BF35FF",
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.metadata_btn.grid(row=0, column=2, padx=4, sticky="ew")
        
        self.soql_btn = ctk.CTkButton(
            buttons_frame,
            text="⚡ SOQL Query Runner",
            command=self._open_soql_query_screen,
            height=42,
            fg_color="#00C5AE" if SOQL_AVAILABLE else "gray",
            hover_color=BUTTON_EXPORT_HOVER if SOQL_AVAILABLE else "gray",
            font=ctk.CTkFont(size=13, weight="bold"),
            state="normal" if SOQL_AVAILABLE else "disabled"
        )
        self.soql_btn.grid(row=0, column=3, padx=4, sticky="ew")

        #NEW: Add this 5th button at the end
        self.sf_switch_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Salesforce Switch",
            command=self._open_salesforce_switch,
            height=42,
            fg_color="#FF6B35",
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.sf_switch_btn.grid(row=0, column=4, padx=4, sticky="ew")  # column=4 for 5th button

        # Add tooltip if disabled
        if not SOQL_AVAILABLE:
            # Create a simple label to show when hovering (optional)
            print("⚠️ SOQL Query Runner disabled - soql_query_screen.py not found")
    
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
            font=("Consolas", 12),
            wrap="word"
        )
        self.status_textbox.grid(row=6, column=0, padx=15, pady=(5, 10), sticky="nsew")
        
        # Welcome message
        self.status_textbox.insert("end", "╔" + "═" * 73 + "╗\n")
        self.status_textbox.insert("end", f"  {APP_NAME} - {APP_FULL_NAME} - Ready\n")
        self.status_textbox.insert("end", "╚" + "═" * 73 + "╝\n")
        self.status_textbox.insert("end", "\n✓ Connected successfully.\n")
        self.status_textbox.insert("end", "\n💡 Tip: Objects loading in background...\n")
        self.status_textbox.configure(state="disabled")
    
    # ==================== LAZY OBJECT LOADING (FIX) ====================
    
    def _start_background_load(self):
        """Start loading objects silently in background"""
        if self.objects_loading or self.objects_loaded:
            return
        
        self.objects_loading = True
        thread = threading.Thread(target=self._background_load_objects, daemon=True)
        thread.start()
    
    def _background_load_objects(self):
        """Background thread - loads objects"""
        try:
            objects = self.sf_client.fetch_all_objects()
            self.after(0, self._objects_loaded_success, objects)
        except Exception as e:
            self.after(0, self._objects_loaded_error, str(e))
    
    def _objects_loaded_success(self, objects: List[str]):
        """Called when objects finish loading"""
        self.all_org_objects = objects
        self.objects_loaded = True
        self.objects_loading = False
        
        # Count standard vs custom
        standard_count = sum(1 for obj in objects if not obj.endswith('__c'))
        custom_count = sum(1 for obj in objects if obj.endswith('__c'))
        
        # Update count with breakdown
        self.available_count_label.configure(
            text=f"({len(objects)} total: {standard_count} standard, {custom_count} custom)"
        )
        
        # Populate if listbox is empty
        if self.available_listbox.size() == 0:
            self._populate_available_objects()
        
        print(f"✓ Loaded {len(objects)} queryable objects")
        print(f"  - {standard_count} standard objects")
        print(f"  - {custom_count} custom objects")
    
    def _objects_loaded_error(self, error_msg: str):
        """Called when loading fails"""
        self.objects_loading = False
        self.available_count_label.configure(text="(Load failed)")
        print(f"✗ Failed to load objects: {error_msg}")
    
    def _load_objects_on_demand(self):
        """Force load objects when user clicks"""
        if self.objects_loaded:
            return
        
        if self.objects_loading:
            self.available_count_label.configure(text="(Loading...)")
            return
        
        # Show loading
        self.available_count_label.configure(text="(Loading...)")
        self.available_listbox.delete(0, END)
        self.available_listbox.insert(END, "⏳ Loading objects from Salesforce...")
        
        # Start loading
        self._start_background_load()
    
    # ==================== Event Handlers ====================
    
    def _toggle_theme(self):
        """Toggle between dark and light mode"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_toggle.configure(text="☀️")
            self.current_theme = "Light"
            self.available_listbox.configure(fg="#000000", background="#FFFFFF")
            self.selected_listbox.configure(fg="#000000", background="#FFFFFF")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_toggle.configure(text="🌙")
            self.current_theme = "Dark"
            self.available_listbox.configure(fg="#FFFFFF", background="#2B2B2B")
            self.selected_listbox.configure(fg="#FFFFFF", background="#2B2B2B")
    
    def _handle_logout(self):
        """Handle logout action"""
        if self.export_in_progress:
            messagebox.showwarning(
                "Export in Progress",
                "Cannot logout while export is running."
            )
            return
        
        confirm = messagebox.askyesno("Logout", "Are you sure you want to log out?")
        if confirm:
            self.on_logout()
    
    def _apply_filter(self, filter_type: str):
        """Apply object filter"""
        if not self.objects_loaded:
            self._load_objects_on_demand()
            return
        
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
        if not self.objects_loaded:
            return []
        
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
        if not self.objects_loaded:
            return
        
        self.available_listbox.delete(0, END)
        filtered_objects = self._get_filtered_objects()
        
        # Show first 200 for performance
        MAX_VISIBLE = 200
        for obj in filtered_objects[:MAX_VISIBLE]:
            self.available_listbox.insert(END, obj)
            if obj in self.selected_objects:
                idx = self.available_listbox.size() - 1
                self.available_listbox.itemconfig(idx, {'fg': '#87CEEB'})
        
        if len(filtered_objects) > MAX_VISIBLE:
            self.available_listbox.insert(END, "")
            self.available_listbox.insert(END, f"--- {len(filtered_objects) - MAX_VISIBLE} more (use search) ---")
    
    def _populate_selected_objects(self):
        """Populate selected objects listbox"""
        self.selected_listbox.delete(0, END)
        for obj in sorted(list(self.selected_objects)):
            self.selected_listbox.insert(END, obj)
    
    def _filter_available_objects(self, event):
        """Filter when user types in search box"""
        if not self.objects_loaded:
            self._load_objects_on_demand()
            return
        
        self._populate_available_objects()
        self._update_object_counts()
    
    def _update_object_counts(self):
        """Update count labels with detailed breakdown"""
        if not self.objects_loaded:
            return
        
        # Get filtered objects
        filtered = self._get_filtered_objects()
        
        # Count breakdown
        if self.current_filter == "all":
            standard_count = sum(1 for obj in filtered if not obj.endswith('__c'))
            custom_count = sum(1 for obj in filtered if obj.endswith('__c'))
            self.available_count_label.configure(
                text=f"({len(filtered)} total: {standard_count} std, {custom_count} cust)"
            )
        elif self.current_filter == "standard":
            self.available_count_label.configure(text=f"({len(filtered)} standard objects)")
        else:  # custom
            self.available_count_label.configure(text=f"({len(filtered)} custom objects)")
        
        # Selected count
        selected_count = len(self.selected_objects)
        self.selected_count_label.configure(text=f"({selected_count} selected)")
    
    def _add_selected_to_export(self):
        """Add selected objects to export list"""
        if not self.objects_loaded:
            self._load_objects_on_demand()
            return
        
        selected_indices = self.available_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("Selection", "Please select objects from the list.")
            return
        
        added_count = 0
        for i in selected_indices:
            obj_name = self.available_listbox.get(i)
            if obj_name not in self.selected_objects and not obj_name.startswith("---"):
                self.selected_objects.add(obj_name)
                added_count += 1
        
        if added_count > 0:
            self._populate_selected_objects()
            self._populate_available_objects()
            print(f"✓ Added {added_count} object(s)")
            self._update_object_counts()
    
    def _remove_selected_from_export(self):
        """Remove selected objects from export list"""
        selected_indices = self.selected_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("Selection", "Please select objects to remove.")
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
            print(f"✓ Removed {len(removed_objects)} object(s)")
            self._update_object_counts()
    
    def _select_all_available(self):
        """Add all visible objects to selected"""
        if not self.objects_loaded:
            self._load_objects_on_demand()
            return
        
        filtered_objects = self._get_filtered_objects()
        
        if not filtered_objects:
            messagebox.showinfo("No Objects", "No objects available to select.")
            return
        
        # ✅ SAFETY: Warn if selecting too many objects
        if len(filtered_objects) > 100:
            confirm = messagebox.askyesno(
                "Large Selection Warning",
                f"You are about to select {len(filtered_objects)} objects.\n\n"
                f"This may take significant time to export.\n\n"
                f"Recommendations:\n"
                f"• For faster exports, select fewer objects\n"
                f"• Use 'Standard' or 'Custom' filters first\n"
                f"• Or use search to narrow down\n\n"
                f"Continue with all {len(filtered_objects)} objects?",
                icon='warning'
            )
            if not confirm:
                return
        
        added_count = 0
        for obj in filtered_objects:
            if obj not in self.selected_objects:
                self.selected_objects.add(obj)
                added_count += 1
        
        if added_count > 0:
            self._populate_selected_objects()
            self._populate_available_objects()
            print(f"✓ Added ALL {added_count} object(s)")
            self._update_object_counts()
        else:
            messagebox.showinfo("Already Selected", "All objects already selected.")
    
    def _deselect_all_available(self):
        """Remove all objects from selected"""
        if not self.selected_objects:
            messagebox.showinfo("No Selection", "No objects selected.")
            return
        
        count = len(self.selected_objects)
        confirm = messagebox.askyesno("Deselect All", f"Remove all {count} objects?")
        
        if confirm:
            self.selected_objects.clear()
            self._populate_selected_objects()
            self._populate_available_objects()
            print(f"✓ Removed ALL {count} object(s)")
            self._update_object_counts()
    
    def _update_status(self, message: str, verbose: bool = False):
        """Update terminal - THROTTLED"""
        timestamp = get_timestamp()
        display_message = f"{timestamp} {message}"
        
        # Only update UI every 500ms
        if not hasattr(self, '_last_terminal_update'):
            self._last_terminal_update = 0
        
        current_time = time.time()
        if current_time - self._last_terminal_update > 0.5:
            try:
                self.status_textbox.configure(state="normal")
                self.status_textbox.insert("end", "\n" + display_message)
                self.status_textbox.see("end")
                self.status_textbox.configure(state="disabled")
                self._last_terminal_update = current_time
            except Exception as e:
                print(f"Terminal update error: {e}")
        
        if not verbose:
            print(display_message)
    
    def _update_status_bar(self, message: str, color: str = COLOR_SUCCESS):
        """Update status bar"""
        try:
            self.status_bar.configure(text=f"Status: {message}", fg_color=color)
        except Exception as e:
            print(f"Status bar update error: {e}")
    
    def _update_progress(self, current: int, total: int):
        """Update progress bar - THROTTLED to 1% (was 5%)"""
        if total > 0:
            progress = current / total
            percentage = int(progress * 100)
            
            # ✅ FIX #5: Update every 1% instead of 5%
            if not hasattr(self, '_last_progress_percentage'):
                self._last_progress_percentage = -1
            
            if percentage != self._last_progress_percentage:
                try:
                    self.progress_bar.set(progress)
                    self.progress_label.configure(text=f"{percentage}%")
                    self._update_status_bar(f"Processing {current}/{total}", COLOR_WARNING)
                    self._last_progress_percentage = percentage
                except Exception as e:
                    print(f"Progress update error: {e}")

    def _disable_ui(self):
        """Disable ALL export buttons and UI elements during export"""
        try:
            self.available_listbox.configure(state="disabled")
            self.selected_listbox.configure(state="disabled")
            self.search_entry.configure(state="disabled")
            self.picklist_export_btn.configure(state="disabled")
            self.dependency_btn.configure(state="disabled")
            self.metadata_btn.configure(state="disabled")
            self.soql_btn.configure(state="disabled")
            self.logout_button.configure(state="disabled")
            self.theme_toggle.configure(state="disabled")
            self.filter_all_btn.configure(state="disabled")
            self.filter_standard_btn.configure(state="disabled")
            self.filter_custom_btn.configure(state="disabled")
        except Exception as e:
            print(f"Disable UI error: {e}")

    def _enable_ui(self):
        """Re-enable ALL export buttons and UI elements after export"""
        try:
            self.available_listbox.configure(state="normal")
            self.selected_listbox.configure(state="normal")
            self.search_entry.configure(state="normal")
            self.picklist_export_btn.configure(state="normal")
            self.dependency_btn.configure(state="normal")
            self.metadata_btn.configure(state="normal")
            self.soql_btn.configure(state="normal")
            self.logout_button.configure(state="normal")
            self.theme_toggle.configure(state="normal")
            self.filter_all_btn.configure(state="normal")
            self.filter_standard_btn.configure(state="normal")
            self.filter_custom_btn.configure(state="normal")
        except Exception as e:
            print(f"Enable UI error: {e}")

    def _ensure_ui_enabled(self):
        """✅ FIX #6: SAFETY - Ensure UI is always re-enabled"""
        try:
            if self.export_in_progress:
                self.export_in_progress = False
                self._enable_ui()
                
                self.picklist_export_btn.configure(
                    text="📋 Export Picklist Data",
                    command=self._export_picklist_action,
                    fg_color=BUTTON_EXPORT,
                    state="normal"
                )
                self.dependency_btn.configure(
                    text="🔗 Dependency Analysis",
                    command=self._export_dependency_action,
                    fg_color=BUTTON_EXPORT,
                    state="normal"
                )
                self.metadata_btn.configure(
                    text="📦 Metadata Exporter",
                    command=self._export_metadata_action,
                    fg_color=BUTTON_EXPORT,
                    state="normal"
                )
                
                self.progress_bar.set(0)
                self.progress_label.configure(text="0%")
                print("🚨 Emergency UI recovery executed")
        except Exception as e:
            print(f"❌ UI recovery error: {e}")

    # ==================== SOQL QUERY SCREEN ====================

    def _open_soql_query_screen(self):
        """Open SOQL Query Runner screen - ✅ NOW WORKS WITH SAFETY CHECK"""
        try:
            # ✅ Safety check: Verify SOQLQueryScreen is available
            if not SOQL_AVAILABLE or SOQLQueryScreen is None:
                messagebox.showerror(
                    "Feature Unavailable",
                    "SOQL Query Runner is not available.\n\n"
                    "Please ensure soql_query_screen.py is in the ui/ folder."
                )
                return
            
            self.grid_forget()
            
            if self.soql_screen is None:
                self.soql_screen = SOQLQueryScreen(
                    self.master,
                    sf_client=self.sf_client,
                    on_back=self._close_soql_query_screen
                )
            
            self.soql_screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
        except NameError as e:
            messagebox.showerror(
                "Import Error", 
                f"SOQLQueryScreen is not defined.\n\n"
                f"Error: {str(e)}\n\n"
                f"Please ensure:\n"
                f"1. soql_query_screen.py exists in ui/ folder\n"
                f"2. File has no syntax errors\n"
                f"3. Class is properly defined"
            )
            self.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to open SOQL Query Runner:\n\n{str(e)}"
            )
            self.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def _close_soql_query_screen(self):
        """Close SOQL Query Runner screen"""
        try:
            if self.soql_screen:
                self.soql_screen.grid_forget()
            
            self.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        except Exception as e:
            print(f"Close SOQL screen error: {e}")
    
    def _open_salesforce_switch(self):
        """Open Salesforce Switch screen"""
        if not self.sf_client:
            messagebox.showerror("Error", "Not logged in to Salesforce.")
            return
        
        try:
            # Get org instance name (not ID)
            org_name = self.sf_client.base_url.replace('https://', '').replace('http://', '')
            
            # Hide main screen
            self.grid_forget()
            
            # Create Salesforce Switch screen if not exists
            if self.sf_switch_screen is None:
                # Create switch manager
                switch_manager = MetadataSwitchManager(
                    sf=self.sf_client.sf,
                    status_callback=self._update_status
                )
                
                # Create UI screen with back callback
                self.sf_switch_screen = SalesforceSwitchFrame(
                    self.master,
                    switch_manager=switch_manager,
                    username=org_name,
                    status_callback=self._update_status,
                    on_back_callback=self._close_salesforce_switch  # Pass callback here
                )
            
            # Show switch screen
            self.sf_switch_screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            # Load components in background
            self.sf_switch_screen.load_components()
            
            self._update_status("Opened Salesforce Switch")
            
        except Exception as e:
            self._update_status(f"Error opening Salesforce Switch: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to open Salesforce Switch:\n\n{str(e)}"
            )
            # Make sure to show main screen again on error
            self.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def _close_salesforce_switch(self):
        """Close Salesforce Switch screen and return to main screen"""
        if self.sf_switch_screen:
            self.sf_switch_screen.grid_forget()
        
        # Show main screen again
        self.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        self._update_status("Returned to main screen")

    def _close_salesforce_switch(self):
        """Close Salesforce Switch screen"""
        if self.sf_switch_screen:
            self.sf_switch_screen.grid_forget()
        
        # Show main screen again
        self.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        self._update_status("Returned to main screen")

    # ==================== EXPORT HANDLERS ====================

    def _export_picklist_action(self):
        """Handle picklist export action"""
        try:
            if not self.sf_client:
                messagebox.showerror("Error", "Not logged in.")
                return
            
            selected_objects_list = sorted(list(self.selected_objects))
            
            if not selected_objects_list:
                messagebox.showwarning("Warning", "Please add objects to export list.")
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
            
            self.picklist_exporter = PicklistExporter(self.sf_client, status_callback=self._update_status)
            
            export_thread = threading.Thread(
                target=self._run_picklist_export,
                args=(selected_objects_list, output_file_path, export_format),
                daemon=True
            )
            export_thread.start()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start export:\n\n{str(e)}")
            self._ensure_ui_enabled()

    def _cancel_export_action(self):
        """Cancel ongoing export"""
        try:
            confirm = messagebox.askyesno(
                "Cancel Export",
                "Are you sure you want to cancel the export?\n\nPartial data will be saved."
            )
            if confirm and self.picklist_exporter:
                self.picklist_exporter.cancel_export()
                self.picklist_export_btn.configure(text="Cancelling...", state="disabled")
                self._update_status_bar("Cancelling export...", COLOR_WARNING)
        except Exception as e:
            print(f"Cancel export error: {e}")

    def _run_picklist_export(self, selected_objects_list: List[str], output_file_path: str, export_format: str):
        """Background thread for picklist export operation"""
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
        
        finally:
            self.after(0, self._ensure_ui_enabled)

    def _export_complete_success(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when export completes successfully"""
        try:
            self._update_status(f"✅ EXPORT COMPLETED!")
            self._update_status(f"Runtime: {runtime_formatted}")
            self._update_status(f"API Calls: {stats.get('api_calls_made', 0)}")
            self._update_status(f"Output: {output_path}")
            
            self._update_status_bar("Export completed!", COLOR_SUCCESS)
            self.progress_bar.set(1.0)
            
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported!\n\nFile: {output_path}\nRuntime: {runtime_formatted}"
            )
            
            self.export_in_progress = False
            self.picklist_exporter = None
            self._enable_ui()
            self.picklist_export_btn.configure(
                text="📋 Export Picklist Data",
                command=self._export_picklist_action,
                fg_color=BUTTON_EXPORT
            )
        except Exception as e:
            print(f"Export complete handler error: {e}")
            self._ensure_ui_enabled()

    def _export_complete_cancelled(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when export is cancelled"""
        try:
            self._update_status(f"🛑 EXPORT CANCELLED")
            self._update_status_bar("Export cancelled", COLOR_WARNING)
            
            messagebox.showwarning("Export Cancelled", f"Partial data saved to:\n{output_path}")
            
            self.export_in_progress = False
            self.picklist_exporter = None
            self._enable_ui()
            self.picklist_export_btn.configure(
                text="📋 Export Picklist Data",
                command=self._export_picklist_action,
                fg_color=BUTTON_EXPORT
            )
        except Exception as e:
            print(f"Cancel handler error: {e}")
            self._ensure_ui_enabled()

    def _export_complete_error(self, error_message: str):
        """Called when export fails"""
        try:
            self._update_status(f"❌ EXPORT ERROR: {error_message}")
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
        except Exception as e:
            print(f"Error handler error: {e}")
            self._ensure_ui_enabled()

    # ✅ FIX #3: Implement missing dependency export
    def _export_dependency_action(self):
        """Handle dependency analysis"""
        try:
            if not self.sf_client:
                messagebox.showerror("Error", "Not logged in.")
                return
            
            selected_objects_list = sorted(list(self.selected_objects))
            
            if len(selected_objects_list) < 2:
                messagebox.showwarning("Warning", "Please select at least 2 objects for dependency analysis.")
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
            self._update_status_bar("Analyzing dependencies...", COLOR_WARNING)
            self.progress_bar.set(0)
            self.progress_label.configure(text="0%")
            
            self.dependency_analyzer = DependencyAnalyzer(self.sf_client, status_callback=self._update_status)
            
            analysis_thread = threading.Thread(
                target=self._run_dependency_analysis,
                args=(selected_objects_list, output_file_path, export_format),
                daemon=True
            )
            analysis_thread.start()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start analysis:\n\n{str(e)}")
            self._ensure_ui_enabled()

    def _cancel_dependency_action(self):
        """Cancel ongoing dependency analysis"""
        try:
            confirm = messagebox.askyesno(
                "Cancel Analysis",
                "Are you sure you want to cancel the analysis?"
            )
            if confirm and self.dependency_analyzer:
                self.dependency_analyzer.cancel_analysis()
                self.dependency_btn.configure(text="Cancelling...", state="disabled")
                self._update_status_bar("Cancelling analysis...", COLOR_WARNING)
        except Exception as e:
            print(f"Cancel analysis error: {e}")

    def _run_dependency_analysis(self, selected_objects_list: List[str], output_file_path: str, export_format: str):
        """Background thread for dependency analysis"""
        start_time = time.time()
        
        try:
            output_path, stats = self.dependency_analyzer.analyze_dependencies(
                selected_objects_list,
                output_file_path,
                export_format=export_format,
                progress_callback=self._update_progress
            )
            
            end_time = time.time()
            runtime_formatted = format_runtime(end_time - start_time)
            
            if stats.get('cancelled'):
                self.after(0, self._dependency_complete_cancelled, output_path, runtime_formatted)
            else:
                self.after(0, self._dependency_complete_success, output_path, stats, runtime_formatted)
        
        except Exception as e:
            self.after(0, self._dependency_complete_error, str(e))
        
        finally:
            self.after(0, self._ensure_ui_enabled)

    def _dependency_complete_success(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when dependency analysis completes"""
        try:
            self._update_status(f"✅ ANALYSIS COMPLETED!")
            self._update_status(f"Runtime: {runtime_formatted}")
            self._update_status(f"Output: {output_path}")
            
            self._update_status_bar("Analysis completed!", COLOR_SUCCESS)
            self.progress_bar.set(1.0)
            
            messagebox.showinfo(
                "Analysis Complete",
                f"Dependency analysis completed!\n\nFile: {output_path}\nRuntime: {runtime_formatted}"
            )
            
            self.export_in_progress = False
            self.dependency_analyzer = None
            self._enable_ui()
            self.dependency_btn.configure(
                text="🔗 Dependency Analysis",
                command=self._export_dependency_action,
                fg_color=BUTTON_EXPORT
            )
        except Exception as e:
            print(f"Dependency complete handler error: {e}")
            self._ensure_ui_enabled()

    def _dependency_complete_cancelled(self, output_path: str, runtime_formatted: str):
        """Called when analysis is cancelled"""
        try:
            self._update_status(f"🛑 ANALYSIS CANCELLED")
            self._update_status_bar("Analysis cancelled", COLOR_WARNING)
            
            messagebox.showwarning("Analysis Cancelled", "Dependency analysis was cancelled.")
            
            self.export_in_progress = False
            self.dependency_analyzer = None
            self._enable_ui()
            self.dependency_btn.configure(
                text="🔗 Dependency Analysis",
                command=self._export_dependency_action,
                fg_color=BUTTON_EXPORT
            )
        except Exception as e:
            print(f"Dependency cancel handler error: {e}")
            self._ensure_ui_enabled()

    def _dependency_complete_error(self, error_message: str):
        """Called when analysis fails"""
        try:
            self._update_status(f"❌ ANALYSIS ERROR: {error_message}")
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
        except Exception as e:
            print(f"Dependency error handler error: {e}")
            self._ensure_ui_enabled()

    # ✅ FIX #3: Implement missing metadata export
    def _export_metadata_action(self):
        """Handle metadata export"""
        try:
            if not self.sf_client:
                messagebox.showerror("Error", "Not logged in.")
                return
            
            selected_objects_list = sorted(list(self.selected_objects))
            
            if not selected_objects_list:
                messagebox.showwarning("Warning", "Please add objects to export list.")
                return
            
            # Show options dialog
            options_dialog = ctk.CTkToplevel(self)
            options_dialog.title("Metadata Export Options")
            options_dialog.geometry("450x250")
            options_dialog.transient(self)
            options_dialog.grab_set()
            
            # Center dialog
            options_dialog.update_idletasks()
            x = (options_dialog.winfo_screenwidth() // 2) - 225
            y = (options_dialog.winfo_screenheight() // 2) - 125
            options_dialog.geometry(f"+{x}+{y}")
            
            main_frame = ctk.CTkFrame(options_dialog)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(
                main_frame,
                text="Metadata Export Options",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=(0, 20))
            
            custom_only_var = ctk.BooleanVar(value=False)
            include_usage_var = ctk.BooleanVar(value=True)
            
            ctk.CTkCheckBox(
                main_frame,
                text="Export custom fields only",
                variable=custom_only_var,
                font=ctk.CTkFont(size=13)
            ).pack(pady=10, anchor="w")
            
            ctk.CTkCheckBox(
                main_frame,
                text="Include field usage analysis (slower but recommended)",
                variable=include_usage_var,
                font=ctk.CTkFont(size=13)
            ).pack(pady=10, anchor="w")
            
            def start_export():
                options_dialog.destroy()
                self._start_metadata_export(
                    selected_objects_list,
                    custom_only_var.get(),
                    include_usage_var.get()
                )
            
            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(pady=(20, 0))
            
            ctk.CTkButton(
                button_frame,
                text="Continue",
                command=start_export,
                fg_color=BUTTON_EXPORT,
                hover_color=BUTTON_EXPORT_HOVER,
                width=120,
                height=35
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                button_frame,
                text="Cancel",
                command=options_dialog.destroy,
                fg_color="gray",
                width=120,
                height=35
            ).pack(side="left", padx=5)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show options:\n\n{str(e)}")

    def _start_metadata_export(self, selected_objects_list: List[str], custom_only: bool, include_usage: bool):
        """Start metadata export after options selected"""
        try:
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
            self._update_status_bar("Exporting metadata...", COLOR_WARNING)
            self.progress_bar.set(0)
            self.progress_label.configure(text="0%")
            
            self.metadata_exporter = MetadataExporter(self.sf_client, status_callback=self._update_status)
            
            metadata_thread = threading.Thread(
                target=self._run_metadata_export,
                args=(selected_objects_list, output_file_path, export_format, include_usage, custom_only),
                daemon=True
            )
            metadata_thread.start()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start metadata export:\n\n{str(e)}")
            self._ensure_ui_enabled()

    def _cancel_metadata_action(self):
        """Cancel ongoing metadata export"""
        try:
            confirm = messagebox.askyesno(
                "Cancel Export",
                "Are you sure you want to cancel the metadata export?"
            )
            if confirm and self.metadata_exporter:
                self.metadata_exporter.cancel_export()
                self.metadata_btn.configure(text="Cancelling...", state="disabled")
                self._update_status_bar("Cancelling export...", COLOR_WARNING)
        except Exception as e:
            print(f"Cancel metadata error: {e}")

    def _run_metadata_export(self, selected_objects_list: List[str], output_file_path: str, 
                            export_format: str, include_usage: bool, custom_only: bool):
        """Background thread for metadata export"""
        start_time = time.time()
        
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
            runtime_formatted = format_runtime(end_time - start_time)
            
            if stats.get('cancelled'):
                self.after(0, self._metadata_complete_cancelled, output_path, runtime_formatted)
            else:
                self.after(0, self._metadata_complete_success, output_path, stats, runtime_formatted)
        
        except Exception as e:
            self.after(0, self._metadata_complete_error, str(e))
        
        finally:
            self.after(0, self._ensure_ui_enabled)

    def _metadata_complete_success(self, output_path: str, stats: Dict, runtime_formatted: str):
        """Called when metadata export completes"""
        try:
            self._update_status(f"✅ METADATA EXPORT COMPLETED!")
            self._update_status(f"Runtime: {runtime_formatted}")
            self._update_status(f"Total Fields: {stats.get('total_fields', 0)}")
            self._update_status(f"Output: {output_path}")
            
            self._update_status_bar("Metadata export completed!", COLOR_SUCCESS)
            self.progress_bar.set(1.0)
            
            messagebox.showinfo(
                "Export Complete",
                f"Metadata export completed!\n\nFile: {output_path}\nFields: {stats.get('total_fields', 0)}\nRuntime: {runtime_formatted}"
            )
            
            self.export_in_progress = False
            self.metadata_exporter = None
            self._enable_ui()
            self.metadata_btn.configure(
                text="📦 Metadata Exporter",
                command=self._export_metadata_action,
                fg_color=BUTTON_EXPORT
            )
        except Exception as e:
            print(f"Metadata complete handler error: {e}")
            self._ensure_ui_enabled()

    def _metadata_complete_cancelled(self, output_path: str, runtime_formatted: str):
        """Called when metadata export is cancelled"""
        try:
            self._update_status(f"🛑 METADATA EXPORT CANCELLED")
            self._update_status_bar("Export cancelled", COLOR_WARNING)
            
            messagebox.showwarning("Export Cancelled", f"Partial data saved to:\n{output_path}")
            
            self.export_in_progress = False
            self.metadata_exporter = None
            self._enable_ui()
            self.metadata_btn.configure(
                text="📦 Metadata Exporter",
                command=self._export_metadata_action,
                fg_color=BUTTON_EXPORT
            )
        except Exception as e:
            print(f"Metadata cancel handler error: {e}")
            self._ensure_ui_enabled()

    def _metadata_complete_error(self, error_message: str):
        """Called when metadata export fails"""
        try:
            self._update_status(f"❌ METADATA EXPORT ERROR: {error_message}")
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
        except Exception as e:
            print(f"Metadata error handler error: {e}")
            self._ensure_ui_enabled()