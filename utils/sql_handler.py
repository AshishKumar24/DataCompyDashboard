import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
import os
from typing import Optional

class SQLHandler:
    """Handle SQL database connections and queries"""
    
    def __init__(self):
        self.engine = None
        self.connection_string = None
    
    def create_connection_string(self, host: str, port: int, database: str, 
                               username: str, password: str, 
                               driver: str = 'postgresql') -> str:
        """Create a database connection string"""
        if driver.lower() in ['postgresql', 'postgres']:
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif driver.lower() == 'mysql':
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        elif driver.lower() == 'sqlite':
            return f"sqlite:///{database}"
        else:
            raise ValueError(f"Unsupported database driver: {driver}")
    
    def connect(self, connection_string: str = None, **kwargs) -> bool:
        """Connect to the database"""
        try:
            if connection_string:
                self.connection_string = connection_string
            elif kwargs:
                self.connection_string = self.create_connection_string(**kwargs)
            else:
                # Try to use environment variables as fallback
                self.connection_string = self._get_env_connection_string()
            
            if not self.connection_string:
                raise ValueError("No connection string provided")
            
            self.engine = create_engine(self.connection_string)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
            
            return True
            
        except Exception as e:
            raise Exception(f"Database connection failed: {str(e)}")
    
    def _get_env_connection_string(self) -> Optional[str]:
        """Get connection string from environment variables"""
        try:
            # Check for DATABASE_URL first (common in cloud environments)
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                return database_url
            
            # Check for individual PostgreSQL environment variables
            host = os.getenv('PGHOST')
            port = os.getenv('PGPORT', '5432')
            database = os.getenv('PGDATABASE')
            username = os.getenv('PGUSER')
            password = os.getenv('PGPASSWORD')
            
            if all([host, database, username, password]):
                return f"postgresql://{username}:{password}@{host}:{port}/{database}"
            
            return None
            
        except Exception:
            return None
    
    def execute_query(self, host: str = None, port: int = None, database: str = None,
                     username: str = None, password: str = None, query: str = None,
                     connection_string: str = None) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame"""
        try:
            # Connect if not already connected or if new credentials provided
            if not self.engine or any([host, port, database, username, password]):
                if connection_string:
                    self.connect(connection_string=connection_string)
                elif all([host, database, username, password]):
                    self.connect(
                        host=host,
                        port=port or 5432,
                        database=database,
                        username=username,
                        password=password
                    )
                else:
                    # Try environment variables
                    self.connect()
            
            if not query:
                raise ValueError("Query is required")
            
            # Execute query and return DataFrame
            df = pd.read_sql_query(query, self.engine)
            
            if df.empty:
                raise ValueError("Query returned no results")
            
            return df
            
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    def test_connection(self, **kwargs) -> tuple[bool, str]:
        """Test database connection and return status"""
        try:
            # Temporarily create connection for testing
            if kwargs:
                connection_string = self.create_connection_string(**kwargs)
            else:
                connection_string = self._get_env_connection_string()
            
            if not connection_string:
                return False, "No connection parameters provided"
            
            engine = create_engine(connection_string)
            
            with engine.connect() as conn:
                result = conn.execute(sqlalchemy.text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                
                if test_value == 1:
                    return True, "Connection successful"
                else:
                    return False, "Connection test failed"
                    
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_table_info(self, table_name: str = None) -> pd.DataFrame:
        """Get information about tables in the database"""
        try:
            if not self.engine:
                raise Exception("Not connected to database")
            
            if table_name:
                query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %(table_name)s
                ORDER BY ordinal_position
                """
                return pd.read_sql_query(query, self.engine, params={'table_name': table_name})
            else:
                query = """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
                return pd.read_sql_query(query, self.engine)
                
        except Exception as e:
            raise Exception(f"Failed to get table info: {str(e)}")
    
    def close_connection(self):
        """Close the database connection"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
