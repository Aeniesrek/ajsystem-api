import os
import pyodbc
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# 環境変数からデータベース接続情報を取得
connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    f"Connection Timeout=30"
)

def _get_db_connection():
    try:
        return pyodbc.connect(connection_string)
    except pyodbc.Error as ex:
        raise RuntimeError(f"Database connection error: {str(ex)}")
    
def execute_query(query, params):
    conn = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
    except pyodbc.Error as ex:
        raise RuntimeError(f"Database error: {str(ex)}")
    finally:
        if conn:
            conn.close()
