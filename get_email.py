from flask import Blueprint, jsonify, request
from urllib.parse import unquote
from DataBaseAccessor.db_connector import execute_query
from DataBaseAccessor.queries import get_email_info_query

email_bp = Blueprint('email_bp', __name__)

@email_bp.route('/get_email', methods=['GET'])
def get_email():
    full_name = request.args.get('full_name')
    if not full_name:
        return jsonify({"error": "full_name parameter is required"}), 400

    full_name = unquote(full_name)
    # Inside the get_email function
    return get_email_info(full_name)

def get_email_info(full_name):
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
    except RuntimeError:
        return jsonify({"error": "Database error occurred"}), 500
    except Exception:
        return jsonify({"error": "Unexpected error occurred"}), 500
        
    return jsonify(result)
    

