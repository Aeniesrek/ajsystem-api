import os
from flask_httpauth import HTTPTokenAuth

auth = HTTPTokenAuth(scheme='Bearer')

# ダミーのトークンリスト（実際にはデータベースや他の方法で管理する）
tokens = {
    os.getenv('ACCESS_TOKEN'): "user1",
}

@auth.verify_token
def verify_token(token):
    return tokens.get(token)
