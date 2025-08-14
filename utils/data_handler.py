import pandas as pd
import datacompy
from typing import List, Optional, Dict, Any

class DataHandler:
    """Handle data comparison operations using datacompy"""
    
    def __init__(self):
        self.base_df = None
        self.compare_df = None
        self.comparison_result = None
    
    def load_data(self, base_df: pd.DataFrame, compare_df: pd.DataFrame):
        """Load base and compare dataframes"""
        self.base_df = base_df.copy()
        self.compare_df = compare_df.copy()
    
    def run_comparison(self, base_df: pd.DataFrame, compare_df: pd.DataFrame, 
                      join_columns: List[str], compare_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run datacompy comparison and return comprehensive results"""
        try:
            # Ensure join_columns is a list
            if isinstance(join_columns, str):
                join_columns = [join_columns]
            
            # Run datacompy comparison
            comparison = datacompy.Compare(
                df1=base_df,
                df2=compare_df,
                join_columns=join_columns,
                df1_name='base',
                df2_name='compare'
            )
            
            # Extract comprehensive results
            results = {
                'comparison_obj': comparison,
                'base_shape': base_df.shape,
                'compare_shape': compare_df.shape,
                'base_columns': list(base_df.columns),
                'compare_columns': list(compare_df.columns),
                'join_columns': join_columns,
                'compare_columns': compare_columns or [],
                
                # Basic statistics
                'intersect_rows': len(comparison.intersect_rows),
                'base_only_rows': len(comparison.df1_unq_rows),
                'compare_only_rows': len(comparison.df2_unq_rows),
                'total_rows_base': len(base_df),
                'total_rows_compare': len(compare_df),
                
                # Match rate calculation
                'match_rate': self._calculate_match_rate(comparison),
                
                # Column differences
                'column_diffs': self._get_column_differences(comparison, compare_columns),
                
                # Summary report
                'summary_report': comparison.report(),
                
                # Additional metrics
                'columns_compared': list(comparison.intersect_columns()),
                'columns_base_only': list(comparison.df1_unq_columns()),
                'columns_compare_only': list(comparison.df2_unq_columns()),
                
                # Data type mismatches
                'dtype_mismatches': self._get_dtype_mismatches(comparison),
                
                # Memory usage
                'base_memory_usage': base_df.memory_usage(deep=True).sum(),
                'compare_memory_usage': compare_df.memory_usage(deep=True).sum()
            }
            
            return results
            
        except Exception as e:
            raise Exception(f"Comparison failed: {str(e)}")
    
    def _calculate_match_rate(self, comparison) -> float:
        """Calculate overall match rate"""
        try:
            total_intersect = len(comparison.intersect_rows)
            total_rows = max(len(comparison.df1), len(comparison.df2))
            
            if total_rows == 0:
                return 0.0
            
            return total_intersect / total_rows
        except:
            return 0.0
    
    def _get_column_differences(self, comparison, compare_columns: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """Get detailed column-by-column differences"""
        column_diffs = {}
        
        try:
            # Get columns to compare
            columns_to_check = compare_columns or list(comparison.intersect_columns())
            
            for col in columns_to_check:
                if col in list(comparison.intersect_columns()):
                    try:
                        # Get rows where this column differs
                        diff_rows = comparison.all_mismatch()
                        if not diff_rows.empty and col in diff_rows.columns:
                            column_diffs[col] = diff_rows[diff_rows[col].notna()]
                    except:
                        continue
        except:
            pass
        
        return column_diffs
    
    def _get_dtype_mismatches(self, comparison) -> Dict[str, Dict[str, str]]:
        """Get data type mismatches between dataframes"""
        dtype_mismatches = {}
        
        try:
            for col in list(comparison.intersect_columns()):
                base_dtype = str(comparison.df1[col].dtype)
                compare_dtype = str(comparison.df2[col].dtype)
                
                if base_dtype != compare_dtype:
                    dtype_mismatches[col] = {
                        'base_dtype': base_dtype,
                        'compare_dtype': compare_dtype
                    }
        except:
            pass
        
        return dtype_mismatches
    
    def export_results(self, results: Dict[str, Any], format: str = 'csv') -> str:
        """Export comparison results to various formats"""
        try:
            if format.lower() == 'csv':
                # Export summary as CSV
                summary_data = {
                    'Metric': [
                        'Base Rows', 'Compare Rows', 'Common Rows', 
                        'Base Only Rows', 'Compare Only Rows', 'Match Rate'
                    ],
                    'Value': [
                        results['base_shape'][0],
                        results['compare_shape'][0],
                        results['intersect_rows'],
                        results['base_only_rows'],
                        results['compare_only_rows'],
                        f"{results['match_rate']:.1%}"
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                return summary_df.to_csv(index=False)
            
            elif format.lower() == 'json':
                import json
                # Create JSON-serializable version
                json_results = {k: v for k, v in results.items() 
                              if k not in ['comparison_obj', 'column_diffs']}
                return json.dumps(json_results, indent=2)
            
            else:
                return results['summary_report']
                
        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")
