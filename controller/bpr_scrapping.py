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
    get_bpr_rac_lain,
    get_fetch_history_all,
    get_fetch_history_id,
    delete_bpr_labeled_by_periode
)
from service.scrapping_service import thread_scrapping
from dto.bpr_scrapping_schema import BprScrappingSchema
from dto.bpr_labeled_schema import BprLabeledSchema
from dto.fetch_history_schema import FetchHistorySchema
from threading import Lock



bpr_scrapping_bp = Blueprint('bpr_scrapping', __name__, url_prefix='/bpr_scrapping')
scraping_lock = Lock()
is_scraping = False

@bpr_scrapping_bp.before_request
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

        with get_db() as db:
            result = process_bpr_scrapping(db, file_path)

            return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@bpr_scrapping_bp.route('/<string:bpr_id>', methods=['GET'])
def get_detail(bpr_id: str):
    """
    Get BPR Scrapping detail by ID
    """
    try:
        with get_db() as db:
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
        finally:
            try:
                next(get_db())  # ensure db.close() runs
            except StopIteration:
                pass
        
        return jsonify(paginated_data), 200
        
    except Exception as e:
        print(f"Unexpected error in get_all: {str(e)}")  # Debug log
        return jsonify({
            "status": "error", 
            "message": f"Internal server error: {str(e)}"
        }), 500

@bpr_scrapping_bp.route('/labeled/<string:bpr_id>', methods=['GET'])
def get_detail_labeled(bpr_id: str):
    """
    Get BPR Scrapping detail by ID
    """
    try:
        with get_db() as db:
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
    global is_scraping
    try:
        # Jika sedang scraping, tolak request baru
        if is_scraping:
            return jsonify({
                "status": "error",
                "message": "Scraping is already in progress. Please wait until it completes."
            }), 429  # 429 Too Many Requests

        with scraping_lock:
            is_scraping = True
    
            months = [
                {"value": "3", "text": "Maret", "index": 0},
                {"value": "6", "text": "Juni", "index": 1},
                {"value": "9", "text": "September", "index": 2},
                {"value": "12", "text": "Desember", "index": 3}
            ]
            bulan = months[(datetime.now().month//3)-1]['text']
            tahun = datetime.now().year

            with get_db() as db:
                cek_duplicate = get_filtered_bpr_list(db,
                    tahun=tahun,
                    bulan=bulan,
                    nama_provinsi=None,
                    nama_kota=None,
                    nama=None,
                    status=None,
                    page=1, 
                    per_page=1)
                print("CEK DUPE", cek_duplicate)
                if cek_duplicate:
                    delete_bpr_labeled_by_periode(db, tahun, bulan)
                    print("DIHAPUS")

            thread_scrapping()

            folder = 'asset/bpr_scrapping/'
            files = [f for f in os.listdir(folder) if f.endswith('.csv')]
            filename = files[-1]
            file_path = os.path.join(folder, filename)

            if not os.path.exists(file_path):
                return jsonify({"status": "error", "message": f"File {filename} tidak ditemukan"}), 404
            
            
            with get_db() as db:
                with open(file_path, 'rb') as f:
                    result = process_bpr_scrapping(db, f)


                return jsonify({
                    "status": "success",
                    "message": "Scraping and upload completed",
                    "upload_result": result
                }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": e}), 500
    finally:
        is_scraping = False
    
@bpr_scrapping_bp.route('/top-asset', methods=['GET'])
def top_5_bpr_asset():
    try:
        with get_db() as db:
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
    try:
        with get_db() as db:
            top_bpr = get_top_bpr_by_npl(db)

            data = []
            for bpr in top_bpr:
                data.append({
                    "nama_bpr": bpr[0],
                    "npl": "{:.2f}".format(bpr[1]),
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

@bpr_scrapping_bp.route('/get_all_bpr', methods=['GET'])
def get_all_filter():
    try:
        with get_db() as db:
            tahun = request.args.get('tahun', type=int)
            bulan = request.args.get('bulan')
            nama_provinsi = request.args.get('nama_provinsi')
            nama_kota = request.args.get('nama_kota')
            nama = request.args.get('nama_bpr')
            status = request.args.get('status')
            page = request.args.get('page', default=1, type=int)
            per_page = request.args.get('per_page', default=10, type=int)

            bpr_list, total = get_filtered_bpr_list(
                db,
                tahun=tahun,
                bulan=bulan,
                nama_provinsi=nama_provinsi,
                nama_kota=nama_kota,
                nama=nama,
                status=status,
                page=page, 
                per_page=per_page
            )

            # Format hasil
            result = [{
                "sandi": bpr.sandi,
                "nama_bpr": bpr.nama,
                "periode": " ".join([bpr.bulan, str(bpr.tahun)]),
                "asset": bpr.asset_saat_ini,
                "laba_desember_tahun_sebelum": bpr.laba_desember_tahun_sebelum,
                "laba_saat_ini": bpr.laba_saat_ini,
                "npl_net": "{:.2f}".format(bpr.npl_net),
                "kpmm": "{:.2f}".format(bpr.kpmm),
                "roa": "{:.2f}".format(bpr.roa),
                "kap": "{:.2f}".format(bpr.kap),
                "bopo": "{:.2f}".format(bpr.bopo),
                "status": bpr.status
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
    try:
        with get_db() as db:
            total = count_total_bpr(db)
            return jsonify({"status": "success", "total_bpr": total}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_scrapping_bp.route('/count_bpr_sehat', methods=['GET'])
def route_count_bpr_sehat():
    try:
        with get_db() as db:
            total = count_bpr_sehat(db)
            return jsonify({"status": "success", "total_bpr_sehat": total}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_scrapping_bp.route('/count_bpr_tidak_sehat', methods=['GET'])
def route_count_bpr_tidak_sehat():
    try:
        with get_db() as db:
            total = count_bpr_tidak_sehat(db)
            return jsonify({"status": "success", "total_bpr_tidak_sehat": total}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_scrapping_bp.route('/get_bpr_asset/<string:bpr_id>', methods=['GET'])
def route_get_bpr_asset(bpr_id):
    try:
        with get_db() as db:
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
    try:
        with get_db() as db:
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
    try:
        with get_db() as db:
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
    
@bpr_scrapping_bp.get("/fetch_history_all")
def route_get_fetch_history_all():
    try:
        with get_db() as db:
            history = get_fetch_history_all(db)    
            formatted_history = []
            for record in history:
                formatted_history.append({
                    "No": record.id,
                    "start": record.start_time,
                    "end": record.end_time, # Format from fetch_time
                    "Periode Laporan": record.periode,
                    "Status": record.status,
                    "User": record.user
                })
            return formatted_history
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bpr_scrapping_bp.get("/fetch_history/<int:fetch_id>")
def route_get_fetch_history_id(fetch_id):
    try:
        with get_db() as db:
            history = get_fetch_history_id(db, fetch_id)    
            formatted_history = []
            for record in history:
                formatted_history.append({
                    "No": record.id,
                    "Date": record.fetch_date.strftime('%d-%b-%Y'), # Format from fetch_date
                    "Time": record.fetch_time.strftime('%H:%M:%S'), # Format from fetch_time
                    "Periode Laporan": record.periode,
                    "Status": record.status,
                    "User": record.user
                })
            return formatted_history
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
