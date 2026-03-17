import os
import urllib
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

# 3. SQLAlchemy Engine (shared across services/bootstrap)
@lru_cache(maxsize=1)
def get_engine():
    """
    Create a shared SQLAlchemy engine.

    Prefer DATABASE_URL when present so older FastAPI-style configs still work;
    otherwise build a pyodbc URL from the .env fields.
    """
    engine_url = os.getenv("DATABASE_URL")
    if not engine_url:
        params = urllib.parse.quote_plus(_get_conn_str())
        engine_url = f"mssql+pyodbc:///?odbc_connect={params}"

    # pool_pre_ping=True helps keep the connection alive if SQL Server drops it.
    return create_engine(engine_url, pool_pre_ping=True)

# 4. Global Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())