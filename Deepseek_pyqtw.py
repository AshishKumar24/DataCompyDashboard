import sys
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QPushButton, QLabel, 
                            QTextEdit, QFileDialog, QMessageBox, QTableWidget,
                            QTableWidgetItem, QSplitter, QProgressBar, QComboBox,
                            QGroupBox, QFormLayout, QLineEdit, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import sqlite3
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

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
            if self.df1[col].dtype in ['int64', 'float64']:
                stats[col] = {
                    'mean_diff': abs(self.df1[col].mean() - self.df2[col].mean()),
                    'std_diff': abs(self.df1[col].std() - self.df2[col].std())
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

        # Source type selection
        self.source_type = QComboBox()
        self.source_type.addItems(['CSV', 'SQL'])
        self.source_type.currentTextChanged.connect(self.on_source_type_changed)

        # CSV widgets
        self.csv_group = QGroupBox("CSV Options")
        csv_layout = QVBoxLayout()
        self.csv_path = QLineEdit()
        self.csv_browse_btn = QPushButton("Browse")
        self.csv_browse_btn.clicked.connect(self.browse_csv)
        csv_layout.addWidget(QLabel("CSV File:"))
        csv_layout.addWidget(self.csv_path)
        csv_layout.addWidget(self.csv_browse_btn)
        self.csv_group.setLayout(csv_layout)

        # SQL widgets
        self.sql_group = QGroupBox("SQL Options")
        sql_layout = QFormLayout()
        self.db_type = QComboBox()
        self.db_type.addItems(['sqlite', 'mysql', 'postgresql'])
        self.host = QLineEdit()
        self.port = QLineEdit()
        self.database = QLineEdit()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.query = QTextEdit()
        
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
        self.load_btn = QPushButton(f"Load {self.title}")
        self.load_btn.clicked.connect(self.load_data)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)

        layout.addWidget(QLabel(f"<b>{self.title}</b>"))
        layout.addWidget(QLabel("Source Type:"))
        layout.addWidget(self.source_type)
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
        
        self.tabs = QTabWidget()
        
        # Schema comparison tab
        self.schema_widget = QTableWidget()
        self.tabs.addTab(self.schema_widget, "Schema")
        
        # Statistics tab
        self.stats_widget = QTextEdit()
        self.stats_widget.setReadOnly(True)
        self.tabs.addTab(self.stats_widget, "Statistics")
        
        # Differences tab
        self.diff_widget = QTableWidget()
        self.tabs.addTab(self.diff_widget, "Differences")
        
        # Visualization tab
        self.viz_widget = QWidget()
        viz_layout = QVBoxLayout()
        self.figure_canvas = FigureCanvas(plt.Figure())
        viz_layout.addWidget(self.figure_canvas)
        self.viz_widget.setLayout(viz_layout)
        self.tabs.addTab(self.viz_widget, "Visualization")
        
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
        self.schema_widget.setColumnCount(1)
        self.schema_widget.setHorizontalHeaderLabels(['Information'])
        self.schema_widget.setVerticalHeaderLabels([
            'Common Columns', 'Unique to Dataset 1', 'Unique to Dataset 2'
        ])
        
        self.schema_widget.setItem(0, 0, QTableWidgetItem(', '.join(schema_data['common_columns'])))
        self.schema_widget.setItem(1, 0, QTableWidgetItem(', '.join(schema_data['unique_to_df1'])))
        self.schema_widget.setItem(2, 0, QTableWidgetItem(', '.join(schema_data['unique_to_df2'])))
        
        self.schema_widget.resizeColumnsToContents()

    def display_stats(self, results):
        stats_text = "=== Row Count Comparison ===\n"
        if 'row_count' in results:
            rc = results['row_count']
            stats_text += f"Dataset 1: {rc['df1_rows']} rows\n"
            stats_text += f"Dataset 2: {rc['df2_rows']} rows\n"
            stats_text += f"Difference: {rc['difference']} rows\n\n"
        
        if 'duplicates' in results:
            dup = results['duplicates']
            stats_text += "=== Duplicates ===\n"
            stats_text += f"Dataset 1 duplicates: {dup['df1_duplicates']}\n"
            stats_text += f"Dataset 2 duplicates: {dup['df2_duplicates']}\n\n"
        
        if 'column_stats' in results:
            stats_text += "=== Column Statistics Differences ===\n"
            for col, stats in results['column_stats'].items():
                stats_text += f"{col}: Mean diff={stats['mean_diff']:.4f}, Std diff={stats['std_diff']:.4f}\n"
        
        self.stats_widget.setText(stats_text)

    def display_differences(self, differences):
        if not differences:
            self.diff_widget.setRowCount(1)
            self.diff_widget.setColumnCount(1)
            self.diff_widget.setItem(0, 0, QTableWidgetItem("No differences found"))
            return
        
        df = pd.DataFrame(differences)
        self.diff_widget.setRowCount(len(df))
        self.diff_widget.setColumnCount(len(df.columns))
        self.diff_widget.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.diff_widget.setItem(i, j, QTableWidgetItem(str(value)))
        
        self.diff_widget.resizeColumnsToContents()

    def display_visualizations(self, column_stats):
        self.figure_canvas.figure.clear()
        
        if not column_stats:
            ax = self.figure_canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No numeric columns for visualization', 
                   ha='center', va='center', transform=ax.transAxes)
            self.figure_canvas.draw()
            return
        
        # Create bar chart for mean differences
        columns = list(column_stats.keys())
        mean_diffs = [stats['mean_diff'] for stats in column_stats.values()]
        
        ax = self.figure_canvas.figure.add_subplot(111)
        bars = ax.bar(columns, mean_diffs)
        ax.set_title('Mean Differences by Column')
        ax.set_ylabel('Absolute Mean Difference')
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars, mean_diffs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                   f'{value:.4f}', ha='center', va='bottom')
        
        self.figure_canvas.figure.tight_layout()
        self.figure_canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df1 = None
        self.df2 = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Dataset Comparison Tool")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Splitter for data sources and results
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section: Data sources
        sources_widget = QWidget()
        sources_layout = QHBoxLayout()
        
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
        options_group = QGroupBox("Comparison Options")
        options_layout = QHBoxLayout()
        
        self.compare_schema = QCheckBox("Compare Schema")
        self.compare_schema.setChecked(True)
        self.compare_rows = QCheckBox("Compare Row Counts")
        self.compare_rows.setChecked(True)
        self.compare_stats = QCheckBox("Compare Statistics")
        self.compare_stats.setChecked(True)
        self.find_dups = QCheckBox("Find Duplicates")
        self.find_diffs = QCheckBox("Find Differences")
        
        options_layout.addWidget(self.compare_schema)
        options_layout.addWidget(self.compare_rows)
        options_layout.addWidget(self.compare_stats)
        options_layout.addWidget(self.find_dups)
        options_layout.addWidget(self.find_diffs)
        options_group.setLayout(options_layout)

        # Compare button
        self.compare_btn = QPushButton("Compare Datasets")
        self.compare_btn.clicked.connect(self.compare_datasets)
        self.compare_btn.setEnabled(False)

        # Progress bar for comparison
        self.compare_progress = QProgressBar()
        self.compare_progress.setVisible(False)

        # Results section
        self.results_widget = ComparisonResultsWidget()

        # Add widgets to splitter
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.addWidget(sources_widget)
        top_layout.addWidget(options_group)
        top_layout.addWidget(self.compare_btn)
        top_layout.addWidget(self.compare_progress)
        top_widget.setLayout(top_layout)

        splitter.addWidget(top_widget)
        splitter.addWidget(self.results_widget)
        splitter.setSizes([300, 500])

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
        self.compare_progress.setVisible(True)

        self.worker = ComparisonWorker(self.df1, self.df2, methods)
        self.worker.progress.connect(self.compare_progress.setValue)
        self.worker.finished.connect(self.on_comparison_finished)
        self.worker.error.connect(self.on_comparison_error)
        self.worker.start()

    def on_comparison_finished(self, results):
        self.compare_btn.setEnabled(True)
        self.compare_progress.setVisible(False)
        self.results_widget.display_results(results)

    def on_comparison_error(self, error_msg):
        self.compare_btn.setEnabled(True)
        self.compare_progress.setVisible(False)
        QMessageBox.critical(self, "Comparison Error", f"Error during comparison:\n{error_msg}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
