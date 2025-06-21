from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from database import get_db
from datetime import datetime
import os
from service.bpr_service import (
    process_bpr_scrapping,
    get_all_bpr_scrapping,
    get_bpr_scrapping_detail,
    get_all_bpr_labeled,
    get_bpr_labeled_detail
)
from service.scrapping_service import thread_scrapping
from dto.bpr_scrapping_schema import BprScrappingSchema
from dto.bpr_labeled_schema import BprLabeledSchema


bpr_scrapping_bp = Blueprint('bpr_scrapping', __name__, url_prefix='/bpr_scrapping')

@bpr_scrapping_bp.before_request
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

@bpr_scrapping_bp.route('/upload', methods=['POST'])
def upload_bpr_scrapping():
    """
    Upload and process BPR Scrapping CSV file
    """
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
            
        db = next(get_db())
        result = process_bpr_scrapping(db, file)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@bpr_scrapping_bp.route('/', methods=['GET'])
def get_all():
    """
    Get all BPR Scrapping records with pagination
    """
    try:
        # Get and validate pagination parameters
        try:
            page = request.args.get('page', default=1, type=int)
            per_page = request.args.get('per_page', default=10, type=int)
            if page < 1:
                return jsonify({"status": "error", "message": "Page number must be greater than 0"}), 400
            if per_page < 1:
                return jsonify({"status": "error", "message": "Items per page must be greater than 0"}), 400
        except ValueError as e:
            return jsonify({"status": "error", "message": "Invalid pagination parameters"}), 400

        print(f"Fetching page {page} with {per_page} items per page")  # Debug log
        
        # Get database session
        try:
            db = next(get_db())
        except Exception as e:
            print(f"Database session error: {str(e)}")  # Debug log
            return jsonify({"status": "error", "message": "Database connection error"}), 500
        
        # Get paginated data
        try:
            paginated_data = get_all_bpr_scrapping(db, page=page, per_page=per_page)
            print(f"Retrieved {len(paginated_data.get('results', []))} records")  # Debug log
        except Exception as e:
            print(f"Pagination error: {str(e)}")  # Debug log
            return jsonify({"status": "error", "message": f"Error fetching data: {str(e)}"}), 500
        
        # Serialize data
        try:
            schema = BprScrappingSchema(many=True)
            paginated_data['results'] = schema.dump(paginated_data['results'])
            print("Data serialization successful")  # Debug log
        except Exception as e:
            print(f"Serialization error: {str(e)}")  # Debug log
            return jsonify({"status": "error", "message": "Error processing data"}), 500
        
        return jsonify(paginated_data), 200
        
    except Exception as e:
        print(f"Unexpected error in get_all: {str(e)}")  # Debug log
        return jsonify({
            "status": "error", 
            "message": f"Internal server error: {str(e)}"
        }), 500

@bpr_scrapping_bp.route('/<int:bpr_id>', methods=['GET'])
def get_detail(bpr_id: int):
    """
    Get BPR Scrapping detail by ID
    """
    try:
        db = next(get_db())
        bpr_scrapping = get_bpr_scrapping_detail(db, bpr_id)
        
        if not bpr_scrapping:
            return jsonify({
                "status": "error",
                "message": f"BPR Scrapping with ID {bpr_id} not found"
            }), 404
            
        schema = BprScrappingSchema()
        result = schema.dump(bpr_scrapping)
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@bpr_scrapping_bp.route('/labeled', methods=['GET'])
def get_all_labeled():
    """
    Get all BPR Scrapping records with pagination
    """
    try:
        # Get and validate pagination parameters
        try:
            page = request.args.get('page', default=1, type=int)
            per_page = request.args.get('per_page', default=10, type=int)
            if page < 1:
                return jsonify({"status": "error", "message": "Page number must be greater than 0"}), 400
            if per_page < 1:
                return jsonify({"status": "error", "message": "Items per page must be greater than 0"}), 400
        except ValueError as e:
            return jsonify({"status": "error", "message": "Invalid pagination parameters"}), 400

        print(f"Fetching page {page} with {per_page} items per page")  # Debug log
        
        # Get database session
        try:
            db = next(get_db())
        except Exception as e:
            print(f"Database session error: {str(e)}")  # Debug log
            return jsonify({"status": "error", "message": "Database connection error"}), 500
        
        # Get paginated data
        try:
            paginated_data = get_all_bpr_labeled(db, page=page, per_page=per_page)
            print(paginated_data.get('results', []))
            print(f"Retrieved {len(paginated_data.get('results', []))} records")  # Debug log
        except Exception as e:
            print(f"Pagination error: {str(e)}")  # Debug log
            return jsonify({"status": "error", "message": f"Error fetching data: {str(e)}"}), 500
        
        # Serialize data
        try:
            schema = BprLabeledSchema(many=True)
            paginated_data['results'] = schema.dump(paginated_data['results'])
            print("Data serialization successful")  # Debug log
        except Exception as e:
            print(f"Serialization error: {str(e)}")  # Debug log
            return jsonify({"status": "error", "message": "Error processing data"}), 500
        
        return jsonify(paginated_data), 200
        
    except Exception as e:
        print(f"Unexpected error in get_all: {str(e)}")  # Debug log
        return jsonify({
            "status": "error", 
            "message": f"Internal server error: {str(e)}"
        }), 500

@bpr_scrapping_bp.route('/labeled/<int:bpr_id>', methods=['GET'])
def get_detail_labeled(bpr_id: int):
    """
    Get BPR Scrapping detail by ID
    """
    try:
        db = next(get_db())
        bpr_scrapping = get_bpr_labeled_detail(db, bpr_id)
        
        if not bpr_scrapping:
            return jsonify({
                "status": "error",
                "message": f"BPR Scrapping with ID {bpr_id} not found"
            }), 404
            
        schema = BprLabeledSchema()
        result = schema.dump(bpr_scrapping)
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@bpr_scrapping_bp.route('/start-scrapping', methods=['GET'])
def start_scrapping():
    try:
        thread_scrapping()

        today_str = datetime.now().strftime('%Y%m%d')
        filename = f"data{today_str}.csv"
        file_path = os.path.join('asset/bpr_scrapping/', filename)

        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": f"File {filename} tidak ditemukan"}), 404

        db = next(get_db())
        with open(file_path, 'rb') as f:
            result = process_bpr_scrapping(db, f)


        return jsonify({
            "status": "success",
            "message": "Scraping and upload completed",
            "upload_result": result
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": e}), 500