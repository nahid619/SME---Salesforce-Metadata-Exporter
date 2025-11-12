"""
SME - SOQL Query Runner Screen UI (UPDATED - Full Featured)
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Toplevel
from typing import Callable, List, Dict
import threading
import re
from config.constants import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from utils.helpers import get_timestamp, format_file_timestamp
from exporters.soql_query_runner import SOQLQueryRunner


class SOQLQueryScreen(ctk.CTkFrame):
    """SOQL Query Runner screen for executing and exporting queries"""
    
    def __init__(self, parent, sf_client, on_back: Callable):
        """
        Initialize SOQL Query screen
        
        Args:
            parent: Parent widget
            sf_client: Salesforce client instance
            on_back: Callback function to return to main screen
        """
        super().__init__(parent)
        self.sf_client = sf_client
        self.on_back = on_back
        
        # State variables
        self.query_results: List[Dict] = []
        self.query_in_progress = False
        self.query_runner = SOQLQueryRunner(sf_client, status_callback=self._log_status)
        
        # Load all objects from org
        self.all_objects = self._load_org_objects()
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)  # Query section - moderate space
        self.grid_rowconfigure(2, weight=2)  # Results section - more space (2x)
        self.grid_columnconfigure(0, weight=1)
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup SOQL Query UI components"""
        # Header
        self._create_header()
        
        # Query Input Section
        self._create_query_input()
        
        # Results Display
        self._create_results_display()
        
        # Status Bar
        self._create_status_bar()
        
        # Progress Bar
        self._create_progress_bar()
    
    def _create_header(self):
        """Create header with back button and title"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=(5, 10), sticky="ew", padx=15)
        header_frame.columnconfigure(1, weight=1)
        
        # Back Button
        self.back_button = ctk.CTkButton(
            header_frame,
            text="← Back",
            command=self._handle_back,
            width=100,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.back_button.grid(row=0, column=0, sticky="w")
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="SOQL Query Runner",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.grid(row=0, column=1, sticky="w", padx=(20, 0))
        
        # Show Objects Button (Orange)
        self.show_objects_btn = ctk.CTkButton(
            header_frame,
            text="📋 Show Objects",
            command=self._show_objects_popup,
            width=140,
            height=35,
            fg_color="#ff6b35",
            hover_color="#e55a2b",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.show_objects_btn.grid(row=0, column=2, sticky="e")
    
    def _create_query_input(self):
        """Create query input section"""
        query_frame = ctk.CTkFrame(self)
        query_frame.grid(row=1, column=0, pady=5, sticky="ew", padx=15)
        query_frame.grid_columnconfigure(0, weight=1)
        
        # Top row: Label and buttons
        top_row = ctk.CTkFrame(query_frame, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top_row.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            top_row,
            text="Enter SOQL Query:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        # Text area for query
        self.query_textbox = ctk.CTkTextbox(
            query_frame,
            height=180,
            font=("Consolas", 12),
            wrap="word"
        )
        self.query_textbox.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Action buttons row
        buttons_frame = ctk.CTkFrame(query_frame, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Execute Query Button
        self.run_query_btn = ctk.CTkButton(
            buttons_frame,
            text="▶ Execute Query",
            command=self._run_query_action,
            height=40,
            fg_color="#1e7e34",
            hover_color="#155724",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.run_query_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        # Clear Button
        self.clear_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Clear",
            command=self._clear_query_action,
            height=40,
            fg_color="#6c757d",
            hover_color="#5a6268",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.clear_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Format Button
        self.format_btn = ctk.CTkButton(
            buttons_frame,
            text="✨ Format",
            command=self._format_query_action,
            height=40,
            fg_color="#6c757d",
            hover_color="#5a6268",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.format_btn.grid(row=0, column=2, padx=5, sticky="ew")
    
    def _create_results_display(self):
        """Create scrollable results table"""
        results_frame = ctk.CTkFrame(self)
        results_frame.grid(row=2, column=0, pady=5, sticky="nsew", padx=15)
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Top row: Label and Export button
        top_row = ctk.CTkFrame(results_frame, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top_row.grid_columnconfigure(0, weight=1)
        
        # Results label (NO API COUNT)
        self.results_label = ctk.CTkLabel(
            top_row,
            text="Query Results (0 records)",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.results_label.grid(row=0, column=0, sticky="w")
        
        # Export buttons container
        export_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        export_frame.grid(row=0, column=1, sticky="e")

        # Export to CSV button
        self.export_csv_btn = ctk.CTkButton(
            export_frame,
            text="📄 Export CSV",
            command=self._export_csv_action,
            height=32,
            width=130,
            fg_color="#ff6b35",
            hover_color="#e55a2b",
            font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled"
        )
        self.export_csv_btn.grid(row=0, column=0, padx=3)

        # Export to Excel button
        self.export_excel_btn = ctk.CTkButton(
            export_frame,
            text="📊 Export Excel",
            command=self._export_excel_action,
            height=32,
            width=130,
            fg_color="#ff6b35",
            hover_color="#e55a2b",
            font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled"
        )
        self.export_excel_btn.grid(row=0, column=1, padx=3)

        # Create Treeview for results
        tree_container = ctk.CTkFrame(results_frame)
        tree_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical")
        hsb = ttk.Scrollbar(tree_container, orient="horizontal")
        
        # Treeview
        self.results_tree = ttk.Treeview(
            tree_container,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="extended"
        )
        
        vsb.config(command=self.results_tree.yview)
        hsb.config(command=self.results_tree.xview)
        
        # Grid layout
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background="#2b2b2b",
                       foreground="white",
                       fieldbackground="#2b2b2b",
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background="#1f538d",
                       foreground="white",
                       borderwidth=1)
        style.map('Treeview', background=[('selected', '#3d6a99')])
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_SUCCESS,
            height=24,
            anchor="w",
            padx=12
        )
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=15, pady=(5, 0))
    
    def _create_progress_bar(self):
        """Create progress bar"""
        self.progress_bar = ctk.CTkProgressBar(self, height=12)
        self.progress_bar.grid(row=4, column=0, sticky="ew", padx=15, pady=(3, 10))
        self.progress_bar.set(0)
    
    def _load_org_objects(self) -> List[str]:
        """
        Load all queryable objects from Salesforce org
        
        Returns:
            List of object API names
        """
        try:
            self._log_status(f"{get_timestamp()} Loading objects from org...")
            objects = self.sf_client.fetch_all_objects()
            self._log_status(f"{get_timestamp()} ✅ Loaded {len(objects)} objects")
            return objects
        except Exception as e:
            self._log_status(f"{get_timestamp()} ⚠️ Failed to load objects: {str(e)}")
            return []
    
    # ==================== Event Handlers ====================
    
    def _handle_back(self):
        """Handle back button click"""
        if self.query_in_progress:
            messagebox.showwarning(
                "Query in Progress",
                "Cannot go back while query is running. Please wait for completion."
            )
            return
        
        self.on_back()
    
    def _clear_query_action(self):
        """Clear the query textbox"""
        self.query_textbox.delete("1.0", "end")
        self._log_status(f"{get_timestamp()} Query cleared")
        self._update_status_bar("Query cleared", COLOR_SUCCESS)
    
    def _format_query_action(self):
        """Format/beautify the SOQL query"""
        query = self.query_textbox.get("1.0", "end-1c").strip()
        
        if not query:
            messagebox.showwarning("No Query", "Please enter a query to format.")
            return
        
        try:
            formatted_query = self._format_soql(query)
            self.query_textbox.delete("1.0", "end")
            self.query_textbox.insert("1.0", formatted_query)
            
            self._log_status(f"{get_timestamp()} Query formatted")
            self._update_status_bar("Query formatted successfully", COLOR_SUCCESS)
        except Exception as e:
            messagebox.showerror("Format Error", f"Failed to format query:\n\n{str(e)}")
    
    def _format_soql(self, query: str) -> str:
        """
        Format SOQL query for better readability
        
        Args:
            query: Raw SOQL query
            
        Returns:
            Formatted SOQL query
        """
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Add newlines before major keywords
        keywords = ['SELECT', 'FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'LIMIT', 'OFFSET']
        
        for keyword in keywords:
            # Case-insensitive replacement
            pattern = re.compile(r'\b' + keyword + r'\b', re.IGNORECASE)
            query = pattern.sub(f'\n{keyword}', query)
        
        # Clean up: remove leading newline if present
        query = query.strip()
        
        # Add proper indentation
        lines = query.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'LIMIT', 'OFFSET')):
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _show_objects_popup(self):
        """Show popup with all objects and search"""
        # Create popup window
        popup = Toplevel(self)
        popup.title("Select Object")
        popup.geometry("500x600")
        popup.transient(self)
        popup.grab_set()
        
        # Center popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (500 // 2)
        y = (popup.winfo_screenheight() // 2) - (600 // 2)
        popup.geometry(f"+{x}+{y}")
        
        # Create frame
        main_frame = ctk.CTkFrame(popup)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            main_frame,
            text="Select an Object",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))
        
        # Search box
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Search objects...",
            textvariable=search_var,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        search_entry.pack(fill="x", pady=(0, 10))
        
        # Listbox for objects
        listbox_frame = ctk.CTkFrame(main_frame)
        listbox_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        scrollbar = ctk.CTkScrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")
        
        objects_listbox = tk.Listbox(
            listbox_frame,
            font=("Segoe UI", 11),
            yscrollcommand=scrollbar.set,
            selectmode="single",
            background="#2b2b2b",
            foreground="white",
            selectbackground="#3d6a99",
            borderwidth=0,
            highlightthickness=0
        )
        objects_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=objects_listbox.yview)
        
        # Populate listbox
        def update_listbox(search_term=""):
            objects_listbox.delete(0, tk.END)
            filtered = [obj for obj in self.all_objects if search_term.lower() in obj.lower()]
            for obj in filtered:
                objects_listbox.insert(tk.END, obj)
        
        update_listbox()
        
        # Search functionality
        def on_search(*args):
            update_listbox(search_var.get())
        
        search_var.trace('w', on_search)
        
        # Select button
        def on_select():
            selection = objects_listbox.curselection()
            if selection:
                selected_object = objects_listbox.get(selection[0])
                # Insert query for selected object
                query = f"SELECT Id FROM {selected_object} LIMIT 10"
                self.query_textbox.delete("1.0", "end")
                self.query_textbox.insert("1.0", query)
                self._log_status(f"{get_timestamp()} Inserted query for {selected_object}")
                popup.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select an object.")
        
        # Double-click to select
        objects_listbox.bind('<Double-Button-1>', lambda e: on_select())
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame,
            text="Select",
            command=on_select,
            fg_color="#1e7e34",
            hover_color="#155724",
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=popup.destroy,
            fg_color="#6c757d",
            hover_color="#5a6268",
            width=120,
            height=35
        ).pack(side="left", padx=5)
    
    def _run_query_action(self):
        """Handle run query action"""
        if self.query_in_progress:
            messagebox.showwarning("Query Running", "A query is already in progress.")
            return
        
        # Get query text
        query = self.query_textbox.get("1.0", "end-1c").strip()
        
        if not query:
            messagebox.showwarning("No Query", "Please enter a SOQL query.")
            return
        
        # Basic validation
        if not query.upper().startswith("SELECT"):
            messagebox.showerror("Invalid Query", "Query must start with SELECT.")
            return
        
        # Disable buttons
        self.query_in_progress = True
        self._disable_ui()
        self.run_query_btn.configure(text="⏸ Running...", state="disabled")
        self._update_status_bar("Executing query...", COLOR_WARNING)
        self.progress_bar.set(0.5)
        
        # Run query in thread
        query_thread = threading.Thread(
            target=self._execute_query,
            args=(query,),
            daemon=True
        )
        query_thread.start()
    
    def _execute_query(self, query: str):
        """Execute query in background thread"""
        try:
            self._log_status(f"{get_timestamp()} Executing SOQL query...")
            self._log_status(f"Query: {query}")
            
            # Call the query runner's execute_query method
            results = self.query_runner.execute_query(query)
            
            # Update UI on main thread
            self.after(0, self._query_complete_success, results)
        
        except Exception as e:
            self.after(0, self._query_complete_error, str(e))
    
    def _query_complete_success(self, results: List[Dict]):
        """Called when query completes successfully"""
        self.query_results = results
        row_count = len(results)
        
        self._log_status(f"{get_timestamp()} ✅ Query successful - {row_count} records returned")
        self._update_status_bar(f"Query successful - {row_count} records returned", COLOR_SUCCESS)
        self.progress_bar.set(1.0)
        
        # Display results in table
        self._display_results(results)
        
        # Enable export button
        self.export_excel_btn.configure(state="normal")
        
        self.query_in_progress = False
        self._enable_ui()
        self.run_query_btn.configure(text="▶ Execute Query", state="normal")
    
    def _query_complete_error(self, error_message: str):
        """Called when query fails"""
        self._log_status(f"{get_timestamp()} ❌ Query error: {error_message}")
        self._update_status_bar(f"Query error: {error_message}", COLOR_DANGER)
        self.progress_bar.set(0)
        
        self.query_in_progress = False
        self._enable_ui()
        self.run_query_btn.configure(text="▶ Execute Query", state="normal")
        
        messagebox.showerror(
            "Query Error",
            f"Query execution failed:\n\n{error_message}"
        )
    
    def _display_results(self, results: List[Dict]):
        """Display query results in treeview"""
        # Clear existing data
        self.results_tree.delete(*self.results_tree.get_children())
        
        if not results:
            self.results_label.configure(text="Query Results (0 records)")
            return
        
        # Get column names from first record
        columns = list(results[0].keys())
        
        # Configure columns
        self.results_tree["columns"] = columns
        self.results_tree["show"] = "headings"
        
        # Setup column headings and widths
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150, minwidth=100, anchor="w")
        
        # Insert data rows
        for record in results:
            values = [str(record.get(col, '')) for col in columns]
            self.results_tree.insert("", "end", values=values)
        
        # Update label (NO API COUNT)
        self.results_label.configure(text=f"Query Results ({len(results)} records)")
        
        self._log_status(f"{get_timestamp()} Displayed {len(results)} rows in table")
    
    def _export_excel_action(self):
        """Export query results to Excel"""
        if not self.query_results:
            messagebox.showwarning("No Data", "No query results to export.")
            return
        
        # Ask for save location
        default_filename = f'SOQL_Export_{format_file_timestamp()}.xlsx'
        output_file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_filename,
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if not output_file_path:
            return
        
        try:
            self._update_status_bar("Exporting to Excel...", COLOR_WARNING)
            
            # Export to Excel
            self.query_runner.export_to_excel(self.query_results, output_file_path)
            
            self._log_status(f"{get_timestamp()} ✅ Exported {len(self.query_results)} records to Excel")
            self._log_status(f"File: {output_file_path}")
            self._update_status_bar("Export successful!", COLOR_SUCCESS)
            
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {len(self.query_results)} records to:\n\n{output_file_path}"
            )
        
        except Exception as e:
            self._log_status(f"{get_timestamp()} ❌ Export error: {str(e)}")
            self._update_status_bar(f"Export failed: {str(e)}", COLOR_DANGER)
            messagebox.showerror("Export Error", f"Failed to export Excel:\n\n{str(e)}")
    
    def _export_csv_action(self):
        """Export query results to CSV"""
        if not self.query_results:
            messagebox.showwarning("No Data", "No query results to export.")
            return
        
        # Ask for save location
        default_filename = f'SOQL_Export_{format_file_timestamp()}.csv'
        output_file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("CSV files", "*.csv")]
        )
        
        if not output_file_path:
            return
        
        try:
            self._update_status_bar("Exporting to CSV...", COLOR_WARNING)
            
            self.query_runner.export_to_csv(self.query_results, output_file_path)
            
            self._log_status(f"{get_timestamp()} ✅ Exported {len(self.query_results)} records to CSV")
            self._log_status(f"File: {output_file_path}")
            self._update_status_bar("Export successful!", COLOR_SUCCESS)
            
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {len(self.query_results)} records to:\n\n{output_file_path}"
            )
        
        except Exception as e:
            self._log_status(f"{get_timestamp()} ❌ Export error: {str(e)}")
            self._update_status_bar(f"Export failed: {str(e)}", COLOR_DANGER)
            messagebox.showerror("Export Error", f"Failed to export CSV:\n\n{str(e)}")


    
    def _disable_ui(self):
        """Disable UI during query execution"""
        self.back_button.configure(state="disabled")
        self.export_excel_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.format_btn.configure(state="disabled")
        self.show_objects_btn.configure(state="disabled")
        self.query_textbox.configure(state="disabled")
        self.export_csv_btn.configure(state="disabled")
    
    def _enable_ui(self):
        """Re-enable UI after query execution"""
        self.back_button.configure(state="normal")
        self.clear_btn.configure(state="normal")
        self.format_btn.configure(state="normal")
        self.show_objects_btn.configure(state="normal")
        self.query_textbox.configure(state="normal")
        self.export_excel_btn.configure(state="normal")
        self.export_csv_btn.configure(state="normal")
    
    def _update_status_bar(self, message: str, color: str = COLOR_SUCCESS):
        """Update status bar with message and color"""
        self.status_bar.configure(text=message, fg_color=color)
        self.update_idletasks()
    
    def _log_status(self, message: str):
        """Log status message"""
        print(message)