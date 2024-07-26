from flask import Flask
from get_email import email_bp

app = Flask(__name__)
app.register_blueprint(email_bp)

if __name__ == '__main__':
    app.run(debug=True)