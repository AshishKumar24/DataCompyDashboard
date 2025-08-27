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
            widget.destroy()
        
        if df is None:
            ttk.Label(frame, text="No data available").pack(pady=20)
            return
        
        # Create a treeview to show data preview
        columns = list(df.columns)
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=10)
        
        # Set headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, minwidth=50)
        
        # Add data (limited to 50 rows for performance)
        for _, row in df.head(50).iterrows():
            tree.insert('', 'end', values=list(row))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add info label
        info_text = f"Showing first 50 rows of {len(df)} total rows, {len(df.columns)} columns"
        ttk.Label(frame, text=info_text, font=('Arial', 9)).pack(side=tk.BOTTOM, fill=tk.X)
    
    def prepare_csv_comparison(self):
        if self.df1 is None or self.df2 is None:
            messagebox.showerror("Error", "Please load both datasets first")
            return
        
        # Create configuration window
        config_window = tk.Toplevel(self.parent)
        config_window.title("Comparison Configuration")
        config_window.geometry("600x500")
        config_window.grab_set()
        
        # Center the configuration window
        self.welcome_screen.center_window(config_window)
        
        # Find common columns
        common_cols = list(set(self.df1.columns) & set(self.df2.columns))
        
        if not common_cols:
            messagebox.showerror("Error", "No common columns found between datasets")
            config_window.destroy()
            return
        
        ttk.Label(config_window, text="Select Join Columns:", font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        
        # Frame for join columns
        join_frame = ttk.Frame(config_window)
        join_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.join_vars = {}
        for col in common_cols:
            var = tk.BooleanVar()
            self.join_vars[col] = var
            cb = ttk.Checkbutton(join_frame, text=col, variable=var)
            cb.pack(anchor=tk.W)
        
        ttk.Label(config_window, text="Select Columns to Compare:", font=('Arial', 12, 'bold')).pack(pady=(20, 5))
        
        # Frame for compare columns
        compare_frame = ttk.Frame(config_window)
        compare_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Create a canvas with scrollbar for compare columns
        compare_canvas = tk.Canvas(compare_frame, height=200)
        compare_scrollbar = ttk.Scrollbar(compare_frame, orient=tk.VERTICAL, command=compare_canvas.yview)
        compare_scrollable_frame = ttk.Frame(compare_canvas)
        
        compare_scrollable_frame.bind(
            "<Configure>",
            lambda e: compare_canvas.configure(scrollregion=compare_canvas.bbox("all"))
        )
        
        compare_canvas.create_window((0, 0), window=compare_scrollable_frame, anchor="nw")
        compare_canvas.configure(yscrollcommand=compare_scrollbar.set)
        
        compare_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        compare_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.compare_vars = {}
        all_cols = list(set(self.df1.columns) | set(self.df2.columns))
        for col in all_cols:
            var = tk.BooleanVar(value=(col in common_cols))  # Pre-select common columns
            self.compare_vars[col] = var
            cb = ttk.Checkbutton(compare_scrollable_frame, text=col, variable=var)
            cb.pack(anchor=tk.W)
        
        # Comparison options
        options_frame = ttk.Frame(config_window)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(options_frame, text="Comparison Options:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.case_sensitive_var = tk.BooleanVar(value=self.welcome_screen.config.get("case_sensitive", False))
        ttk.Checkbutton(options_frame, text="Case Sensitive", variable=self.case_sensitive_var).pack(anchor=tk.W)
        
        # Tolerance for numeric comparisons
        tol_frame = ttk.Frame(options_frame)
        tol_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(tol_frame, text="Numeric Tolerance:").pack(side=tk.LEFT)
        self.tolerance_var = tk.DoubleVar(value=self.welcome_screen.config.get("tolerance", 0.0))
        tol_spinbox = ttk.Spinbox(tol_frame, from_=0.0, to=1.0, increment=0.01, 
                                 textvariable=self.tolerance_var, width=8)
        tol_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(config_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Compare", command=lambda: self.run_csv_comparison(config_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=config_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def run_csv_comparison(self, config_window):
        # Get selected join columns
        join_cols = [col for col, var in self.join_vars.items() if var.get()]
        
        if not join_cols:
            messagebox.showerror("Error", "Please select at least one join column")
            return
        
        # Get selected compare columns
        compare_cols = [col for col, var in self.compare_vars.items() if var.get()]
        
        if not compare_cols:
            messagebox.showerror("Error", "Please select at least one column to compare")
            return
        
        # Update config
        self.welcome_screen.config["tolerance"] = self.tolerance_var.get()
        self.welcome_screen.config["case_sensitive"] = self.case_sensitive_var.get()
        self.welcome_screen.save_config()
        
        config_window.destroy()
        
        # Show progress
        self.show_progress("Comparing datasets...")
        
        # Run comparison in a separate thread
        threading.Thread(
            target=self.run_comparison_in_thread, 
            args=(join_cols, compare_cols),
            daemon=True
        ).start()
    
    def run_comparison_in_thread(self, join_cols, compare_cols):
        """Run comparison in a separate thread"""
        try:
            compare_result = datacompy.Compare(
                self.df1, 
                self.df2, 
                join_columns=join_cols,
                on_index=False,
                abs_tol=self.tolerance_var.get(),
                rel_tol=0.0,  # Using absolute tolerance only for simplicity
                df1_name='Dataset1', 
                df2_name='Dataset2',
                cast_column_names_lower=not self.case_sensitive_var.get()
            )
            
            # Schedule UI update in main thread
            self.parent.after(0, self.show_comparison_results, compare_result, join_cols, compare_cols)
            
        except Exception as e:
            logging.error(f"Comparison failed: {str(e)}")
            logging.error(traceback.format_exc())
            self.parent.after(0, lambda: messagebox.showerror("Error", 
                f"Comparison failed: {str(e)}\n\nSee log for details."))
        finally:
            self.parent.after(0, self.hide_progress)
    
    def show_comparison_results(self, compare_result, join_cols, compare_cols):
        """Show comparison results in a new window"""
        # Create comparison window
        comparison_window = tk.Toplevel(self.parent)
        comparison_window.title("Data Comparison Results")
        comparison_window.geometry("1200x800")
        self.welcome_screen.center_window(comparison_window)
        
        # Display results
        ComparisonResults(comparison_window, compare_result, self.df1, self.df2, join_cols, compare_cols)
    
    def compare_sql(self):
        # Get queries
        query1 = self.query1_text.get("1.0", tk.END).strip()
        query2 = self.query2_text.get("1.0", tk.END).strip()
        
        if not query1 or not query2:
            messagebox.showerror("Error", "Please enter both SQL queries")
            return
        
        conn_str = self.conn_string.get()
        
        # Update config
        self.welcome_screen.config["connection_string"] = conn_str
        self.welcome_screen.save_config()
        
        # Show progress
        self.show_progress("Executing SQL queries...")
        
        # Execute queries in a separate thread
        threading.Thread(target=self.execute_sql_thread, args=(query1, query2, conn_str), daemon=True).start()
    
    def execute_sql_thread(self, query1, query2, conn_str):
        """Execute SQL queries in a separate thread"""
        try:
            if conn_str.startswith("sqlite:///"):
                # SQLite connection
                db_path = conn_str[10:]  # Remove "sqlite:///" prefix
                conn = sqlite3.connect(db_path)
                
                # Execute queries
                self.df1 = pd.read_sql_query(query1, conn)
                self.df2 = pd.read_sql_query(query2, conn)
                
                conn.close()
                
                # Update UI in main thread
                self.parent.after(0, lambda: self.show_preview(self.df1, self.preview1_frame, "Dataset 1"))
                self.parent.after(0, lambda: self.show_preview(self.df2, self.preview2_frame, "Dataset 2"))
                
                # Prepare for comparison
                self.parent.after(0, self.prepare_csv_comparison)
                
            else:
                # Use SQLAlchemy for other databases
                engine = sa.create_engine(conn_str)
                
                # Execute queries
                self.df1 = pd.read_sql_query(query1, engine)
                self.df2 = pd.read_sql_query(query2, engine)
                
                # Update UI in main thread
                self.parent.after(0, lambda: self.show_preview(self.df1, self.preview1_frame, "Dataset 1"))
                self.parent.after(0, lambda: self.show_preview(self.df2, self.preview2_frame, "Dataset 2"))
                
                # Prepare for comparison
                self.parent.after(0, self.prepare_csv_comparison)
                
        except Exception as e:
            logging.error(f"SQL execution failed: {str(e)}")
            logging.error(traceback.format_exc())
            self.parent.after(0, lambda: messagebox.showerror("Error", 
                f"SQL execution failed: {str(e)}\n\nSee log for details."))
        finally:
            self.parent.after(0, self.hide_progress)

class ComparisonResults:
    def __init__(self, parent, compare_result, df1, df2, join_cols, compare_cols):
        self.parent = parent
        self.compare_result = compare_result
        self.df1 = df1
        self.df2 = df2
        self.join_cols = join_cols
        self.compare_cols = compare_cols
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Summary tab
        self.summary_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.summary_frame, text="Summary")
        
        # Columns tab
        self.columns_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.columns_frame, text="Columns")
        
        # Differences tab
        self.diff_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.diff_frame, text="Differences")
        
        # Sample matches tab
        self.matches_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.matches_frame, text="Sample Matches")
        
        # Data profiling tab
        self.profiling_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.profiling_frame, text="Data Profiling")
        
        # Setup tabs
        self.setup_summary_tab()
        self.setup_columns_tab()
        self.setup_differences_tab()
        self.setup_matches_tab()
        self.setup_profiling_tab()
        
        # Add export button
        export_button = ttk.Button(parent, text="Export Results", command=self.export_results)
        export_button.pack(pady=10)
    
    def setup_summary_tab(self):
        # Create summary text
        summary_text = f"""
DataCompy Comparison Summary
============================

Dataset 1: {len(self.df1)} rows, {len(self.df1.columns)} columns
Dataset 2: {len(self.df2)} rows, {len(self.df2.columns)} columns
Join Columns: {', '.join(self.join_cols)}
Compare Columns: {', '.join(self.compare_cols)}

{self.compare_result.report()}
"""
        
        # Create text widget for summary
        text_widget = scrolledtext.ScrolledText(self.summary_frame, wrap=tk.WORD, font=('Courier', 10))
        text_widget.insert(1.0, summary_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
    
    def setup_columns_tab(self):
        # Create a treeview to show column comparison
        tree = ttk.Treeview(self.columns_frame, columns=('Dataset1', 'Dataset2', 'Match', 'Type1', 'Type2'), show='headings', height=15)
        tree.heading('Dataset1', text='Columns in Dataset1')
        tree.heading('Dataset2', text='Columns in Dataset2')
        tree.heading('Match', text='Match Status')
        tree.heading('Type1', text='Type in Dataset1')
        tree.heading('Type2', text='Type in Dataset2')
        
        # Set column widths
        tree.column('Dataset1', width=150)
        tree.column('Dataset2', width=150)
        tree.column('Match', width=100)
        tree.column('Type1', width=100)
        tree.column('Type2', width=100)
        
        # Add data
        cols1 = set(self.df1.columns)
        cols2 = set(self.df2.columns)
        common_cols = cols1 & cols2
        only_in_1 = cols1 - cols2
        only_in_2 = cols2 - cols1
        
        for col in common_cols:
            type1 = str(self.df1[col].dtype)
            type2 = str(self.df2[col].dtype)
            match_status = "Yes" if type1 == type2 else f"No (Type mismatch)"
            tree.insert('', 'end', values=(col, col, match_status, type1, type2))
        
        for col in only_in_1:
            tree.insert('', 'end', values=(col, '', 'No', str(self.df1[col].dtype), ''))
        
        for col in only_in_2:
            tree.insert('', 'end', values=('', col, 'No', '', str(self.df2[col].dtype)))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.columns_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_differences_tab(self):
        # Get sample differences
        try:
            if hasattr(self.compare_result, 'sample_mismatch') and self.compare_result.sample_mismatch(0.1) is not None:
                diff_df = self.compare_result.sample_mismatch(0.1)
                
                if diff_df is not None and not diff_df.empty:
                    # Create a treeview to show differences
                    columns = list(diff_df.columns)
                    tree = ttk.Treeview(self.diff_frame, columns=columns, show='headings', height=15)
                    
                    # Set headings and column widths
                    for col in columns:
                        tree.heading(col, text=col)
                        tree.column(col, width=100, anchor=tk.W)
                    
                    # Add data
                    for _, row in diff_df.iterrows():
                        tree.insert('', 'end', values=list(row))
                    
                    # Add scrollbar
                    scrollbar = ttk.Scrollbar(self.diff_frame, orient=tk.VERTICAL, command=tree.yview)
                    tree.configure(yscrollcommand=scrollbar.set)
                    
                    # Layout
                    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    
                    # Add info label
                    info_text = f"Showing {len(diff_df)} sample mismatches out of {self.compare_result.intersect_rows - self.compare_result.count_matching_rows()} total mismatches"
                    ttk.Label(self.diff_frame, text=info_text, font=('Arial', 9)).pack(side=tk.BOTTOM, fill=tk.X)
                else:
                    ttk.Label(self.diff_frame, text="No differences found").pack(pady=20)
            else:
                ttk.Label(self.diff_frame, text="No differences found or sample not available").pack(pady=20)
        except Exception as e:
            ttk.Label(self.diff_frame, text=f"Error displaying differences: {str(e)}").pack(pady=20)
    
    def setup_matches_tab(self):
        # Get sample matches
        try:
            if hasattr(self.compare_result, 'sample_match') and self.compare_result.sample_match(0.1) is not None:
                match_df = self.compare_result.sample_match(0.1)
                
                if match_df is not None and not match_df.empty:
                    # Create a treeview to show matches
                    columns = list(match_df.columns)
                    tree = ttk.Treeview(self.matches_frame, columns=columns, show='headings', height=15)
                    
                    # Set headings and column widths
                    for col in columns:
                        tree.heading(col, text=col)
                        tree.column(col, width=100, anchor=tk.W)
                    
                    # Add data
                    for _, row in match_df.iterrows():
                        tree.insert('', 'end', values=list(row))
                    
                    # Add scrollbar
                    scrollbar = ttk.Scrollbar(self.matches_frame, orient=tk.VERTICAL, command=tree.yview)
                    tree.configure(yscrollcommand=scrollbar.set)
                    
                    # Layout
                    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    
                    # Add info label
                    info_text = f"Showing {len(match_df)} sample matches out of {self.compare_result.count_matching_rows()} total matches"
                    ttk.Label(self.matches_frame, text=info_text, font=('Arial', 9)).pack(side=tk.BOTTOM, fill=tk.X)
                else:
                    ttk.Label(self.matches_frame, text="No matches found").pack(pady=20)
            else:
                ttk.Label(self.matches_frame, text="No matches found or sample not available").pack(pady=20)
        except Exception as e:
            ttk.Label(self.matches_frame, text=f"Error displaying matches: {str(e)}").pack(pady=20)
    
    def setup_profiling_tab(self):
        """Setup data profiling tab with statistics for each dataset"""
        try:
            # Create a notebook for dataset profiling
            profiling_notebook = ttk.Notebook(self.profiling_frame)
            profiling_notebook.pack(fill=tk.BOTH, expand=True)
            
            # Dataset 1 profiling
            df1_frame = ttk.Frame(profiling_notebook)
            profiling_notebook.add(df1_frame, text="Dataset 1 Profiling")
            
            # Dataset 2 profiling
            df2_frame = ttk.Frame(profiling_notebook)
            profiling_notebook.add(df2_frame, text="Dataset 2 Profiling")
            
            # Profile both datasets
            self.profile_dataset(self.df1, df1_frame, "Dataset 1")
            self.profile_dataset(self.df2, df2_frame, "Dataset 2")
            
        except Exception as e:
            ttk.Label(self.profiling_frame, text=f"Error creating data profiles: {str(e)}").pack(pady=20)
    
    def profile_dataset(self, df, frame, title):
        """Create a data profile for a dataset"""
        try:
            # Calculate basic statistics
            profile_data = []
            
            for col in df.columns:
                col_type = str(df[col].dtype)
                non_null_count = df[col].count()
                null_count = len(df) - non_null_count
                null_percentage = (null_count / len(df)) * 100 if len(df) > 0 else 0
                unique_count = df[col].nunique()
                
                # Add to profile data
                profile_data.append([
                    col, col_type, non_null_count, null_count, 
                    f"{null_percentage:.2f}%", unique_count
                ])
            
            # Create treeview
            columns = ['Column', 'Type', 'Non-Null', 'Null', 'Null %', 'Unique']
            tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
            
            # Set headings
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor=tk.W)
            
            # Add data
            for row in profile_data:
                tree.insert('', 'end', values=row)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Layout
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Add summary
            summary_text = f"{title}: {len(df)} rows, {len(df.columns)} columns"
            ttk.Label(frame, text=summary_text, font=('Arial', 10, 'bold')).pack(side=tk.BOTTOM, fill=tk.X)
            
        except Exception as e:
            ttk.Label(frame, text=f"Error profiling {title}: {str(e)}").pack(pady=20)
    
    def export_results(self):
        """Export comparison results to a file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.xlsx'):
                # Export to Excel with multiple sheets
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # Summary sheet
                    summary_data = {
                        'Metric': ['Dataset 1 Rows', 'Dataset 1 Columns', 'Dataset 2 Rows', 'Dataset 2 Columns',
                                  'Join Columns', 'Compare Columns', 'Matching Rows', 'Mismatched Rows',
                                  'Rows only in Dataset 1', 'Rows only in Dataset 2'],
                        'Value': [len(self.df1), len(self.df1.columns), len(self.df2), len(self.df2.columns),
                                 ', '.join(self.join_cols), ', '.join(self.compare_cols),
                                 self.compare_result.count_matching_rows(),
                                 self.compare_result.intersect_rows - self.compare_result.count_matching_rows(),
                                 self.compare_result.df1_unq_rows, self.compare_result.df2_unq_rows]
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Differences sheet
                    diff_df = self.compare_result.sample_mismatch(1.0)  # Get all mismatches
                    if diff_df is not None and not diff_df.empty:
                        diff_df.to_excel(writer, sheet_name='Differences', index=False)
                    
                    # Profile sheets
                    self.export_profile_to_excel(self.df1, writer, 'Dataset1_Profile')
                    self.export_profile_to_excel(self.df2, writer, 'Dataset2_Profile')
                
                messagebox.showinfo("Success", f"Exported results to {file_path}")
                
            elif file_path.endswith('.csv'):
                # Export differences to CSV
                diff_df = self.compare_result.sample_mismatch(1.0)  # Get all mismatches
                if diff_df is not None and not diff_df.empty:
                    diff_df.to_csv(file_path, index=False)
                    messagebox.showinfo("Success", f"Exported {len(diff_df)} differences to {file_path}")
                else:
                    messagebox.showinfo("Info", "No differences to export")
            else:
                # Export full report to text file
                with open(file_path, 'w') as f:
                    f.write("Data Comparison Tool - Results Report\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write(f"Dataset 1: {len(self.df1)} rows, {len(self.df1.columns)} columns\n")
                    f.write(f"Dataset 2: {len(self.df2)} rows, {len(self.df2.columns)} columns\n")
                    f.write(f"Join Columns: {', '.join(self.join_cols)}\n")
                    f.write(f"Compare Columns: {', '.join(self.compare_cols)}\n\n")
                    
                    f.write(self.compare_result.report())
                
                messagebox.showinfo("Success", f"Exported full report to {file_path}")
                
        except Exception as e:
            logging.error(f"Failed to export results: {str(e)}")
            logging.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to export results: {str(e)}\n\nSee log for details.")
    
    def export_profile_to_excel(self, df, writer, sheet_name):
        """Export data profile to Excel"""
        profile_data = []
        
        for col in df.columns:
            col_type = str(df[col].dtype)
            non_null_count = df[col].count()
            null_count = len(df) - non_null_count
            null_percentage = (null_count / len(df)) * 100 if len(df) > 0 else 0
            unique_count = df[col].nunique()
            
            # Add to profile data
            profile_data.append({
                'Column': col,
                'Type': col_type,
                'Non-Null': non_null_count,
                'Null': null_count,
                'Null %': f"{null_percentage:.2f}%",
                'Unique': unique_count
            })
        
        pd.DataFrame(profile_data).to_excel(writer, sheet_name=sheet_name, index=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = WelcomeScreen(root)
    root.mainloop()
