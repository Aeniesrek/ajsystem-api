from flask import Flask, jsonify
import os
import pyodbc
from dotenv import load_dotenv
from urllib.parse import quote as url_quote  # 修正
import hashlib

app = Flask(__name__)

# .envファイルから環境変数を読み込み
load_dotenv()

# 環境変数からデータベース接続情報を取得
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'

# 接続文字列の作成
connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD=****;Connection Timeout=30'  # パスワードをマスク

@app.route('/get_email', methods=['GET'])
def get_email():
    conn = None
    result = []
    try:
        # 実際の接続文字列を使用して接続
        real_connection_string = connection_string.replace("PWD=****", f"PWD={password}")
        conn = pyodbc.connect(real_connection_string)
        cursor = conn.cursor()

        # サンプルクエリの実行
        cursor.execute("SELECT Email FROM [dbo].[AspNetUsers] WHERE LastName = N'森口' and FirstName = N'裕之'")
        row = cursor.fetchone()
        while row:
            hashed_email = hashlib.sha256(row.Email.encode()).hexdigest()
            result.append(hashed_email)
            row = cursor.fetchone()
    except pyodbc.Error as ex:
        return jsonify({"error": str(ex), "connection_string": connection_string}), 500
    finally:
        # 接続を閉じる
        if conn:
            conn.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
