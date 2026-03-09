"""
Database connectivity helpers.

This project connects to Achieva's Microsoft SQL Server using ODBC.
Connection settings are provided via environment variables (usually from `.env`).
"""

import os

from dotenv import load_dotenv

# Load `.env` into process env for local dev; in Docker, Compose also injects env vars.
load_dotenv()


def get_db_connection():
    """
    Create and return a live SQL Server connection via pyodbc.

    Notes:
    - `pyodbc` is imported lazily so the web server can start even if pyodbc
      isn't installed in a local environment (only DB routes need it).
    - The SQL Server host/port and credentials come from env vars:
      DB_SERVER, DB_NAME, DB_USER, DB_PWD
    """
    import pyodbc

    # ODBC Driver 18 defaults to encrypted connections; we explicitly allow
    # self-signed/enterprise certs by trusting the server certificate.
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PWD')};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

