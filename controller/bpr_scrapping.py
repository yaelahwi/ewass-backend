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
    get_bpr_labeled_detail,
    get_top_bpr_by_asset,
    get_top_bpr_by_npl,
    get_filtered_bpr_list,
    count_total_bpr,
    count_bpr_sehat,
    count_bpr_tidak_sehat,
    get_bpr_asset,
    get_bpr_laba,
    get_bpr_rac_lain
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
        file_path = os.path.join('asset/bpr_scrapping/', file.filename)   
        db = next(get_db())
        print("satu")
        result = process_bpr_scrapping(db, file_path)

        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500


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

        folder = 'asset/bpr_scrapping/'
        files = [f for f in os.listdir(folder) if f.endswith('.csv')]
        filename = files[-1]
        file_path = os.path.join(folder, filename)

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
    
@bpr_scrapping_bp.route('/top-asset', methods=['GET'])
def top_5_bpr_asset():
    db = next(get_db())
    try:
        top_bpr = get_top_bpr_by_asset(db)

        data = []
        for bpr in top_bpr:
            data.append({
                "nama_bpr": bpr[0],
                "asset_saat_ini": bpr[1],
                "kota_kabupaten": bpr[2]
            })

        return jsonify({
            "status": "success",
            "data": data
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@bpr_scrapping_bp.route('/top-npl', methods=['GET'])
def top_5_bpr_npl():
    db = next(get_db())
    try:
        top_bpr = get_top_bpr_by_npl(db)

        data = []
        for bpr in top_bpr:
            data.append({
                "nama_bpr": bpr[0],
                "npl": bpr[1],
                "kota_kabupaten": bpr[2]
            })

        return jsonify({
            "status": "success",
            "data": data
        }), 200


    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@bpr_scrapping_bp.route('/', methods=['GET'])
def get_all_filter():
    db = next(get_db())
    try:
        # Ambil parameter dari query string
        tahun = request.args.get('tahun', type=int)
        bulan = request.args.get('bulan')
        nama_provinsi = request.args.get('nama_provinsi')
        nama_kota = request.args.get('nama_kota')
        nama = request.args.get('nama')
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)

        # Panggil service
        bpr_list, total = get_filtered_bpr_list(
            db,
            tahun=tahun,
            bulan=bulan,
            nama_provinsi=nama_provinsi,
            nama_kota=nama_kota,
            nama=nama,
            page=page, per_page=per_page
        )

        # Format hasil
        result = [{
            "sandi": bpr.sandi,
            "nama_bpr": bpr.nama,
            "asset": bpr.asset_saat_ini,
            "laba_desember_tahun_sebelum": bpr.laba_desember_tahun_sebelum,
            "laba_saat_ini": bpr.laba_saat_ini,
            "npl_net": bpr.npl_net,
            "kpmm": bpr.kpmm,
            "roa": bpr.roa,
            "kap": bpr.kap,
            "bopo": bpr.bopo,
            "result": bpr.status
        } for bpr in bpr_list]

        return jsonify({
            "status": "success",
            "page": page,
            "per_page": per_page,
            "total": total,
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    

@bpr_scrapping_bp.route('/count_total_bpr', methods=['GET'])
def route_count_total_bpr():
    db = next(get_db())

    try:
        total = count_total_bpr(db)
        return jsonify({"status": "success", "total_bpr": total}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_scrapping_bp.route('/count_bpr_sehat', methods=['GET'])
def route_count_bpr_sehat():
    db = next(get_db())
    try:
        total = count_bpr_sehat(db)
        return jsonify({"status": "success", "total_bpr_sehat": total}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_scrapping_bp.route('/count_bpr_tidak_sehat', methods=['GET'])
def route_count_bpr_tidak_sehat():
    db = next(get_db())
    try:
        total = count_bpr_tidak_sehat(db)
        return jsonify({"status": "success", "total_bpr_tidak_sehat": total}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_scrapping_bp.route('/get_bpr_asset/<string:bpr_id>', methods=['GET'])
def route_get_bpr_asset(bpr_id):
    db = next(get_db())
    try:
        result = get_bpr_asset(db, bpr_id)
        data = [
            {
                "tahun": row[0],
                "bulan": row[1],
                "asset_saat_ini": row[2]
            } for row in result
        ]
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_scrapping_bp.route('/get_bpr_laba/<string:bpr_id>', methods=['GET'])
def route_get_bpr_laba(bpr_id):
    db = next(get_db())
    try:
        result = get_bpr_laba(db, bpr_id)
        data = [
            {
                "tahun": row[0],
                "bulan": row[1],
                "laba_saat_ini": row[2]
            } for row in result
        ]
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_scrapping_bp.route('/get_bpr_rac_lain/<string:bpr_id>', methods=['GET'])
def route_get_bpr_rac_lain(bpr_id):
    db = next(get_db())
    try:
        result = get_bpr_rac_lain(db, bpr_id)
        data = [
            {
                "tahun": row[0],
                "bulan": row[1],
                "npl_net": row[2],
                "kap": row[3],
                "kpmm": row[4],
                "roa": row[5],
                "bopo": row[6]
            } for row in result
        ]
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
