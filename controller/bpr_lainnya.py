from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from database import get_db
from service.bpr_service import (
    process_bpr_lainnya,
    get_all_bpr_lainnya,
    get_bpr_lainnya_detail
)
from dto.bpr_lainnya_schema import BprLainnyaSchema

bpr_lainnya_bp = Blueprint('bpr_lainnya', __name__, url_prefix='/bpr_lainnya')

@bpr_lainnya_bp.before_request
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

@bpr_lainnya_bp.route('/upload', methods=['POST'])
def upload_bpr_lainnya():
    """
    Upload and process BPR Lainnya XLSX file
    """
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
            
        db = next(get_db())
        result = process_bpr_lainnya(db, file)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@bpr_lainnya_bp.route('/', methods=['GET'])
def get_all():
    """
    Get all BPR Lainnya records with pagination
    """
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        db = next(get_db())
        paginated_data = get_all_bpr_lainnya(db, page=page, per_page=per_page)
        
        schema = BprLainnyaSchema(many=True)
        paginated_data['results'] = schema.dump(paginated_data['results'])
        
        return jsonify(paginated_data), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@bpr_lainnya_bp.route('/<int:bpr_id>', methods=['GET'])
def get_detail(bpr_id: int):
    """
    Get BPR Lainnya detail by ID
    """
    try:
        db = next(get_db())
        bpr_lainnya = get_bpr_lainnya_detail(db, bpr_id)
        
        if not bpr_lainnya:
            return jsonify({
                "status": "error",
                "message": f"BPR Lainnya with ID {bpr_id} not found"
            }), 404
            
        schema = BprLainnyaSchema()
        result = schema.dump(bpr_lainnya)
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
