"""
SME - SOQL Query Runner Screen UI
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, List, Dict
import threading
from config.constants import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, BUTTON_EXPORT, 
    BUTTON_EXPORT_HOVER
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
        
        # Configure grid
        self.grid_rowconfigure(3, weight=1)  # Results section gets extra space
        self.grid_columnconfigure(0, weight=1)
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup SOQL Query UI components"""
        # Header
        self._create_header()
        
        # Query Input Section
        self._create_query_input()
        
        # Action Buttons
        self._create_action_buttons()
        
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
    
    def _create_query_input(self):
        """Create query input text area"""
        query_frame = ctk.CTkFrame(self)
        query_frame.grid(row=1, column=0, pady=5, sticky="ew", padx=15)
        query_frame.grid_columnconfigure(0, weight=1)
        
        # Label
        ctk.CTkLabel(
            query_frame,
            text="Enter SOQL Query:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Text area for query
        self.query_textbox = ctk.CTkTextbox(
            query_frame,
            height=100,
            font=("Consolas", 12),
            wrap="word"
        )
        self.query_textbox.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Placeholder
        placeholder = "Enter your SOQL query here...\n\nExamples:\n  SELECT Id, Name FROM Account LIMIT 10\n  SELECT Id, Account.Name, Amount FROM Opportunity WHERE Amount > 10000"
        self.query_textbox.insert("1.0", placeholder)
        self.query_textbox.bind("<FocusIn>", self._clear_placeholder)
        self.placeholder_active = True
    
    def _clear_placeholder(self, event):
        """Clear placeholder text on focus"""
        if self.placeholder_active:
            self.query_textbox.delete("1.0", "end")
            self.placeholder_active = False
    
    def _create_action_buttons(self):
        """Create action buttons row"""
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.grid(row=2, column=0, pady=5, sticky="ew", padx=15)
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Run Query Button
        self.run_query_btn = ctk.CTkButton(
            buttons_frame,
            text="▶ Run Query",
            command=self._run_query_action,
            height=40,
            fg_color=BUTTON_EXPORT,
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.run_query_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        # Export CSV Button
        self.export_csv_btn = ctk.CTkButton(
            buttons_frame,
            text="📄 Export to CSV",
            command=self._export_csv_action,
            height=40,
            fg_color=BUTTON_EXPORT,
            hover_color=BUTTON_EXPORT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled"
        )
        self.export_csv_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Clear Results Button
        self.clear_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Clear Results",
            command=self._clear_results_action,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled"
        )
        self.clear_btn.grid(row=0, column=2, padx=5, sticky="ew")
    
    def _create_results_display(self):
        """Create scrollable results table"""
        results_frame = ctk.CTkFrame(self)
        results_frame.grid(row=3, column=0, pady=5, sticky="nsew", padx=15)
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Label with row count
        self.results_label = ctk.CTkLabel(
            results_frame,
            text="Query Results (0 rows)",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.results_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
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
            text="Status: Ready to execute query",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_SUCCESS,
            height=24,
            anchor="w",
            padx=12
        )
        self.status_bar.grid(row=4, column=0, sticky="ew", padx=15, pady=(5, 0))
    
    def _create_progress_bar(self):
        """Create progress bar"""
        self.progress_bar = ctk.CTkProgressBar(self, height=12)
        self.progress_bar.grid(row=5, column=0, sticky="ew", padx=15, pady=(3, 10))
        self.progress_bar.set(0)
    
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
    
    def _run_query_action(self):
        """Handle run query action"""
        if self.query_in_progress:
            messagebox.showwarning("Query Running", "A query is already in progress.")
            return
        
        # Get query text
        query = self.query_textbox.get("1.0", "end-1c").strip()
        
        if not query or self.placeholder_active:
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
            
            results = self.query_runner.execute_query(query)
            
            self.after(0, self._query_complete_success, results)
        
        except Exception as e:
            self.after(0, self._query_complete_error, str(e))
    
    def _query_complete_success(self, results: List[Dict]):
        """Called when query completes successfully"""
        self.query_results = results
        row_count = len(results)
        
        self._log_status(f"{get_timestamp()} ✅ Query successful - {row_count} rows returned")
        self._update_status_bar(f"Query successful - {row_count} rows returned", COLOR_SUCCESS)
        self.progress_bar.set(1.0)
        
        # Display results in table
        self._display_results(results)
        
        # Enable export button
        self.export_csv_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")
        
        self.query_in_progress = False
        self._enable_ui()
        self.run_query_btn.configure(text="▶ Run Query", state="normal")
        
        messagebox.showinfo(
            "Query Complete",
            f"Query executed successfully!\n\nRows returned: {row_count}"
        )
    
    def _query_complete_error(self, error_message: str):
        """Called when query fails"""
        self._log_status(f"{get_timestamp()} ❌ Query error: {error_message}")
        self._update_status_bar(f"Query error: {error_message}", COLOR_DANGER)
        self.progress_bar.set(0)
        
        self.query_in_progress = False
        self._enable_ui()
        self.run_query_btn.configure(text="▶ Run Query", state="normal")
        
        messagebox.showerror(
            "Query Error",
            f"Query execution failed:\n\n{error_message}"
        )
    
    def _display_results(self, results: List[Dict]):
        """Display query results in treeview"""
        # Clear existing data
        self.results_tree.delete(*self.results_tree.get_children())
        
        if not results:
            self.results_label.configure(text="Query Results (0 rows)")
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
        
        # Update label
        self.results_label.configure(text=f"Query Results ({len(results)} rows)")
        
        self._log_status(f"{get_timestamp()} Displayed {len(results)} rows in table")
    
    def _export_csv_action(self):
        """Handle export to CSV action"""
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
            
            self._log_status(f"{get_timestamp()} ✅ Exported {len(self.query_results)} rows to CSV")
            self._log_status(f"File: {output_file_path}")
            self._update_status_bar("Export successful!", COLOR_SUCCESS)
            
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {len(self.query_results)} rows to:\n\n{output_file_path}"
            )
        
        except Exception as e:
            self._log_status(f"{get_timestamp()} ❌ Export error: {str(e)}")
            self._update_status_bar(f"Export failed: {str(e)}", COLOR_DANGER)
            messagebox.showerror("Export Error", f"Failed to export CSV:\n\n{str(e)}")
    
    def _clear_results_action(self):
        """Clear results table"""
        confirm = messagebox.askyesno(
            "Clear Results",
            "Clear all query results?"
        )
        
        if confirm:
            self.query_results = []
            self.results_tree.delete(*self.results_tree.get_children())
            self.results_label.configure(text="Query Results (0 rows)")
            self.export_csv_btn.configure(state="disabled")
            self.clear_btn.configure(state="disabled")
            self._update_status_bar("Results cleared", COLOR_SUCCESS)
            self._log_status(f"{get_timestamp()} Results cleared")
    
    def _disable_ui(self):
        """Disable UI during query execution"""
        self.back_button.configure(state="disabled")
        self.export_csv_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.query_textbox.configure(state="disabled")
    
    def _enable_ui(self):
        """Re-enable UI after query execution"""
        self.back_button.configure(state="normal")
        self.query_textbox.configure(state="normal")
    
    def _update_status_bar(self, message: str, color: str = COLOR_SUCCESS):
        """Update status bar with message and color"""
        self.status_bar.configure(text=f"Status: {message}", fg_color=color)
        self.update_idletasks()
    
    def _log_status(self, message: str):
        """Log status message"""
        print(message)