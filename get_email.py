from flask import Blueprint, Flask, jsonify, request
import os
from flask_httpauth import HTTPTokenAuth
from urllib.parse import unquote
from DataBaseAccessor.db_connector import execute_query
from DataBaseAccessor.queries import get_email_info_query

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Bearer')

# ダミーのトークンリスト（実際にはデータベースや他の方法で管理する）
tokens = {
    os.getenv('ACCESS_TOKEN'): "user1",
}

@auth.verify_token
def verify_token(token):
    return tokens.get(token)

email_bp = Blueprint('email_bp', __name__)
@email_bp.route('/get_email', methods=['GET'])
@auth.login_required
def get_email():
    full_name = request.args.get('full_name')
    if not full_name:
        return jsonify({"error": "full_name parameter is required"}), 400

    full_name = unquote(full_name)
    app.logger.info(f"Received full_name: {full_name}")

    try:
        row = execute_query(get_email_info_query(), (full_name,))

        if row:
            result = {
                "Email": row.Email, 
                "TotalOvertimeHours": float(row.TotalOvertimeHours) if row.TotalOvertimeHours is not None else None, 
                "DateCount": row.DateCount
            }
        else:
            result = {"Email": None, "TotalOvertimeHours": None, "DateCount": 0}

    except RuntimeError as ex:
        app.logger.error(str(ex))
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as ex:
        app.logger.error(f"Unexpected error: {str(ex)}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
