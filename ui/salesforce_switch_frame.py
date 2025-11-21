"""
Salesforce Switch Frame - UI for bulk enabling/disabling automation components
Uses direct threading.Thread (no ThreadHelper dependency)
"""
import tkinter as tk
from tkinter import messagebox
from typing import List
import customtkinter as ctk
import threading

from exporters.metadata_switch_manager import MetadataSwitchManager, MetadataComponent


class SalesforceSwitchFrame(ctk.CTkFrame):
    """Frame for Salesforce Switch functionality"""
    
    def __init__(self, parent, switch_manager: MetadataSwitchManager, 
                 username: str, status_callback=None, on_back_callback=None):
        super().__init__(parent)
        
        self.switch_manager = switch_manager
        self.username = username
        self.status_callback = status_callback
        self.on_back_callback = on_back_callback  # NEW: Callback to return to main screen
        
        # Current tab
        self.current_tab = "ValidationRule"
        
        # Search state
        self.search_text = tk.StringVar()
        self.search_text.trace('w', lambda *args: self._on_search_changed())
        
        # Component checkboxes storage
        self.component_checkboxes: List = []
        
        # Filtered components cache
        self.filtered_components: List[MetadataComponent] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self._setup_header()
        self._setup_info_banner()
        self._setup_tabs()
        self._setup_action_buttons()
        self._setup_status_bar()
    
    def _setup_header(self):
        """Setup header with back button and title"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=(10, 5), sticky="ew", padx=20)
        header_frame.columnconfigure(1, weight=1)
        
        self.back_button = ctk.CTkButton(
            header_frame,
            text="← Back",
            command=self._on_back,
            width=100,
            fg_color="#666666"
        )
        self.back_button.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="Salesforce Switch - Automation Control",
            font=ctk.CTkFont(size=30, weight="bold")
        ).grid(row=0, column=1, sticky="w")
        
        ctk.CTkLabel(
            header_frame,
            text=f"Org: {self.username}",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        ).grid(row=0, column=2, sticky="e", padx=10)
    
    def _setup_info_banner(self):
        """Setup info banner with warnings"""
        info_frame = ctk.CTkFrame(self, fg_color="#1F538D")
        info_frame.grid(row=1, column=0, pady=(5, 10), sticky="ew", padx=20)
        info_frame.grid_columnconfigure(0, weight=1)
        
        info_text = (
            "ℹ️ Salesforce Switch: Quickly enable/disable automation components in bulk.\n"
            "⚠️ WARNING: Triggers take longer to deploy (especially in Production) because all Apex tests must run.\n"
            "💡 TIP: Use 'Rollback to Original' to undo all changes before deploying."
        )
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=1000
        ).grid(row=0, column=0, sticky="w", padx=15, pady=10)
    
    def _setup_tabs(self):
        """Setup tabbed interface for different component types"""
        tabs_container = ctk.CTkFrame(self)
        tabs_container.grid(row=2, column=0, pady=10, sticky="nsew", padx=20)
        tabs_container.grid_columnconfigure(0, weight=1)
        tabs_container.grid_rowconfigure(2, weight=1)
        
        # Tab buttons frame
        tab_buttons_frame = ctk.CTkFrame(tabs_container, fg_color="transparent")
        tab_buttons_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Create tab buttons
        self.tab_buttons = {}
        tabs = [
            ("Validation Rules", "ValidationRule"),
            ("Workflow Rules", "WorkflowRule"),
            ("Process Flows", "Flow"),
            ("Apex Triggers", "ApexTrigger")
        ]
        
        for idx, (label, tab_type) in enumerate(tabs):
            btn = ctk.CTkButton(
                tab_buttons_frame,
                text=label,
                command=lambda t=tab_type: self._switch_tab(t),
                height=40,
                width=180,
                fg_color="#1F538D" if tab_type == self.current_tab else "#666666"
            )
            btn.grid(row=0, column=idx, padx=5)
            self.tab_buttons[tab_type] = btn
        
        # Bulk action buttons
        bulk_frame = ctk.CTkFrame(tab_buttons_frame, fg_color="transparent")
        bulk_frame.grid(row=0, column=len(tabs), padx=(20, 0), sticky="e")
        tab_buttons_frame.grid_columnconfigure(len(tabs), weight=1)

        self.enable_all_button = ctk.CTkButton(
            bulk_frame,
            text="✅ ENABLE ALL",
            command=lambda: self._bulk_action(True),
            height=40,
            width=140,
            fg_color="green"
        )
        self.enable_all_button.grid(row=0, column=0, padx=(0, 5))

        self.disable_all_button = ctk.CTkButton(
            bulk_frame,
            text="❌ DISABLE ALL",
            command=lambda: self._bulk_action(False),
            height=40,
            width=140,
            fg_color="#CC3333"
        )
        self.disable_all_button.grid(row=0, column=1, padx=(5, 0))
        
        # Search and refresh frame
        search_frame = ctk.CTkFrame(tabs_container, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search components...",
            textvariable=self.search_text,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.clear_search_button = ctk.CTkButton(
            search_frame,
            text="✕ Clear",
            command=self._clear_search,
            width=80,
            height=40,
            fg_color="#666666"
        )
        self.clear_search_button.grid(row=0, column=1, padx=(5, 10))
        
        self.refresh_button = ctk.CTkButton(
            search_frame,
            text="🔄 Refresh",
            command=self._refresh_current_tab,
            width=140,
            height=40,
            fg_color="#1B518F"
        )
        self.refresh_button.grid(row=0, column=2, padx=(5, 0))
        
        # Components list container
        list_container = ctk.CTkFrame(tabs_container)
        list_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(0, weight=1)
        
        self.components_scroll = ctk.CTkScrollableFrame(
            list_container,
            label_text="Components"
        )
        self.components_scroll.grid(row=0, column=0, sticky="nsew")
        self.components_scroll.grid_columnconfigure(0, weight=1)
        
        self._populate_components()
    
    def _setup_action_buttons(self):
        """Setup main action buttons"""
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=3, column=0, pady=(10, 10), sticky="ew", padx=20)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)
        
        self.rollback_button = ctk.CTkButton(
            action_frame,
            text="🔄 ROLLBACK TO ORIGINAL",
            command=self._rollback_changes,
            height=50,
            fg_color="#FF6B35",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.rollback_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.deploy_button = ctk.CTkButton(
            action_frame,
            text="🚀 DEPLOY CHANGES",
            command=self._deploy_changes,
            height=50,
            fg_color="green",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.deploy_button.grid(row=0, column=1, sticky="ew", padx=(10, 0))
    
    def _setup_status_bar(self):
        """Setup status bar"""
        status_frame = ctk.CTkFrame(self, height=30)
        status_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready - Select components to enable/disable",
            anchor="w",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.modified_label = ctk.CTkLabel(
            status_frame,
            text="Modified: 0",
            anchor="e",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FF6B35"
        )
        self.modified_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
    
    def _switch_tab(self, tab_type: str):
        """Switch to a different tab"""
        self.current_tab = tab_type
        
        for tab, btn in self.tab_buttons.items():
            if tab == tab_type:
                btn.configure(fg_color="#1F538D")
            else:
                btn.configure(fg_color="#666666")
        
        self._populate_components()
        self._update_status(f"Viewing {tab_type}s")
    
    def _on_search_changed(self):
        """Handle search text changes"""
        self._populate_components()
    
    def _clear_search(self):
        """Clear the search field"""
        self.search_text.set("")
        self.search_entry.focus()
    
    def _filter_components(self, components: List[MetadataComponent]) -> List[MetadataComponent]:
        """Filter components based on search text"""
        search_term = self.search_text.get().strip().lower()
        
        if not search_term:
            return components
        
        return [c for c in components if search_term in c.name.lower()]
    
    def _populate_components(self):
        """Populate the components list for current tab"""
        for widget in self.components_scroll.winfo_children():
            widget.destroy()
        
        self.component_checkboxes.clear()
        
        all_components = self.switch_manager.get_components(self.current_tab)
        
        if not all_components:
            ctk.CTkLabel(
                self.components_scroll,
                text=f"No {self.current_tab}s found in this org",
                font=ctk.CTkFont(size=14),
                text_color="#888888"
            ).grid(row=0, column=0, pady=20)
            
            self.components_scroll.configure(
                label_text=f"{self.current_tab}s (0 components)"
            )
            return
        
        self.filtered_components = self._filter_components(all_components)
        
        if self.search_text.get().strip():
            label = f"{self.current_tab}s ({len(self.filtered_components)} of {len(all_components)} components)"
        else:
            label = f"{self.current_tab}s ({len(all_components)} components)"
        
        self.components_scroll.configure(label_text=label)
        
        if not self.filtered_components:
            ctk.CTkLabel(
                self.components_scroll,
                text=f"No components match your search",
                font=ctk.CTkFont(size=14),
                text_color="#888888"
            ).grid(row=0, column=0, pady=20)
            return
        
        for idx, component in enumerate(self.filtered_components):
            self._create_component_row(idx, component)
        
        self._update_modified_count()
        self._update_tab_counts()
    
    def _create_component_row(self, row_idx: int, component: MetadataComponent):
        """Create a row for a component with checkbox and info"""
        row_frame = ctk.CTkFrame(
            self.components_scroll,
            fg_color="#2b2b2b" if row_idx % 2 == 0 else "#333333"
        )
        row_frame.grid(row=row_idx, column=0, sticky="ew", padx=5, pady=2)
        row_frame.grid_columnconfigure(1, weight=1)
        
        var = tk.BooleanVar(value=component.is_active)
        checkbox = ctk.CTkCheckBox(
            row_frame,
            text="",
            variable=var,
            command=lambda c=component, v=var: self._on_component_toggle(c, v),
            width=30
        )
        checkbox.grid(row=0, column=0, padx=10, pady=8)
        self.component_checkboxes.append((checkbox, component, var))
        
        name_button = ctk.CTkButton(
            row_frame,
            text=component.name,
            command=lambda c=component: self._show_component_details(c),
            fg_color="transparent",
            hover_color="#1F538D",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        name_button.grid(row=0, column=1, sticky="ew", padx=5)
        
        status_text = "✅ Active" if component.is_active else "❌ Inactive"
        status_color = "green" if component.is_active else "#CC3333"
        
        status_label = ctk.CTkLabel(
            row_frame,
            text=status_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=status_color,
            width=100
        )
        status_label.grid(row=0, column=2, padx=10)
        
        if component.modified:
            modified_label = ctk.CTkLabel(
                row_frame,
                text="⚠️ Modified",
                font=ctk.CTkFont(size=10),
                text_color="#FF6B35"
            )
            modified_label.grid(row=0, column=3, padx=10)
    
    def _on_component_toggle(self, component: MetadataComponent, var: tk.BooleanVar):
        """Handle component toggle"""
        new_state = var.get()
        component.set_active(new_state)
        
        self._populate_components()
        self._update_modified_count()
        
        action = "enabled" if new_state else "disabled"
        self._update_status(f"Marked {component.name} for {action}")
    
    def _bulk_action(self, enable: bool):
        """Enable or disable all components in current tab"""
        action_text = "enable" if enable else "disable"
        
        components = self.filtered_components if self.search_text.get().strip() else self.switch_manager.get_components(self.current_tab)
        
        if not components:
            messagebox.showinfo(
                "No Components",
                f"There are no {self.current_tab}s to {action_text}."
            )
            return
        
        search_msg = " (filtered by search)" if self.search_text.get().strip() else ""
        confirm = messagebox.askyesno(
            "Confirm Bulk Action",
            f"Are you sure you want to {action_text} ALL visible {self.current_tab}s{search_msg}?\n\n"
            f"This will affect {len(components)} component(s)."
        )
        
        if not confirm:
            return
        
        for component in components:
            component.set_active(enable)
        
        self._populate_components()
        self._update_status(f"Bulk {action_text}d {len(components)} {self.current_tab}s")
        self._update_modified_count()
    
    def _refresh_current_tab(self):
        """Refresh components for the current tab only"""
        modified_count = self.switch_manager.get_modified_count(self.current_tab)
        
        if modified_count > 0:
            confirm = messagebox.askyesno(
                "Unsaved Changes Warning",
                f"You have {modified_count} unsaved change(s) in {self.current_tab}s.\n\n"
                f"Refreshing will discard these changes.\n\n"
                f"Do you want to continue?"
            )
            if not confirm:
                return
        
        current_tab = self.current_tab
        self._set_loading_state(True, "Refreshing...")
        
        def do_refresh():
            try:
                self.after(0, lambda: self._log(f"=== Refreshing {current_tab}s ==="))
                
                count = 0
                if current_tab == "ValidationRule":
                    self.switch_manager.validation_rules = self.switch_manager._fetch_validation_rules()
                    count = len(self.switch_manager.validation_rules)
                elif current_tab == "WorkflowRule":
                    self.switch_manager.workflow_rules = self.switch_manager._fetch_workflow_rules()
                    count = len(self.switch_manager.workflow_rules)
                elif current_tab == "Flow":
                    self.switch_manager.flows = self.switch_manager._fetch_flows()
                    count = len(self.switch_manager.flows)
                elif current_tab == "ApexTrigger":
                    self.switch_manager.triggers = self.switch_manager._fetch_triggers()
                    count = len(self.switch_manager.triggers)
                
                self.after(0, lambda c=count: self._on_refresh_complete(c))
            
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda: self._on_refresh_error(error_msg))
        
        threading.Thread(target=do_refresh, daemon=True).start()
    
    def _on_refresh_complete(self, count: int):
        """Called when refresh completes"""
        self._set_loading_state(False)
        self.search_text.set("")
        self._populate_components()
        
        message = f"✅ Refreshed {count} {self.current_tab}s"
        self._update_status(message)
        messagebox.showinfo("Refresh Complete", message)
    
    def _on_refresh_error(self, error: str):
        """Called when refresh fails"""
        self._set_loading_state(False)
        
        message = f"❌ Error refreshing {self.current_tab}s: {error}"
        self._update_status(message)
        messagebox.showerror("Refresh Error", message)
    
    def _rollback_changes(self):
        """Rollback all changes to original state"""
        modified_count = self.switch_manager.get_modified_count(self.current_tab)
        
        if modified_count == 0:
            messagebox.showinfo(
                "No Changes",
                "There are no modified components to rollback."
            )
            return
        
        confirm = messagebox.askyesno(
            "Confirm Rollback",
            f"Are you sure you want to rollback {modified_count} modified {self.current_tab}(s)?\n\n"
            f"This will restore them to their original state."
        )
        
        if not confirm:
            return
        
        self.switch_manager.rollback_all(self.current_tab)
        self._populate_components()
        self._update_status(f"✅ Rolled back {modified_count} component(s) to original state")
        
        messagebox.showinfo(
            "Rollback Complete", 
            f"Successfully rolled back {modified_count} component(s) to original state."
        )
    
    def _deploy_changes(self):
        """Deploy changes to Salesforce"""
        components = self.switch_manager.get_components(self.current_tab)
        modified_components = [c for c in components if c.modified]
        
        if not modified_components:
            messagebox.showinfo(
                "No Changes",
                "There are no modified components to deploy."
            )
            return
        
        enabled_count = sum(1 for c in modified_components if c.is_active)
        disabled_count = len(modified_components) - enabled_count
        
        if self.current_tab == "ApexTrigger":
            confirm = messagebox.askyesno(
                "Deploy Triggers Warning",
                f"⚠️ You are about to deploy {len(modified_components)} Apex Trigger(s):\n"
                f"  • {enabled_count} will be ENABLED\n"
                f"  • {disabled_count} will be DISABLED\n\n"
                f"This operation will run ALL Apex tests in your org and may take 5-15 minutes.\n\n"
                f"Do you want to proceed?"
            )
        else:
            confirm = messagebox.askyesno(
                "Confirm Deployment",
                f"Are you sure you want to deploy {len(modified_components)} modified {self.current_tab}(s)?\n\n"
                f"  • {enabled_count} will be ENABLED\n"
                f"  • {disabled_count} will be DISABLED"
            )
        
        if not confirm:
            return
        
        self._set_loading_state(True, "Deploying...")
        
        def do_deploy():
            run_tests = (self.current_tab == "ApexTrigger")
            success, message = self.switch_manager.deploy_changes(
                self.current_tab,
                modified_components,
                run_tests=run_tests
            )
            
            self.after(0, lambda: self._on_deploy_complete(success, message))
        
        threading.Thread(target=do_deploy, daemon=True).start()
    
    def _on_deploy_complete(self, success: bool, message: str):
        """Called when deployment completes"""
        self._set_loading_state(False)
        
        if success:
            messagebox.showinfo("Deployment Complete", message)
            self._populate_components()
            self._update_status("✅ Deployment successful - all changes committed")
        else:
            messagebox.showerror("Deployment Failed", message)
            self._update_status("❌ Deployment failed - see error details above")
        
        self._update_modified_count()
        self._update_tab_counts()
    
    def _set_loading_state(self, is_loading: bool, loading_text: str = "Loading..."):
        """Set loading state for all controls"""
        if is_loading:
            self.deploy_button.configure(state="disabled", text=f"⏳ {loading_text.upper()}")
            self.rollback_button.configure(state="disabled")
            self.enable_all_button.configure(state="disabled")
            self.disable_all_button.configure(state="disabled")
            self.refresh_button.configure(state="disabled", text="⏳ Loading...")
            self.search_entry.configure(state="disabled")
            self.clear_search_button.configure(state="disabled")
            
            for btn in self.tab_buttons.values():
                btn.configure(state="disabled")
            
            for checkbox, _, _ in self.component_checkboxes:
                checkbox.configure(state="disabled")
        else:
            self.deploy_button.configure(state="normal", text="🚀 DEPLOY CHANGES")
            self.rollback_button.configure(state="normal")
            self.enable_all_button.configure(state="normal")
            self.disable_all_button.configure(state="normal")
            self.refresh_button.configure(state="normal", text="🔄 Refresh")
            self.search_entry.configure(state="normal")
            self.clear_search_button.configure(state="normal")
            
            for btn in self.tab_buttons.values():
                btn.configure(state="normal")
            
            for checkbox, _, _ in self.component_checkboxes:
                checkbox.configure(state="normal")
    
    def _show_component_details(self, component: MetadataComponent):
        """Show component metadata details in a dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Component Details - {component.name}")
        dialog.geometry("700x500")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(
            dialog,
            text=component.name,
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10, padx=20)
        
        details_frame = ctk.CTkFrame(dialog)
        details_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        metadata_text = ctk.CTkTextbox(details_frame, wrap="word")
        metadata_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        details = f"Component Type: {component.component_type}\n"
        details += f"Full Name: {component.full_name}\n"
        details += f"Record ID: {component.record_id}\n\n"
        details += f"Current Status: {'Active' if component.is_active else 'Inactive'}\n"
        details += f"Original Status: {'Active' if component.original_is_active else 'Inactive'}\n"
        details += f"Modified: {'Yes ⚠️' if component.modified else 'No'}\n\n"
        details += "=== Metadata ===\n"
        
        for key, value in component.metadata.items():
            if key != 'body':
                details += f"{key}: {value}\n"
        
        metadata_text.insert("1.0", details)
        metadata_text.configure(state="disabled")
        
        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=100
        ).pack(pady=10)
    
    def _update_tab_counts(self):
        """Update tab button texts with component counts"""
        tab_labels = {
            "ValidationRule": "Validation Rules",
            "WorkflowRule": "Workflow Rules",
            "Flow": "Process Flows",
            "ApexTrigger": "Apex Triggers"
        }
        
        for tab_type, btn in self.tab_buttons.items():
            components = self.switch_manager.get_components(tab_type)
            count = len(components)
            label = tab_labels[tab_type]
            btn.configure(text=f"{label} ({count})")
    
    def _update_modified_count(self):
        """Update the modified count label"""
        modified_count = self.switch_manager.get_modified_count(self.current_tab)
        
        if modified_count > 0:
            self.modified_label.configure(
                text=f"Modified: {modified_count}",
                text_color="#FF6B35"
            )
        else:
            self.modified_label.configure(
                text="Modified: 0",
                text_color="#888888"
            )
    
    def _update_status(self, message: str):
        """Update status label"""
        self.status_label.configure(text=message)
        if self.status_callback:
            self.status_callback(message, verbose=True)
    
    def _log(self, message: str):
        """Log message through status callback"""
        if self.status_callback:
            self.status_callback(message, verbose=True)
    
    def _on_back(self):
        """Handle back button click"""
        total_modified = sum(
            self.switch_manager.get_modified_count(component_type)
            for component_type in ["ValidationRule", "WorkflowRule", "Flow", "ApexTrigger"]
        )
        
        if total_modified > 0:
            confirm = messagebox.askyesno(
                "Unsaved Changes",
                f"You have {total_modified} unsaved change(s).\n\n"
                f"Are you sure you want to go back?\n"
                f"All unsaved changes will be lost."
            )
            if not confirm:
                return
        
        # ✅ FIX: Actually call the callback to return to main screen
        if self.on_back_callback:
            self.on_back_callback()
    
    def load_components(self):
        """Load components from Salesforce (called when frame is shown)"""
        self._update_status("Loading automation components...")
        self._set_loading_state(True, "Loading all components...")
        
        def do_load():
            try:
                stats = self.switch_manager.fetch_all_components()
                self.after(0, lambda: self._on_load_complete(stats))
            except Exception as e:
                self.after(0, lambda: self._on_load_error(str(e)))
        
        threading.Thread(target=do_load, daemon=True).start()
    
    def _on_load_complete(self, stats: dict):
        """Called when component loading completes"""
        self._populate_components()
        self._set_loading_state(False)
        
        # Update all tab counts
        self._update_tab_counts()
        
        summary = (
            f"✅ Loaded: {stats['validation_rules']} Validation Rules, "
            f"{stats['workflow_rules']} Workflow Rules, "
            f"{stats['flows']} Process Flows, "
            f"{stats['triggers']} Apex Triggers"
        )
        
        self._update_status(summary)
        messagebox.showinfo("Components Loaded", summary)
    
    def _on_load_error(self, error: str):
        """Called when component loading fails"""
        self._set_loading_state(False)
        self._update_status(f"❌ Error loading components: {error}")
        messagebox.showerror("Load Error", f"Failed to load components:\n{error}")
        self.deploy_button.configure(state="disabled")
        self.rollback_button.configure(state="disabled")