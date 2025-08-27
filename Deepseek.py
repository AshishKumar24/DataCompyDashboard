Data Comparison Tool - Enhanced Version

I'll implement a comprehensive data comparison tool with all the improvements suggested in the review. Here's the complete, enhanced solution:

```python
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import pandas as pd
import datacompy
import sqlite3
from io import StringIO
import traceback
import threading
import json
import os
import logging
import gc
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(
    filename=f'data_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class WelcomeScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Comparison Tool")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        self.root.configure(bg="#f8f9fa")
        
        # Load configuration
        self.config = self.load_config()
        
        # Center the window on screen
        self.center_window()
        
        # Configure root grid for responsiveness
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Set style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f8f9fa')
        self.style.configure('TLabel', background='#f8f9fa', font=('Arial', 10))
        self.style.configure('Title.TLabel', background='#f8f9fa', font=('Arial', 24, 'bold'), foreground='#007bff')
        self.style.configure('Subtitle.TLabel', background='#f8f9fa', font=('Arial', 14), foreground='#6c757d')
        self.style.configure('Section.TLabel', background='#f8f9fa', font=('Arial', 20, 'bold'), foreground='#343a40')
        self.style.configure('Card.TFrame', background='white', relief=tk.RAISED, borderwidth=1)
        self.style.configure('CardTitle.TLabel', background='white', font=('Arial', 16, 'bold'))
        self.style.configure('CardText.TLabel', background='white', font=('Arial', 12), foreground='#6c757d')
        self.style.configure('Feature.TLabel', background='white', font=('Arial', 11))
        self.style.configure('StepTitle.TLabel', background='#f8f9fa', font=('Arial', 14, 'bold'))
        self.style.configure('StepText.TLabel', background='#f8f9fa', font=('Arial', 11), foreground='#6c757d')
        self.style.configure('TechTitle.TLabel', background='white', font=('Arial', 16, 'bold'))
        self.style.configure('TechText.TLabel', background='white', font=('Arial', 12), foreground='#6c757d')
        
        # Configure button styles
        self.style.configure('Primary.TButton', background='#007bff', foreground='white', font=('Arial', 14, 'bold'))
        self.style.map('Primary.TButton', background=[('active', '#0056b3')])
        
        self.setup_ui()
        
    def load_config(self):
        """Load configuration from file"""
        config_file = "data_comparison_config.json"
        default_config = {
            "last_directory": os.getcwd(),
            "connection_string": "sqlite:///sample.db",
            "tolerance": 0.0,
            "case_sensitive": False,
            "chunk_size": 10000
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                return default_config
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        config_file = "data_comparison_config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {str(e)}")
        
    def center_window(self, window=None):
        """Center a window on the screen"""
        window = window or self.root
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
    def setup_ui(self):
        # Main container with scrollbar
        main_container = ttk.Frame(self.root)
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_container, bg='#f8f9fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure main_container grid
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Bind mouse wheel to scroll
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", 
                    lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        # Hero Section
        hero_frame = ttk.Frame(self.scrollable_frame)
        hero_frame.pack(fill=tk.X, padx=20, pady=40)
        
        title_label = ttk.Label(hero_frame, text="Data Comparison Tool", style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        subtitle_text = "Compare datasets with precision and ease. Upload CSV files or execute SQL queries to perform comprehensive data analysis with detailed metrics and insights."
        subtitle_label = ttk.Label(hero_frame, text=subtitle_text, style='Subtitle.TLabel', wraplength=700, justify=tk.CENTER)
        subtitle_label.pack(pady=(0, 30))
        
        get_started_btn = ttk.Button(hero_frame, text="Get Started", style='Primary.TButton', 
                                   command=self.open_data_input)
        get_started_btn.pack(pady=10, ipadx=20, ipady=10)
        
        # Features Section
        features_frame = ttk.Frame(self.scrollable_frame)
        features_frame.pack(fill=tk.X, padx=20, pady=40)
        
        # Create three columns for features
        features_container = ttk.Frame(features_frame)
        features_container.pack(fill=tk.X, padx=0, pady=10)
        
        # Configure features container for responsive layout
        features_container.grid_columnconfigure(0, weight=1, uniform="features")
        features_container.grid_columnconfigure(1, weight=1, uniform="features")
        features_container.grid_columnconfigure(2, weight=1, uniform="features")
        
        # CSV Files Feature
        feature1_frame = ttk.Frame(features_container, style='Card.TFrame')
        feature1_frame.grid(row=0, column=0, sticky="nsew", padx=10)
        feature1_frame.configure(padding=20)
        
        icon1 = tk.Label(feature1_frame, text="📊", font=('Arial', 30), background='white')
        icon1.pack(pady=(0, 15))
        
        ttk.Label(feature1_frame, text="CSV Files", style='CardTitle.TLabel').pack(pady=(0, 10))
        feature1_desc = "Upload and compare CSV files with automatic delimiter detection and encoding support. Handle large datasets efficiently."
        ttk.Label(feature1_frame, text=feature1_desc, style='CardText.TLabel', wraplength=250, justify=tk.CENTER).pack(pady=(0, 15))
        
        benefits1 = [
            "Auto-detect delimiter",
            "Encoding detection",
            "Data validation"
        ]
        
        for benefit in benefits1:
            benefit_frame = ttk.Frame(feature1_frame)
            benefit_frame.pack(fill=tk.X, pady=5)
            ttk.Label(benefit_frame, text="✓", foreground="#28a745", font=('Arial', 12, 'bold'), background='white').pack(side=tk.LEFT)
            ttk.Label(benefit_frame, text=benefit, style='Feature.TLabel').pack(side=tk.LEFT, padx=5)
        
        # SQL Queries Feature
        feature2_frame = ttk.Frame(features_container, style='Card.TFrame')
        feature2_frame.grid(row=0, column=1, sticky="nsew", padx=10)
        feature2_frame.configure(padding=20)
        
        icon2 = tk.Label(feature2_frame, text="🔍", font=('Arial', 30), background='white')
        icon2.pack(pady=(0, 15))
        
        ttk.Label(feature2_frame, text="SQL Queries", style='CardTitle.TLabel').pack(pady=(0, 10))
        feature2_desc = "Execute SQL queries directly against your database connections. Compare query results in real-time."
        ttk.Label(feature2_frame, text=feature2_desc, style='CardText.TLabel', wraplength=250, justify=tk.CENTER).pack(pady=(0, 15))
        
        benefits2 = [
            "Direct SQL execution",
            "Query validation",
            "Real-time results"
        ]
        
        for benefit in benefits2:
            benefit_frame = ttk.Frame(feature2_frame)
            benefit_frame.pack(fill=tk.X, pady=5)
            ttk.Label(benefit_frame, text="✓", foreground="#28a745", font=('Arial', 12, 'bold'), background='white').pack(side=tk.LEFT)
            ttk.Label(benefit_frame, text=benefit, style='Feature.TLabel').pack(side=tk.LEFT, padx=5)
        
        # Advanced Analytics Feature
        feature3_frame = ttk.Frame(features_container, style='Card.TFrame')
        feature3_frame.grid(row=0, column=2, sticky="nsew", padx=10)
        feature3_frame.configure(padding=20)
        
        icon3 = tk.Label(feature3_frame, text="🚀", font=('Arial', 30), background='white')
        icon3.pack(pady=(0, 15))
        
        ttk.Label(feature3_frame, text="Advanced Analytics", style='CardTitle.TLabel').pack(pady=(0, 10))
        feature3_desc = "Get detailed insights with comprehensive metrics, mismatch analysis, and interactive dashboards."
        ttk.Label(feature3_frame, text=feature3_desc, style='CardText.TLabel', wraplength=250, justify=tk.CENTER).pack(pady=(0, 15))
        
        benefits3 = [
            "Detailed metrics",
            "Advanced analysis",
            "Export results"
        ]
        
        for benefit in benefits3:
            benefit_frame = ttk.Frame(feature3_frame)
            benefit_frame.pack(fill=tk.X, pady=5)
            ttk.Label(benefit_frame, text="✓", foreground="#28a745", font=('Arial', 12, 'bold'), background='white').pack(side=tk.LEFT)
            ttk.Label(benefit_frame, text=benefit, style='Feature.TLabel').pack(side=tk.LEFT, padx=5)
        
        # How It Works Section
        how_it_works_frame = ttk.Frame(self.scrollable_frame)
        how_it_works_frame.pack(fill=tk.X, padx=20, pady=40)
        
        section_label = ttk.Label(how_it_works_frame, text="How It Works", style='Section.TLabel')
        section_label.pack(pady=(0, 30))
        
        steps_container = ttk.Frame(how_it_works_frame)
        steps_container.pack(fill=tk.X, padx=0, pady=10)
        
        # Configure steps container for responsive layout
        for i in range(4):
            steps_container.grid_columnconfigure(i, weight=1, uniform="steps")
        
        steps = [
            ("Load Data", "Upload CSV files or enter SQL queries to load your datasets"),
            ("Configure", "Select join columns and specify which columns to compare"),
            ("Compare", "Run the comparison and get detailed analysis results"),
            ("Analyze", "View metrics, explore mismatches, and report results")
        ]
        
        for i, (step_title, step_desc) in enumerate(steps):
            step_frame = ttk.Frame(steps_container)
            step_frame.grid(row=0, column=i, sticky="nsew", padx=10)
            
            # Step circle with number
            step_circle = tk.Canvas(step_frame, width=50, height=50, highlightthickness=0, bg='#f8f9fa')
            step_circle.pack(pady=(0, 15))
            step_circle.create_oval(5, 5, 45, 45, fill='#007bff', outline='')
            step_circle.create_text(25, 25, text=str(i+1), fill='white', font=('Arial', 16, 'bold'))
            
            # Step content
            ttk.Label(step_frame, text=step_title, style='StepTitle.TLabel').pack(pady=(0, 5))
            ttk.Label(step_frame, text=step_desc, style='StepText.TLabel', wraplength=200, justify=tk.CENTER).pack()
        
        # Tech Stack Section
        tech_frame = ttk.Frame(self.scrollable_frame, style='Card.TFrame')
        tech_frame.pack(fill=tk.X, padx=20, pady=40)
        tech_frame.configure(padding=30)
        
        ttk.Label(tech_frame, text="Built with Modern Technology", style='TechTitle.TLabel').pack(pady=(0, 30))
        
        tech_container = ttk.Frame(tech_frame)
        tech_container.pack(fill=tk.X, padx=0, pady=10)
        
        # Configure tech container for responsive layout
        for i in range(4):
            tech_container.grid_columnconfigure(i, weight=1, uniform="tech")
        
        tech_items = [
            ("🐍", "Python", "Primary language"),
            ("🗃️", "Database", "Data storage"),
            ("⚙️", "Framework", "Application framework"),
            ("📈", "Analytics", "Data visualization")
        ]
        
        for i, (icon, title, desc) in enumerate(tech_items):
            tech_item_frame = ttk.Frame(tech_container)
            tech_item_frame.grid(row=0, column=i, sticky="nsew", padx=10)
            
            ttk.Label(tech_item_frame, text=icon, font=('Arial', 24), background='white').pack(pady=(0, 10))
            ttk.Label(tech_item_frame, text=title, style='CardTitle.TLabel').pack(pady=(0, 5))
            ttk.Label(tech_item_frame, text=desc, style='CardText.TLabel').pack()
        
        # Footer
        footer_frame = ttk.Frame(self.scrollable_frame)
        footer_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(footer_frame, text="Powered by Modern Technology", 
                 font=('Arial', 10), foreground='#6c757d').pack()
        
        # Bind resize event to update UI elements
        self.root.bind('<Configure>', self.on_window_resize)
    
    def on_window_resize(self, event):
        # Update text wrapping based on window size
        if event.widget == self.root:
            # Update hero section text wrapping
            for child in self.scrollable_frame.winfo_children():
                if isinstance(child, ttk.Frame) and len(child.winfo_children()) > 0:
                    for widget in child.winfo_children():
                        if isinstance(widget, ttk.Label) and "Subtitle.TLabel" in widget.cget("style"):
                            widget.configure(wraplength=min(700, self.root.winfo_width() - 100))
                        elif isinstance(widget, ttk.Label) and "CardText.TLabel" in widget.cget("style"):
                            widget.configure(wraplength=min(250, self.root.winfo_width() // 4 - 50))
                        elif isinstance(widget, ttk.Label) and "StepText.TLabel" in widget.cget("style"):
                            widget.configure(wraplength=min(200, self.root.winfo_width() // 4 - 50))
    
    def open_data_input(self):
        """Open the data input window when Get Started is clicked"""
        # Create a new window for data input
        data_window = tk.Toplevel(self.root)
        data_window.title("Data Input - Data Comparison Tool")
        data_window.geometry("900x700")
        data_window.configure(bg="#f8f9fa")
        data_window.minsize(800, 600)
        
        # Center the new window
        self.center_window(data_window)
        data_window.transient(self.root)
        data_window.grab_set()
        
        # Create the data input interface
        DataInputWindow(data_window, self)
        
        # Make sure to handle window close properly
        data_window.protocol("WM_DELETE_WINDOW", lambda: self.on_data_window_close(data_window))

    def on_data_window_close(self, data_window):
        """Handle closing of the data input window"""
        data_window.destroy()
        self.root.deiconify()  # Show the main window again

class DataInputWindow:
    def __init__(self, parent, welcome_screen):
        self.parent = parent
        self.welcome_screen = welcome_screen
        self.df1 = None
        self.df2 = None
        self.selected_join_cols = []
        self.selected_compare_cols = []
        self.progress_window = None
        
        # Configure parent grid
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # CSV Upload Tab
        self.csv_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.csv_frame, text="CSV Upload")
        
        # SQL Query Tab
        self.sql_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.sql_frame, text="SQL Query")
        
        # Setup CSV tab
        self.setup_csv_tab()
        
        # Setup SQL tab
        self.setup_sql_tab()
        
        # Back button
        back_button = ttk.Button(parent, text="Back to Welcome", 
                                command=self.go_back_to_welcome)
        back_button.pack(pady=10)
    
    def setup_csv_tab(self):
        # Configure CSV frame
        self.csv_frame.grid_rowconfigure(1, weight=1)
        self.csv_frame.grid_columnconfigure(0, weight=1)
        self.csv_frame.grid_columnconfigure(1, weight=1)
        
        # Dataset 1
        ttk.Label(self.csv_frame, text="Dataset 1:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        file1_frame = ttk.Frame(self.csv_frame)
        file1_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        self.file1_entry = ttk.Entry(file1_frame, font=('Arial', 10))
        self.file1_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(file1_frame, text="Browse", command=self.load_file1).pack(side=tk.RIGHT)
        
        # Dataset 2
        ttk.Label(self.csv_frame, text="Dataset 2:", font=('Arial', 12, 'bold')).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        file2_frame = ttk.Frame(self.csv_frame)
        file2_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        
        self.file2_entry = ttk.Entry(file2_frame, font=('Arial', 10))
        self.file2_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(file2_frame, text="Browse", command=self.load_file2).pack(side=tk.RIGHT)
        
        # Compare button
        compare_frame = ttk.Frame(self.csv_frame)
        compare_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(compare_frame, text="Compare Datasets", command=self.prepare_csv_comparison, style='Primary.TButton').pack()
        
        # Preview area
        ttk.Label(self.csv_frame, text="Data Preview:", font=('Arial', 12, 'bold')).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        preview_frame = ttk.Frame(self.csv_frame)
        preview_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        
        # Create a notebook for preview tabs
        self.preview_notebook = ttk.Notebook(preview_frame)
        self.preview_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Dataset 1 preview
        self.preview1_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.preview1_frame, text="Dataset 1 Preview")
        
        # Dataset 2 preview
        self.preview2_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.preview2_frame, text="Dataset 2 Preview")
        
        # Configure rows and columns for expansion
        self.csv_frame.grid_rowconfigure(4, weight=1)
    
    def setup_sql_tab(self):
        # Configure SQL frame
        self.sql_frame.grid_rowconfigure(1, weight=1)
        self.sql_frame.grid_columnconfigure(0, weight=1)
        self.sql_frame.grid_columnconfigure(1, weight=1)
        
        # Query 1
        ttk.Label(self.sql_frame, text="SQL Query 1:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        self.query1_text = scrolledtext.ScrolledText(self.sql_frame, height=10, font=('Consolas', 10))
        self.query1_text.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.query1_text.insert('1.0', "SELECT * FROM table1;")
        
        # Query 2
        ttk.Label(self.sql_frame, text="SQL Query 2:", font=('Arial', 12, 'bold')).grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        self.query2_text = scrolledtext.ScrolledText(self.sql_frame, height=10, font=('Consolas', 10))
        self.query2_text.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        self.query2_text.insert('1.0', "SELECT * FROM table2;")
        
        # Connection info
        conn_frame = ttk.Frame(self.sql_frame)
        conn_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        ttk.Label(conn_frame, text="Database Connection:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.conn_string = ttk.Entry(conn_frame, font=('Arial', 10))
        self.conn_string.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.conn_string.insert(0, self.welcome_screen.config.get("connection_string", "sqlite:///sample.db"))
        
        # Test connection button
        ttk.Button(conn_frame, text="Test Connection", command=self.test_connection).pack(side=tk.RIGHT)
        
        # Compare button
        compare_frame = ttk.Frame(self.sql_frame)
        compare_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(compare_frame, text="Execute and Compare", command=self.compare_sql, style='Primary.TButton').pack()
        
        # Configure rows for expansion
        self.sql_frame.grid_rowconfigure(1, weight=1)
    
    def test_connection(self):
        """Test the database connection"""
        conn_str = self.conn_string.get()
        try:
            if conn_str.startswith("sqlite:///"):
                # SQLite connection
                db_path = conn_str[10:]  # Remove "sqlite:///" prefix
                conn = sqlite3.connect(db_path)
                conn.close()
                messagebox.showinfo("Success", "SQLite connection successful!")
            else:
                # Test connection using SQLAlchemy for other databases
                engine = sa.create_engine(conn_str)
                with engine.connect() as conn:
                    conn.execute(sa.text("SELECT 1"))
                messagebox.showinfo("Success", "Database connection successful!")
        except SQLAlchemyError as e:
            messagebox.showerror("Connection Failed", f"Failed to connect to database: {str(e)}")
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Failed to connect to database: {str(e)}")
    
    def go_back_to_welcome(self):
        """Return to the welcome screen"""
        self.cleanup()
        self.parent.destroy()
        self.welcome_screen.root.deiconify()
    
    def cleanup(self):
        """Release memory by clearing dataframes"""
        self.df1 = None
        self.df2 = None
        gc.collect()
    
    def load_large_file(self, filename, chunk_size=None):
        """Load large files in chunks to manage memory"""
        if chunk_size is None:
            chunk_size = self.welcome_screen.config.get("chunk_size", 10000)
            
        try:
            if filename.endswith('.csv'):
                # Read in chunks
                chunks = []
                for chunk in pd.read_csv(filename, chunksize=chunk_size):
                    chunks.append(chunk)
                return pd.concat(chunks, ignore_index=True)
            elif filename.endswith('.xlsx'):
                # For Excel files, read the entire file (could be optimized)
                return pd.read_excel(filename)
            else:
                messagebox.showerror("Error", "Unsupported file format")
                return None
        except Exception as e:
            logging.error(f"Failed to load file {filename}: {str(e)}")
            logging.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to load file: {str(e)}\n\nSee log for details.")
            return None
    
    def load_file1(self):
        initial_dir = self.welcome_screen.config.get("last_directory", os.getcwd())
        filename = filedialog.askopenfilename(
            title="Select First Dataset", 
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        if filename:
            # Update config with last directory
            self.welcome_screen.config["last_directory"] = os.path.dirname(filename)
            self.welcome_screen.save_config()
            
            self.file1_entry.delete(0, tk.END)
            self.file1_entry.insert(0, filename)
            
            # Show progress window
            self.show_progress("Loading Dataset 1...")
            
            # Load file in a separate thread
            threading.Thread(target=self.load_file_thread, args=(filename, 1), daemon=True).start()
    
    def load_file2(self):
        initial_dir = self.welcome_screen.config.get("last_directory", os.getcwd())
        filename = filedialog.askopenfilename(
            title="Select Second Dataset", 
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        if filename:
            # Update config with last directory
            self.welcome_screen.config["last_directory"] = os.path.dirname(filename)
            self.welcome_screen.save_config()
            
            self.file2_entry.delete(0, tk.END)
            self.file2_entry.insert(0, filename)
            
            # Show progress window
            self.show_progress("Loading Dataset 2...")
            
            # Load file in a separate thread
            threading.Thread(target=self.load_file_thread, args=(filename, 2), daemon=True).start()
    
    def load_file_thread(self, filename, dataset_num):
        """Load file in a separate thread"""
        try:
            if filename.endswith('.csv'):
                df = self.load_large_file(filename)
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filename)
            else:
                self.parent.after(0, lambda: messagebox.showerror("Error", "Unsupported file format"))
                return
            
            if df is not None:
                if dataset_num == 1:
                    self.df1 = df
                    self.parent.after(0, lambda: self.show_preview(self.df1, self.preview1_frame, "Dataset 1"))
                    self.parent.after(0, lambda: messagebox.showinfo("Success", 
                        f"Loaded dataset 1 with {len(self.df1)} rows and {len(self.df1.columns)} columns"))
                else:
                    self.df2 = df
                    self.parent.after(0, lambda: self.show_preview(self.df2, self.preview2_frame, "Dataset 2"))
                    self.parent.after(0, lambda: messagebox.showinfo("Success", 
                        f"Loaded dataset 2 with {len(self.df2)} rows and {len(self.df2.columns)} columns"))
        except Exception as e:
            logging.error(f"Failed to load file {filename}: {str(e)}")
            logging.error(traceback.format_exc())
            self.parent.after(0, lambda: messagebox.showerror("Error", 
                f"Failed to load file: {str(e)}\n\nSee log for details."))
        finally:
            self.parent.after(0, self.hide_progress)
    
    def show_progress(self, message="Processing..."):
        """Show a progress window"""
        if self.progress_window and self.progress_window.winfo_exists():
            self.progress_window.destroy()
            
        self.progress_window = tk.Toplevel(self.parent)
        self.progress_window.title("Please Wait")
        self.progress_window.geometry("300x100")
        self.progress_window.transient(self.parent)
        self.progress_window.grab_set()
        
        # Center the progress window
        self.welcome_screen.center_window(self.progress_window)
        
        ttk.Label(self.progress_window, text=message, font=('Arial', 12)).pack(pady=20)
        
        progress_bar = ttk.Progressbar(self.progress_window, mode='indeterminate')
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        progress_bar.start()
        
        self.progress_window.update()
    
    def hide_progress(self):
        """Hide the progress window"""
        if self.progress_window and self.progress_window.winfo_exists():
            self.progress_window.destroy()
        self.progress_window = None
    
    def show_preview(self, df, frame, title):
        # Clear previous content
        for widget in frame.winfo_children():
            widget.destroy
```
