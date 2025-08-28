import sys
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QPushButton, QLabel, 
                            QTextEdit, QFileDialog, QMessageBox, QTableWidget,
                            QTableWidgetItem, QSplitter, QProgressBar, QComboBox,
                            QGroupBox, QFormLayout, QLineEdit, QCheckBox, 
                            QFrame, QSizePolicy, QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
import sqlite3
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns

# Set modern matplotlib style
plt.style.use('seaborn-v0_8')

class StyledButton(QPushButton):
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.setMinimumHeight(35)
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #007acc;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:disabled {
                    background-color: #f8f8f8;
                    color: #aaaaaa;
                }
            """)

class ModernGroupBox(QGroupBox):
    def __init__(self, title):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #007acc;
            }
        """)

class ModernProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                background-color: #f8f8f8;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 5px;
            }
        """)

class ModernTableWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f8f8f8;
            }
            QTableWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)

class ModernTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 4px;
                background-color: white;
            }
        """)

class ModernLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #007acc;
            }
        """)

class ModernComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 6px;
                background-color: white;
                min-height: 30px;
            }
            QComboBox:focus {
                border: 2px solid #007acc;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #cccccc;
            }
        """)

class DataLoaderThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object, str)
    error = pyqtSignal(str)

    def __init__(self, source_type, source, db_config=None):
        super().__init__()
        self.source_type = source_type
        self.source = source
        self.db_config = db_config

    def run(self):
        try:
            if self.source_type == 'csv':
                self.progress.emit(30)
                df = pd.read_csv(self.source)
                self.progress.emit(100)
                self.finished.emit(df, f"CSV: {self.source}")
                
            elif self.source_type == 'sql':
                self.progress.emit(20)
                engine = create_engine(self.db_config)
                self.progress.emit(50)
                with engine.connect() as conn:
                    df = pd.read_sql(text(self.source), conn)
                self.progress.emit(100)
                self.finished.emit(df, f"SQL Query")
                
        except Exception as e:
            self.error.emit(str(e))

class ComparisonWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, df1, df2, comparison_methods):
        super().__init__()
        self.df1 = df1
        self.df2 = df2
        self.comparison_methods = comparison_methods

    def run(self):
        try:
            results = {}
            total_steps = len(self.comparison_methods)
            
            for i, method in enumerate(self.comparison_methods):
                self.progress.emit(int((i / total_steps) * 100))
                
                if method == 'schema':
                    results['schema'] = self.compare_schema()
                elif method == 'row_count':
                    results['row_count'] = self.compare_row_count()
                elif method == 'column_stats':
                    results['column_stats'] = self.compare_column_stats()
                elif method == 'duplicates':
                    results['duplicates'] = self.find_duplicates()
                elif method == 'differences':
                    results['differences'] = self.find_differences()
            
            self.progress.emit(100)
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))

    def compare_schema(self):
        schema1 = set(self.df1.columns)
        schema2 = set(self.df2.columns)
        return {
            'common_columns': list(schema1.intersection(schema2)),
            'unique_to_df1': list(schema1 - schema2),
            'unique_to_df2': list(schema2 - schema1)
        }

    def compare_row_count(self):
        return {
            'df1_rows': len(self.df1),
            'df2_rows': len(self.df2),
            'difference': abs(len(self.df1) - len(self.df2))
        }

    def compare_column_stats(self):
        common_cols = set(self.df1.columns).intersection(set(self.df2.columns))
        stats = {}
        for col in common_cols:
            if pd.api.types.is_numeric_dtype(self.df1[col]) and pd.api.types.is_numeric_dtype(self.df2[col]):
                stats[col] = {
                    'mean_diff': abs(self.df1[col].mean() - self.df2[col].mean()),
                    'std_diff': abs(self.df1[col].std() - self.df2[col].std()),
                    'min_diff': abs(self.df1[col].min() - self.df2[col].min()),
                    'max_diff': abs(self.df1[col].max() - self.df2[col].max())
                }
        return stats

    def find_duplicates(self):
        return {
            'df1_duplicates': self.df1.duplicated().sum(),
            'df2_duplicates': self.df2.duplicated().sum()
        }

    def find_differences(self):
        common_cols = list(set(self.df1.columns).intersection(set(self.df2.columns)))
        if not common_cols:
            return {}
        
        # Sample comparison for demonstration
        merged = pd.merge(self.df1[common_cols], self.df2[common_cols], 
                         how='outer', indicator=True)
        differences = merged[merged['_merge'] != 'both']
        return differences.to_dict('records')

class DataSourceWidget(QWidget):
    data_loaded = pyqtSignal(pd.DataFrame, str)
    load_started = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel(f"<h3>{self.title}</h3>")
        title_label.setStyleSheet("color: #007acc; font-weight: bold;")
        layout.addWidget(title_label)

        # Source type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Source Type:"))
        self.source_type = ModernComboBox()
        self.source_type.addItems(['CSV', 'SQL'])
        self.source_type.currentTextChanged.connect(self.on_source_type_changed)
        type_layout.addWidget(self.source_type)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # CSV widgets
        self.csv_group = ModernGroupBox("CSV Options")
        csv_layout = QVBoxLayout()
        csv_layout.setSpacing(5)
        
        path_layout = QHBoxLayout()
        self.csv_path = ModernLineEdit()
        self.csv_path.setPlaceholderText("Select CSV file...")
        self.csv_browse_btn = StyledButton("Browse")
        self.csv_browse_btn.clicked.connect(self.browse_csv)
        path_layout.addWidget(self.csv_path)
        path_layout.addWidget(self.csv_browse_btn)
        csv_layout.addLayout(path_layout)
        
        self.csv_group.setLayout(csv_layout)

        # SQL widgets
        self.sql_group = ModernGroupBox("SQL Options")
        sql_layout = QFormLayout()
        sql_layout.setSpacing(8)
        
        self.db_type = ModernComboBox()
        self.db_type.addItems(['sqlite', 'mysql', 'postgresql'])
        self.host = ModernLineEdit()
        self.host.setPlaceholderText("localhost")
        self.port = ModernLineEdit()
        self.port.setPlaceholderText("3306")
        self.database = ModernLineEdit()
        self.database.setPlaceholderText("database_name")
        self.username = ModernLineEdit()
        self.username.setPlaceholderText("username")
        self.password = ModernLineEdit()
        self.password.setPlaceholderText("password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.query = ModernTextEdit()
        self.query.setPlaceholderText("Enter your SQL query here...")
        self.query.setMaximumHeight(100)
        
        sql_layout.addRow("DB Type:", self.db_type)
        sql_layout.addRow("Host:", self.host)
        sql_layout.addRow("Port:", self.port)
        sql_layout.addRow("Database:", self.database)
        sql_layout.addRow("Username:", self.username)
        sql_layout.addRow("Password:", self.password)
        sql_layout.addRow("SQL Query:", self.query)
        self.sql_group.setLayout(sql_layout)
        self.sql_group.setVisible(False)

        # Load button
        self.load_btn = StyledButton(f"Load {self.title}", primary=True)
        self.load_btn.clicked.connect(self.load_data)

        # Progress bar
        self.progress = ModernProgressBar()
        self.progress.setVisible(False)

        layout.addWidget(self.csv_group)
        layout.addWidget(self.sql_group)
        layout.addWidget(self.load_btn)
        layout.addWidget(self.progress)

        self.setLayout(layout)

    def on_source_type_changed(self, text):
        self.csv_group.setVisible(text == 'CSV')
        self.sql_group.setVisible(text == 'SQL')

    def browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.csv_path.setText(file_path)

    def load_data(self):
        source_type = self.source_type.currentText().lower()
        
        if source_type == 'csv':
            file_path = self.csv_path.text()
            if not file_path:
                QMessageBox.warning(self, "Error", "Please select a CSV file")
                return
            source = file_path
            db_config = None
            
        else:  # SQL
            if not self.query.toPlainText().strip():
                QMessageBox.warning(self, "Error", "Please enter a SQL query")
                return
            
            db_type = self.db_type.currentText()
            host = self.host.text() or 'localhost'
            port = self.port.text() or '3306'
            database = self.database.text()
            username = self.username.text()
            password = self.password.text()
            
            if not all([database, username]):
                QMessageBox.warning(self, "Error", "Please fill all database fields")
                return
            
            db_config = f"{db_type}://{username}:{password}@{host}:{port}/{database}"
            source = self.query.toPlainText()

        self.load_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.load_started.emit()

        self.thread = DataLoaderThread(source_type, source, db_config)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.on_data_loaded)
        self.thread.error.connect(self.on_load_error)
        self.thread.start()

    def on_data_loaded(self, df, source_name):
        self.load_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.data_loaded.emit(df, source_name)

    def on_load_error(self, error_msg):
        self.load_btn.setEnabled(True)
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Load Error", f"Error loading data:\n{error_msg}")

class ComparisonResultsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 0px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Schema comparison tab
        self.schema_widget = ModernTableWidget()
        self.tabs.addTab(self.schema_widget, "📊 Schema")
        
        # Statistics tab
        self.stats_widget = ModernTextEdit()
        self.stats_widget.setReadOnly(True)
        self.tabs.addTab(self.stats_widget, "📈 Statistics")
        
        # Differences tab
        self.diff_widget = ModernTableWidget()
        self.tabs.addTab(self.diff_widget, "🔍 Differences")
        
        # Visualization tab
        self.viz_widget = QWidget()
        viz_layout = QVBoxLayout()
        self.figure_canvas = FigureCanvas(plt.Figure(figsize=(10, 6)))
        viz_layout.addWidget(self.figure_canvas)
        self.viz_widget.setLayout(viz_layout)
        self.tabs.addTab(self.viz_widget, "📊 Visualization")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def display_results(self, results):
        if 'schema' in results:
            self.display_schema(results['schema'])
        if 'row_count' in results:
            self.display_stats(results)
        if 'differences' in results:
            self.display_differences(results['differences'])
        if 'column_stats' in results:
            self.display_visualizations(results['column_stats'])

    def display_schema(self, schema_data):
        self.schema_widget.setRowCount(3)
        self.schema_widget.setColumnCount(2)
        self.schema_widget.setHorizontalHeaderLabels(['Category', 'Columns'])
        self.schema_widget.setVerticalHeaderLabels([])
        
        categories = ['Common Columns', 'Unique to Dataset 1', 'Unique to Dataset 2']
        data = [
            ', '.join(schema_data['common_columns']),
            ', '.join(schema_data['unique_to_df1']),
            ', '.join(schema_data['unique_to_df2'])
        ]
        
        for i, (category, columns) in enumerate(zip(categories, data)):
            self.schema_widget.setItem(i, 0, QTableWidgetItem(category))
            self.schema_widget.setItem(i, 1, QTableWidgetItem(columns))
        
        self.schema_widget.resizeColumnsToContents()

    def display_stats(self, results):
        stats_text = "<h3>📊 Dataset Comparison Results</h3>"
        
        if 'row_count' in results:
            rc = results['row_count']
            stats_text += f"<h4>📋 Row Count Comparison</h4>"
            stats_text += f"<b>Dataset 1:</b> {rc['df1_rows']:,} rows<br>"
            stats_text += f"<b>Dataset 2:</b> {rc['df2_rows']:,} rows<br>"
            stats_text += f"<b>Difference:</b> {rc['difference']:,} rows<br><br>"
        
        if 'duplicates' in results:
            dup = results['duplicates']
            stats_text += f"<h4>🔍 Duplicates Analysis</h4>"
            stats_text += f"<b>Dataset 1 duplicates:</b> {dup['df1_duplicates']:,}<br>"
            stats_text += f"<b>Dataset 2 duplicates:</b> {dup['df2_duplicates']:,}<br><br>"
        
        if 'column_stats' in results and results['column_stats']:
            stats_text += f"<h4>📈 Column Statistics Differences</h4>"
            for col, stats in results['column_stats'].items():
                stats_text += f"<b>{col}:</b><br>"
                stats_text += f"  • Mean difference: {stats['mean_diff']:.4f}<br>"
                stats_text += f"  • Std deviation difference: {stats['std_diff']:.4f}<br>"
                stats_text += f"  • Min difference: {stats.get('min_diff', 0):.4f}<br>"
                stats_text += f"  • Max difference: {stats.get('max_diff', 0):.4f}<br><br>"
        
        self.stats_widget.setHtml(stats_text)

    def display_differences(self, differences):
        if not differences:
            self.diff_widget.setRowCount(1)
            self.diff_widget.setColumnCount(1)
            self.diff_widget.setItem(0, 0, QTableWidgetItem("✅ No differences found"))
            return
        
        df = pd.DataFrame(differences)
        self.diff_widget.setRowCount(len(df))
        self.diff_widget.setColumnCount(len(df.columns))
        self.diff_widget.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                if pd.isna(value):
                    item.setBackground(QColor('#fff0f0'))
                self.diff_widget.setItem(i, j, item)
        
        self.diff_widget.resizeColumnsToContents()

    def display_visualizations(self, column_stats):
        self.figure_canvas.figure.clear()
        
        if not column_stats:
            ax = self.figure_canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No numeric columns for visualization', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='gray')
            ax.set_axis_off()
            self.figure_canvas.draw()
            return
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Statistical Comparison of Numeric Columns', fontsize=14, fontweight='bold')
        
        columns = list(column_stats.keys())
        metrics = ['mean_diff', 'std_diff', 'min_diff', 'max_diff']
        titles = ['Mean Differences', 'Std Deviation Differences', 'Min Differences', 'Max Differences']
        axes = [ax1, ax2, ax3, ax4]
        colors = ['#007acc', '#ff6b6b', '#34c759', '#ff9500']
        
        for ax, metric, title, color in zip(axes, metrics, titles, colors):
            values = [stats[metric] for stats in column_stats.values() if metric in stats]
            if values:
                bars = ax.bar(columns[:len(values)], values, color=color, alpha=0.7)
                ax.set_title(title, fontweight='bold')
                ax.tick_params(axis='x', rotation=45)
                
                # Add value labels
                for bar, value in zip(bars, values):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                           f'{value:.4f}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        self.figure_canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df1 = None
        self.df2 = None
        self.init_ui()
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
        """)

    def init_ui(self):
        self.setWindowTitle("🔍 Dataset Comparison Tool")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("<h1>🔍 Dataset Comparison Tool</h1>")
        header.setStyleSheet("color: #007acc; margin: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Splitter for data sources and results
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section: Data sources
        sources_widget = QWidget()
        sources_layout = QHBoxLayout()
        sources_layout.setSpacing(15)
        sources_layout.setContentsMargins(0, 0, 0, 0)
        
        self.source1 = DataSourceWidget("Dataset 1")
        self.source2 = DataSourceWidget("Dataset 2")
        
        self.source1.data_loaded.connect(lambda df, name: self.on_data_loaded(df, name, 1))
        self.source2.data_loaded.connect(lambda df, name: self.on_data_loaded(df, name, 2))
        self.source1.load_started.connect(self.on_load_started)
        self.source2.load_started.connect(self.on_load_started)
        
        sources_layout.addWidget(self.source1)
        sources_layout.addWidget(self.source2)
        sources_widget.setLayout(sources_layout)

        # Comparison options
        options_group = ModernGroupBox("Comparison Options")
        options_layout = QGridLayout()
        options_layout.setSpacing(10)
        
        self.compare_schema = QCheckBox("Compare Schema")
        self.compare_schema.setChecked(True)
        self.compare_rows = QCheckBox("Compare Row Counts")
        self.compare_rows.setChecked(True)
        self.compare_stats = QCheckBox("Compare Statistics")
        self.compare_stats.setChecked(True)
        self.find_dups = QCheckBox("Find Duplicates")
        self.find_diffs = QCheckBox("Find Differences")
        
        options_layout.addWidget(self.compare_schema, 0, 0)
        options_layout.addWidget(self.compare_rows, 0, 1)
        options_layout.addWidget(self.compare_stats, 0, 2)
        options_layout.addWidget(self.find_dups, 1, 0)
        options_layout.addWidget(self.find_diffs, 1, 1)
        options_group.setLayout(options_layout)

        # Compare button
        self.compare_btn = StyledButton("🚀 Compare Datasets", primary=True)
        self.compare_btn.clicked.connect(self.compare_datasets)
        self.compare_btn.setEnabled(False)

        # Progress bar for comparison
        self.compare_progress = ModernProgressBar()
        self.compare_progress.setVisible(False)

        # Results section
        self.results_widget = ComparisonResultsWidget()

        # Add widgets to splitter
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setSpacing(10)
        top_layout.addWidget(sources_widget)
        top_layout.addWidget(options_group)
        top_layout.addWidget(self.compare_btn)
        top_layout.addWidget(self.compare_progress)
        top_widget.setLayout(top_layout)

        splitter.addWidget(top_widget)
        splitter.addWidget(self.results_widget)
        splitter.setSizes([400, 500])

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def on_load_started(self):
        self.compare_btn.setEnabled(False)

    def on_data_loaded(self, df, source_name, dataset_num):
        if dataset_num == 1:
            self.df1 = df
            self.source1_label = source_name
        else:
            self.df2 = df
            self.source2_label = source_name
        
        if self.df1 is not None and self.df2 is not None:
            self.compare_btn.setEnabled(True)
            self.compare_btn.setText("🚀 Compare Datasets (Ready)")

    def compare_datasets(self):
        if self.df1 is None or self.df2 is None:
            QMessageBox.warning(self, "Error", "Please load both datasets first")
            return

        # Get selected comparison methods
        methods = []
        if self.compare_schema.isChecked():
            methods.append('schema')
        if self.compare_rows.isChecked():
            methods.append('row_count')
        if self.compare_stats.isChecked():
            methods.append('column_stats')
        if self.find_dups.isChecked():
            methods.append('duplicates')
        if self.find_diffs.isChecked():
            methods.append('differences')

        if not methods:
            QMessageBox.warning(self, "Error", "Please select at least one comparison method")
            return

        self.compare_btn.setEnabled(False)
        self.compare_btn.setText("⏳ Comparing...")
        self.compare_progress.setVisible(True)

        self.worker = ComparisonWorker(self.df1, self.df2, methods)
        self.worker.progress.connect(self.compare_progress.setValue)
        self.worker.finished.connect(self.on_comparison_finished)
        self.worker.error.connect(self.on_comparison_error)
        self.worker.start()

    def on_comparison_finished(self, results):
        self.compare_btn.setEnabled(True)
        self.compare_btn.setText("🚀 Compare Datasets")
        self.compare_progress.setVisible(False)
        self.results_widget.display_results(results)

    def on_comparison_error(self, error_msg):
        self.compare_btn.setEnabled(True)
        self.compare_btn.setText("🚀 Compare Datasets")
        self.compare_progress.setVisible(False)
        QMessageBox.critical(self, "Comparison Error", f"Error during comparison:\n{error_msg}")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
