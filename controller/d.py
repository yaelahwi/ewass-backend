from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from database import get_db
from service.bpr_service import (
    process_d_data,
    get_all_d,
    get_d_detail
)
from dto.d_schema import DSchema

d_bp = Blueprint('d', __name__, url_prefix='/d')

@d_bp.before_request
def require_jwt():
    try:
        verify_jwt_in_request()
        # Get the current user identity
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({
                "status": "error",
                "message": "Invalid authentication token"
            }), 401
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 401

@d_bp.route('/upload', methods=['POST'])
def upload_d_data():
    """
    Upload and process D entity XLSX file
    """
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
            
        db = next(get_db())
        result = process_d_data(db, file)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@d_bp.route('/', methods=['GET'])
def get_all():
    """
    Get all D entity records with pagination
    """
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        db = next(get_db())
        paginated_data = get_all_d(db, page=page, per_page=per_page)
        
        schema = DSchema(many=True)
        paginated_data['results'] = schema.dump(paginated_data['results'])
        
        return jsonify(paginated_data), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@d_bp.route('/<int:d_id>', methods=['GET'])
def get_detail(d_id: int):
    """
    Get D entity detail by ID
    """
    try:
        db = next(get_db())
        d_entity = get_d_detail(db, d_id)
        
        if not d_entity:
            return jsonify({
                "status": "error",
                "message": f"D entity with ID {d_id} not found"
            }), 404
            
        schema = DSchema()
        result = schema.dump(d_entity)
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
