from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from database import get_db
from service.bpr_service import (
    process_rac_data,
    get_all_rac,
    get_rac_detail
)
from dto.rac_schema import RACSchema

rac_bp = Blueprint('rac', __name__, url_prefix='/rac')

@rac_bp.before_request
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

@rac_bp.route('/upload', methods=['POST'])
def uploarac_rac_data():
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
        result = process_rac_data(db, file)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@rac_bp.route('/', methods=['GET'])
def get_all():
    """
    Get all RAC entity records with pagination
    """
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        db = next(get_db())
        paginaterac_data = get_all_rac(db, page=page, per_page=per_page)
        
        schema = RACSchema(many=True)
        paginaterac_data['results'] = schema.dump(paginaterac_data['results'])
        
        return jsonify(paginaterac_data), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@rac_bp.route('/<int:rac_id>', methods=['GET'])
def get_detail(rac_id: int):
    """
    Get D entity detail by ID
    """
    try:
        db = next(get_db())
        rac_entity = get_rac_detail(db, rac_id)
        
        if not rac_entity:
            return jsonify({
                "status": "error",
                "message": f"D entity with ID {rac_id} not found"
            }), 404
            
        schema = RACSchema()
        result = schema.dump(rac_entity)
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
