import os
from dotenv import load_dotenv

load_dotenv()

def build_connection_string() -> str:
    """Build SQLAlchemy connection string for MSSQL"""
    driver = os.getenv("DB_DRIVER", "ODBC Driver 11 for SQL Server")
    server = os.getenv("DB_SERVER", "(local)")
    port = os.getenv("DB_PORT", "1433")
    database = os.getenv("DB_NAME", "ShareMarket")
    username = os.getenv("DB_USERNAME", "sa")
    password = os.getenv("DB_PASSWORD", "123")
    use_windows_auth = os.getenv("USE_WINDOWS_AUTH", "false").lower() == "true"

    if use_windows_auth:
        return f"mssql+pyodbc://@{server},{port}/{database}?driver={driver}&trusted_connection=yes"
    else:
        return f"mssql+pyodbc://{username}:{password}@{server},{port}/{database}?driver={driver}"