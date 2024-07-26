from flask import Flask
from token_auth import auth
from get_email import email_bp

app = Flask(__name__)

# 全てのエンドポイントにトークン認証を適用
@app.before_request
@auth.login_required
def before_request():
    pass

app.register_blueprint(email_bp)

if __name__ == '__main__':
    app.run(debug=True)
