import os
import pyodbc
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# 環境変数からデータベース接続情報を取得
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'

print("Server:", server)
print("Database:", database)
print("Username:", username)
print("Password:", password)

# 接続文字列の作成
connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

conn = None
try:
    # データベースへの接続
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    # サンプルクエリの実行
    cursor.execute("SELECT Email FROM [dbo].[AspNetUsers] WHERE LastName = N'森口' and FirstName = N'裕之'")
    row = cursor.fetchone()
    while row:
        print(row)
        row = cursor.fetchone()
except pyodbc.Error as ex:
    print("Error:", ex)
finally:
    # 接続を閉じる
    if conn:
        conn.close()
