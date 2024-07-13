from urllib.parse import quote as url_quote
from flask import Flask, jsonify, request
import os
import pyodbc
from dotenv import load_dotenv
from flask_httpauth import HTTPTokenAuth
import urllib.parse

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Bearer')

# .envファイルから環境変数を読み込み
load_dotenv()

# 環境変数からデータベース接続情報を取得
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'

# 接続文字列の作成
connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Connection Timeout=30'

# ダミーのトークンリスト（実際にはデータベースや他の方法で管理する）
tokens = {
    os.getenv('ACCESS_TOKEN'): "user1",
}

@auth.verify_token
def verify_token(token):
    if token in tokens:
        return tokens[token]
    return None

@app.route('/get_email', methods=['GET'])
@auth.login_required
def get_email():
    full_name = request.args.get('full_name')
    if not full_name:
        return jsonify({"error": "full_name parameter is required"}), 400

    # URLデコード
    full_name = urllib.parse.unquote(full_name)
    # デバッグメッセージを追加
    app.logger.info(f"Received full_name: {full_name}")

    conn = None
    result = []
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # サンプルクエリの実行
        query = """
SELECT CAST(SUM(CAST(DATEDIFF(MINUTE, '00:00:00', A.Overtime) AS DECIMAL(10, 2)) / 60.0) AS DECIMAL(10, 2)) AS TotalOvertimeHours,
       Count(*) As DateCount
FROM [dbo].[Attendances] A
INNER JOIN AspNetUsers E ON A.UserId = E.Id
WHERE (E.LastName + E.FirstName) = ?
  AND MONTH(A.[Date]) = MONTH(GETDATE())
  AND YEAR(A.[Date]) = YEAR(GETDATE());
        """
        cursor.execute(query, (full_name,))
        row = cursor.fetchone()
        if row:
            result.append(row.TotalOvertimeHours)
            result.append(row.DateCount)
        else:
            result.append(None)
            result.append(0)
    except pyodbc.Error as ex:
        app.logger.error(f"Database error: {str(ex)}")
        return jsonify({"error": str(ex), "query": query, "full_name": full_name, "connection_string": connection_string}), 500
    except Exception as ex:
        app.logger.error(f"Unexpected error: {str(ex)}")
        return jsonify({"error": str(ex)}), 500
    finally:
        # 接続を閉じる
        if conn:
            conn.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
