import os
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from datetime import datetime
from utils.pagination import paginate
from object.models import BprScrapping, BprLainnya, RAC, BprLabeled
from csv_to_db.csv_parser import parse_bpr_scrapping_csv
from csv_to_db.xlsx_parser import parse_bpr_lainnya_xlsx, parse_rac_xlsx

UPLOAD_FOLDER = {
    'bpr_scrapping': "asset/bpr_scrapping",
    'bpr_lainnya': "asset/bpr_lainnya",
    'rac': "asset/rac"
}
ALLOWED_EXTENSIONS_CSV = {'csv'}
ALLOWED_EXTENSIONS_XLSX = {'xlsx'}

def allowed_file_csv(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_CSV

def allowed_file_xlsx(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_XLSX

def ensure_upload_folders():
    """Ensure all upload folders exist"""
    for folder in UPLOAD_FOLDER.values():
        if not os.path.exists(folder):
            os.makedirs(folder)

def process_bpr_scrapping(db: Session, file) -> Dict[str, str]:
    """
    Process BPR Scrapping CSV file
    
    Args:
        db (Session): Database session
        file: Uploaded file object
        
    Returns:
        Dict[str, str]: Status message
        
    Raises:
        ValueError: If file processing fails
    """
    # if not allowed_file_csv(file.filename):
    #     raise ValueError("Invalid file type. Only CSV files are allowed.")
    
    ensure_upload_folders()
    print("FILEE ",file)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = file.name
    
    try:
        # file.save(file_path)
        data_list = parse_bpr_scrapping_csv(file_path)

        for data in data_list:
            # print("DATAA: ", data)
            status=cek_kesehatan_bpr(db,data['npl_net'], data['laba_tahun_lalu'], data['laba_saat_ini'], data['kap'], data['kpmm'], data['asset_saat_ini'], data['roa'], data['bopo'])
            print(status)
            bpr_scrapping = BprScrapping(**data)
            bpr_labeled = BprLabeled(**data, status=status)
            db.add(bpr_scrapping)
            db.add(bpr_labeled)
        
        db.commit()
        return {"status": "success", "message": "File bpr_scrapping.csv uploaded and data saved."}
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error processing BPR Scrapping file: {str(e)}")
    finally:
        pass  # Keep the file in the folder

def process_bpr_lainnya(db: Session, file) -> Dict[str, str]:
    """
    Process BPR Lainnya XLSX file
    
    Args:
        db (Session): Database session
        file: Uploaded file object
        
    Returns:
        Dict[str, str]: Status message
        
    Raises:
        ValueError: If file processing fails
    """
    if not allowed_file_xlsx(file.filename):
        raise ValueError("Invalid file type. Only XLSX files are allowed.")
    
    ensure_upload_folders()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER['bpr_lainnya'], filename)
    
    try:
        file.save(file_path)
        data_list = parse_bpr_lainnya_xlsx(file_path)
        
        for data in data_list:
            bpr_lainnya = BprLainnya(**data)
            db.add(bpr_lainnya)
        
        db.commit()
        return {"status": "success", "message": "File bpr_lainnya.xlsx uploaded and data saved."}
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error processing BPR Lainnya file: {str(e)}")
    finally:
        pass  # Keep the file in the folder

def process_rac_data(db: Session, file) -> Dict[str, str]:
    """
    Process D entity XLSX file
    
    Args:
        db (Session): Database session
        file: Uploaded file object
        
    Returns:
        Dict[str, str]: Status message
        
    Raises:
        ValueError: If file processing fails
    """
    if not allowed_file_xlsx(file.filename):
        raise ValueError("Invalid file type. Only XLSX files are allowed.")
    
    ensure_upload_folders()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER['rac'], filename)
    
    try:
        file.save(file_path)
        data_list = parse_rac_xlsx(file_path)
        
        for data in data_list:
            rac_entity = RAC(**data)
            db.add(rac_entity)
        
        db.commit()
        return {"status": "success", "message": "RAC entity data saved successfully."}
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error processing RAC entity file: {str(e)}")
    finally:
        pass  # Keep the file in the folder

def cek_kesehatan_bpr(db, npl, laba_sebelum, laba_sekarang, kap, kpmm, asset, roa, bopo) -> str:
    total_skor = 0
    rac_entity = get_rac_detail(db, 1)

    if npl < rac_entity.npl_net:
        total_skor += 10

    if laba_sebelum >= rac_entity.laba_sebelum:
        total_skor += 10

    if laba_sekarang >= rac_entity.laba_sekarang:
        total_skor += 10

    if kap < rac_entity.kap: 
        total_skor += 10

    if kpmm >= rac_entity.kpmm:
        total_skor += 10

    if asset >= rac_entity.asset:
        total_skor += 10

    if roa >= rac_entity.roa:
        total_skor += 10

    if bopo < rac_entity.bopo:
        total_skor += 10

    if total_skor >= 80:
        return "SEHAT"
    else:
        return "TIDAK SEHAT"


# Query functions
def get_all_bpr_scrapping(db: Session, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    query = db.query(BprScrapping)
    return paginate(query, page=page, per_page=per_page)

def get_bpr_scrapping_detail(db: Session, bpr_id: int) -> Optional[BprScrapping]:
    return db.query(BprScrapping).filter(BprScrapping.id == bpr_id).first()

def get_all_bpr_labeled(db: Session, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    query = db.query(BprLabeled)
    print(query)
    return paginate(query, page=page, per_page=per_page)

def get_bpr_labeled_detail(db: Session, bpr_id: int) -> Optional[BprLabeled]:
    return db.query(BprLabeled).filter(BprLabeled.id == bpr_id).first()

def get_all_bpr_lainnya(db: Session, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    query = db.query(BprLainnya)
    return paginate(query, page=page, per_page=per_page)

def get_bpr_lainnya_detail(db: Session, bpr_id: int) -> Optional[BprLainnya]:
    return db.query(BprLainnya).filter(BprLainnya.id == bpr_id).first()

def get_all_rac(db: Session, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    query = db.query(RAC)
    return paginate(query, page=page, per_page=per_page)

def get_rac_detail(db: Session, rac_id: int) -> Optional[RAC]:
    return db.query(RAC).filter(RAC.id == rac_id).first()

