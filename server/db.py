import os
import urllib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

load_dotenv()

# 1. The Raw Connection String (shared logic)
def _get_conn_str():
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PWD')};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

# 2. Keep your original helper (for raw SQL)
def get_db_connection():
    import pyodbc
    return pyodbc.connect(_get_conn_str())

# 3. NEW: SQLAlchemy Engine (for your new Services)
def get_engine():
    """
    Creates a SQLAlchemy engine. 
    Note the 'mssql+pyodbc://' prefix and the URL encoding.
    """
    params = urllib.parse.quote_plus(_get_conn_str())
    engine_url = f"mssql+pyodbc:///?odbc_connect={params}"
    
    # pool_pre_ping=True helps keep the connection alive if SQL Server drops it
    return create_engine(engine_url, pool_pre_ping=True)

# 4. NEW: Global Session Factory
# This makes it easier to use 'Session(engine)' in your services
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())