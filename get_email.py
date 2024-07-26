from flask import Blueprint, Flask, jsonify, request
import os
import pyodbc
from dotenv import load_dotenv
from flask_httpauth import HTTPTokenAuth
from urllib.parse import unquote
from decimal import Decimal

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Bearer')

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

# ダミーのトークンリスト（実際にはデータベースや他の方法で管理する）
tokens = {
    os.getenv('ACCESS_TOKEN'): "user1",
}

@auth.verify_token
def verify_token(token):
    return tokens.get(token)

email_bp = Blueprint('email_bp', __name__)

def get_db_connection():
    return pyodbc.connect(connection_string)

def execute_query(cursor, full_name):
    query = """
    SELECT 
        CAST(SUM(CAST(DATEDIFF(MINUTE, '00:00:00', A.Overtime) AS DECIMAL(10, 2)) / 60.0) AS DECIMAL(10, 2)) AS TotalOvertimeHours,
        COUNT(*) AS DateCount,
        E.Email
    FROM [dbo].[Attendances] A
    INNER JOIN AspNetUsers E ON A.UserId = E.Id
    WHERE (E.LastName + E.FirstName) = ?
      AND MONTH(A.[Date]) = MONTH(GETDATE())
      AND YEAR(A.[Date]) = YEAR(GETDATE())
    GROUP BY E.Email;
    """
    cursor.execute(query, (full_name,))
    return cursor.fetchone()

@email_bp.route('/get_email', methods=['GET'])
@auth.login_required
def get_email():
    full_name = request.args.get('full_name')
    if not full_name:
        return jsonify({"error": "full_name parameter is required"}), 400

    full_name = unquote(full_name)
    app.logger.info(f"Received full_name: {full_name}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        row = execute_query(cursor, full_name)

        if row:
            result = {
                "Email": row.Email, 
                "TotalOvertimeHours": float(row.TotalOvertimeHours) if row.TotalOvertimeHours is not None else None, 
                "DateCount": row.DateCount
            }
        else:
            result = {"Email": None, "TotalOvertimeHours": None, "DateCount": 0}

    except pyodbc.Error as ex:
        app.logger.error(f"Database error: {str(ex)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as ex:
        app.logger.error(f"Unexpected error: {str(ex)}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    finally:
        if conn:
            conn.close()
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
