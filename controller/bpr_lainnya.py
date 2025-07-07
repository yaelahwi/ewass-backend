from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from database import get_db
from service.bpr_service import (
    process_bpr_lainnya,
    get_all_bpr_lainnya,
    get_bpr_lainnya_detail,
    get_bpr_plafon,
    count_total_provinsi,
    get_all_provinsi,
    get_all_kota,
    get_all_nama_bpr
)
from dto.bpr_lainnya_schema import BprLainnyaSchema

bpr_lainnya_bp = Blueprint('bpr_lainnya', __name__, url_prefix='/bpr_lainnya')

@bpr_lainnya_bp.before_request
def require_jwt():
    if request.method == 'OPTIONS':
        return '', 200
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
            
        with get_db() as db:
            result = process_bpr_lainnya(db, file)
            return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@bpr_lainnya_bp.route('/get_bpr_lainnya', methods=['GET'])
def get_all():
    """
    Get all BPR Lainnya records with pagination
    """
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        with get_db() as db:
            paginated_data = get_all_bpr_lainnya(db, page=page, per_page=per_page)
        
            schema = BprLainnyaSchema(many=True)
            paginated_data['results'] = schema.dump(paginated_data['results'])
        
            return jsonify(paginated_data), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@bpr_lainnya_bp.route('/get_detail/<string:bpr_id>', methods=['GET'])
def get_detail(bpr_id: str):
    """
    Get BPR Lainnya detail by ID
    """
    try:
        with get_db() as db:
            bpr_lainnya = get_bpr_lainnya_detail(db, bpr_id)
            print(bpr_lainnya)
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
        return jsonify({"status": "error", "message": e}), 500


@bpr_lainnya_bp.route('/plafon/<string:bpr_id>', methods=['GET'])
def get_bpr_potential_plafon(bpr_id: str):
    try:
        with get_db() as db:
            kyd, tabungan, deposito, simpanan_bank_lain,dana_tersedia, kebutuhan_dana, plafon = get_bpr_plafon(db, bpr_id)

            if kyd is None and tabungan is None and deposito is None and simpanan_bank_lain is None:
                return jsonify({
                    "status": "error",
                    "message": "Data tidak ditemukan"
                }), 404
        


            return jsonify({
                "status": "success",
                "data": {
                    "kyd_saat_ini": kyd,
                    "tabungan_saat_ini": tabungan,
                    "deposito_saat_ini": deposito,
                    "simpanan_dari_bank_lain_saat_ini": simpanan_bank_lain,
                    "dana_tersedia":dana_tersedia,
                    "kebutuhan_dana": kebutuhan_dana,
                    "plafon": plafon
                }
            }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@bpr_lainnya_bp.route('/count_total_provinsi', methods=['GET'])
def route_count_total_provinsi():
    try:
        with get_db() as db:
            total = count_total_provinsi(db)
            return jsonify({"status": "success", "total_provinsi": total}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_lainnya_bp.route('/get_all_provinsi', methods=['GET'])
def route_get_all_provinsi():
    try:
        with get_db() as db:
            result = get_all_provinsi(db)
            return jsonify({"status": "success", "provinsi": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_lainnya_bp.route('/get_all_kota', methods=['GET'])
def route_get_all_kota():
    try:
        with get_db() as db:
            provinsi = request.args.get('provinsi')
            
            result = get_all_kota(db, provinsi)
            return jsonify({"status": "success", "kota_kabupaten": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_lainnya_bp.route('/get_all_nama_bpr', methods=['GET'])
def route_get_all_nama_bpr():
    try:
        with get_db() as db:
            provinsi = request.args.get('provinsi')
            kota_kabupaten = request.args.get('kota_kabupaten')
            
            result = get_all_nama_bpr(db, provinsi, kota_kabupaten)
            return jsonify({"status": "success", "nama_bpr": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500