import duckdb
import pandas as pd
import uuid
import os
import glob
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import atexit

class DuckDBHandler:
    """Handle DuckDB operations for session-based data storage"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.db_path = f"session_{self.session_id}.duckdb"
        
        # Clean up old session files before creating new session
        self._cleanup_old_sessions()
        
        self.conn = duckdb.connect(self.db_path)
        self._initialize_schema()
        
        # Register cleanup to run when app exits
        atexit.register(self.cleanup_current_session)
    
    def _cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old DuckDB session files to prevent storage accumulation"""
        try:
            # Get all session files matching the pattern
            session_files = glob.glob("session_*.duckdb*")
            current_time = time.time()
            cleaned_count = 0
            
            for file_path in session_files:
                try:
                    # Check file age
                    file_age_hours = (current_time - os.path.getmtime(file_path)) / 3600
                    
                    if file_age_hours > max_age_hours:
                        os.remove(file_path)
                        cleaned_count += 1
                        print(f"DEBUG: Cleaned up old session file: {file_path}")
                        
                except Exception as e:
                    print(f"DEBUG: Could not remove session file {file_path}: {e}")
                    continue
            
            if cleaned_count > 0:
                print(f"DEBUG: Cleaned up {cleaned_count} old session files (older than {max_age_hours} hours)")
                
        except Exception as e:
            print(f"DEBUG: Error during session cleanup: {e}")
    
    def _initialize_schema(self):
        """Initialize the database schema"""
        try:
            # Create tables for storing datasets (DuckDB uses sequences for auto-increment)
            self.conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS dataset_seq START 1
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS base_dataset (
                    id INTEGER PRIMARY KEY DEFAULT nextval('dataset_seq'),
                    data TEXT,
                    columns TEXT,
                    shape_rows INTEGER,
                    shape_cols INTEGER,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS compare_dataset (
                    id INTEGER PRIMARY KEY DEFAULT nextval('dataset_seq'),
                    data TEXT,
                    columns TEXT,
                    shape_rows INTEGER,
                    shape_cols INTEGER,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create table for comparison results
            self.conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS comparison_seq START 1
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS comparison_results (
                    id INTEGER PRIMARY KEY DEFAULT nextval('comparison_seq'),
                    base_rows INTEGER,
                    compare_rows INTEGER,
                    common_rows INTEGER,
                    base_only_rows INTEGER,
                    compare_only_rows INTEGER,
                    match_rate REAL,
                    total_mismatches INTEGER,
                    columns_compared INTEGER,
                    column_differences INTEGER,
                    dtype_mismatches INTEGER,
                    comparison_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    results_json TEXT
                )
            """)
            
            # Create table for detailed mismatches
            self.conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS mismatch_seq START 1
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS mismatch_details (
                    id INTEGER PRIMARY KEY DEFAULT nextval('mismatch_seq'),
                    comparison_id INTEGER,
                    column_name TEXT,
                    row_index INTEGER,
                    base_value TEXT,
                    compare_value TEXT,
                    mismatch_type TEXT
                )
            """)
            
        except Exception as e:
            print(f"Error initializing schema: {e}")
    
    def store_base_dataset(self, df: pd.DataFrame) -> bool:
        """Store base dataset in DuckDB"""
        try:
            # Clear existing data
            self.conn.execute("DELETE FROM base_dataset")
            
            # Store DataFrame as JSON
            data_json = df.to_json(orient='split')
            columns_json = df.columns.tolist()
            
            self.conn.execute("""
                INSERT INTO base_dataset (data, columns, shape_rows, shape_cols)
                VALUES (?, ?, ?, ?)
            """, (data_json, str(columns_json), len(df), len(df.columns)))
            
            return True
        except Exception as e:
            print(f"Error storing base dataset: {e}")
            return False
    
    def store_compare_dataset(self, df: pd.DataFrame) -> bool:
        """Store compare dataset in DuckDB"""
        try:
            # Clear existing data
            self.conn.execute("DELETE FROM compare_dataset")
            
            # Store DataFrame as JSON
            data_json = df.to_json(orient='split')
            columns_json = df.columns.tolist()
            
            self.conn.execute("""
                INSERT INTO compare_dataset (data, columns, shape_rows, shape_cols)
                VALUES (?, ?, ?, ?)
            """, (data_json, str(columns_json), len(df), len(df.columns)))
            
            return True
        except Exception as e:
            print(f"Error storing compare dataset: {e}")
            return False
    
    def get_base_dataset(self) -> Optional[pd.DataFrame]:
        """Retrieve base dataset from DuckDB"""
        try:
            result = self.conn.execute("SELECT data FROM base_dataset ORDER BY id DESC LIMIT 1").fetchone()
            if result:
                return pd.read_json(result[0], orient='split')
            return None
        except Exception as e:
            print(f"Error retrieving base dataset: {e}")
            return None
    
    def get_compare_dataset(self) -> Optional[pd.DataFrame]:
        """Retrieve compare dataset from DuckDB"""
        try:
            result = self.conn.execute("SELECT data FROM compare_dataset ORDER BY id DESC LIMIT 1").fetchone()
            if result:
                return pd.read_json(result[0], orient='split')
            return None
        except Exception as e:
            print(f"Error retrieving compare dataset: {e}")
            return None
    
    def store_comparison_results(self, results: Dict[str, Any]) -> int:
        """Store comparison results and return comparison ID"""
        try:
            import json
            
            # Calculate total mismatches
            total_mismatches = results.get('base_only_rows', 0) + results.get('compare_only_rows', 0)
            
            # Insert comparison summary
            cursor = self.conn.execute("""
                INSERT INTO comparison_results (
                    base_rows, compare_rows, common_rows, base_only_rows, compare_only_rows,
                    match_rate, total_mismatches, columns_compared, column_differences,
                    dtype_mismatches, results_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                results.get('total_rows_base', 0),
                results.get('total_rows_compare', 0),
                results.get('intersect_rows', 0),
                results.get('base_only_rows', 0),
                results.get('compare_only_rows', 0),
                results.get('match_rate', 0.0),
                total_mismatches,
                len(results.get('columns_compared', [])),
                len(results.get('column_diffs', {})),
                len(results.get('dtype_mismatches', {})),
                json.dumps({k: v for k, v in results.items() if k not in ['comparison_obj', 'column_diffs']}, default=str)
            ))
            
            comparison_id = cursor.lastrowid
            
            # Store detailed mismatch information
            self._store_mismatch_details(comparison_id, results)
            
            return comparison_id
            
        except Exception as e:
            print(f"Error storing comparison results: {e}")
            return -1
    
    def _store_mismatch_details(self, comparison_id: int, results: Dict[str, Any]):
        """Store detailed mismatch information"""
        try:
            # Clear existing mismatch details for this comparison
            self.conn.execute("DELETE FROM mismatch_details WHERE comparison_id = ?", (comparison_id,))
            
            # Store column-level differences
            column_diffs = results.get('column_diffs', {})
            for col_name, diff_df in column_diffs.items():
                if hasattr(diff_df, 'iterrows'):
                    for idx, row in diff_df.iterrows():
                        base_val = str(row.get(f'{col_name}_base', ''))
                        compare_val = str(row.get(f'{col_name}_compare', ''))
                        
                        self.conn.execute("""
                            INSERT INTO mismatch_details 
                            (comparison_id, column_name, row_index, base_value, compare_value, mismatch_type)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (comparison_id, col_name, idx, base_val, compare_val, 'value_mismatch'))
            
        except Exception as e:
            print(f"Error storing mismatch details: {e}")
    
    def get_comparison_results(self) -> Optional[Dict[str, Any]]:
        """Get the latest comparison results"""
        try:
            result = self.conn.execute("""
                SELECT * FROM comparison_results ORDER BY id DESC LIMIT 1
            """).fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'base_rows': result[1],
                    'compare_rows': result[2],
                    'common_rows': result[3],
                    'base_only_rows': result[4],
                    'compare_only_rows': result[5],
                    'match_rate': result[6],
                    'total_mismatches': result[7],
                    'columns_compared': result[8],
                    'column_differences': result[9],
                    'dtype_mismatches': result[10],
                    'comparison_time': result[11]
                }
            return None
        except Exception as e:
            print(f"Error getting comparison results: {e}")
            return None
    
    def get_mismatch_details(self, comparison_id: int = None) -> pd.DataFrame:
        """Get detailed mismatch information"""
        try:
            if comparison_id is None:
                # Get latest comparison ID
                result = self.conn.execute("SELECT id FROM comparison_results ORDER BY id DESC LIMIT 1").fetchone()
                if not result:
                    return pd.DataFrame()
                comparison_id = result[0]
            
            query = """
                SELECT column_name, row_index, base_value, compare_value, mismatch_type
                FROM mismatch_details 
                WHERE comparison_id = ?
                ORDER BY column_name, row_index
            """
            
            return self.conn.execute(query, (comparison_id,)).df()
            
        except Exception as e:
            print(f"Error getting mismatch details: {e}")
            return pd.DataFrame()
    
    def get_column_stats(self) -> pd.DataFrame:
        """Get column-level statistics for the dashboard"""
        try:
            base_df = self.get_base_dataset()
            compare_df = self.get_compare_dataset()
            
            if base_df is None or compare_df is None:
                return pd.DataFrame()
            
            stats_data = []
            
            # Get common columns
            common_cols = set(base_df.columns).intersection(set(compare_df.columns))
            
            for col in common_cols:
                base_nulls = base_df[col].isnull().sum()
                compare_nulls = compare_df[col].isnull().sum()
                
                base_dtype = str(base_df[col].dtype)
                compare_dtype = str(compare_df[col].dtype)
                dtype_match = base_dtype == compare_dtype
                
                stats_data.append({
                    'Column': col,
                    'Base_Nulls': base_nulls,
                    'Compare_Nulls': compare_nulls,
                    'Base_DType': base_dtype,
                    'Compare_DType': compare_dtype,
                    'DType_Match': dtype_match
                })
            
            return pd.DataFrame(stats_data)
            
        except Exception as e:
            print(f"Error getting column stats: {e}")
            return pd.DataFrame()
    
    def cleanup_current_session(self):
        """Clean up the current session and its files"""
        try:
            # Close the database connection first
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                print(f"DEBUG: Closed DuckDB connection for session {self.session_id}")
            
            # Remove current session files
            session_files = [
                self.db_path,
                f"{self.db_path}.wal",  # Write-ahead log file
                f"{self.db_path}.tmp"   # Temporary files
            ]
            
            for file_path in session_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"DEBUG: Removed session file: {file_path}")
                    except Exception as e:
                        print(f"DEBUG: Could not remove {file_path}: {e}")
                        
        except Exception as e:
            print(f"DEBUG: Error during current session cleanup: {e}")
    
    def cleanup(self):
        """Close connection but keep database file for session persistence"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except Exception as e:
            print(f"DEBUG: Error closing DuckDB connection: {e}")
    
    def force_cleanup_all_sessions(self):
        """Force cleanup of all session files (use with caution)"""
        try:
            session_files = glob.glob("session_*.duckdb*")
            cleaned_count = 0
            
            for file_path in session_files:
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    print(f"DEBUG: Force removed session file: {file_path}")
                except Exception as e:
                    print(f"DEBUG: Could not remove session file {file_path}: {e}")
                    continue
            
            print(f"DEBUG: Force cleaned {cleaned_count} session files")
            return cleaned_count
            
        except Exception as e:
            print(f"DEBUG: Error during force cleanup: {e}")
            return 0
    
    @staticmethod
    def get_session_files_info():
        """Get information about current session files"""
        try:
            session_files = glob.glob("session_*.duckdb*")
            file_info = []
            
            for file_path in session_files:
                try:
                    file_size = os.path.getsize(file_path)
                    file_age = time.time() - os.path.getmtime(file_path)
                    
                    file_info.append({
                        'filename': file_path,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'age_hours': round(file_age / 3600, 1)
                    })
                except Exception as e:
                    print(f"DEBUG: Error getting info for {file_path}: {e}")
                    continue
            
            return file_info
            
        except Exception as e:
            print(f"DEBUG: Error getting session files info: {e}")
            return []
    
    def __del__(self):
        self.cleanup()