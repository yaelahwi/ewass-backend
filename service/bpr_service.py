import os
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from datetime import datetime

from object.models import BprScrapping, BprLainnya, D
from csv_to_db.csv_parser import parse_bpr_scrapping_csv
from csv_to_db.xlsx_parser import parse_bpr_lainnya_xlsx, parse_d_xlsx

UPLOAD_FOLDER = {
    'bpr_scrapping': "asset/bpr_scrapping",
    'bpr_lainnya': "asset/bpr_lainnya",
    'd': "asset/d"
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
    if not allowed_file_csv(file.filename):
        raise ValueError("Invalid file type. Only CSV files are allowed.")
    
    ensure_upload_folders()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER['bpr_scrapping'], filename)
    
    try:
        file.save(file_path)
        data_list = parse_bpr_scrapping_csv(file_path)
        
        for data in data_list:
            bpr_scrapping = BprScrapping(**data)
            db.add(bpr_scrapping)
        
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

def process_d_data(db: Session, file) -> Dict[str, str]:
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
    file_path = os.path.join(UPLOAD_FOLDER['d'], filename)
    
    try:
        file.save(file_path)
        data_list = parse_d_xlsx(file_path)
        
        for data in data_list:
            d_entity = D(**data)
            db.add(d_entity)
        
        db.commit()
        return {"status": "success", "message": "D entity data saved successfully."}
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error processing D entity file: {str(e)}")
    finally:
        pass  # Keep the file in the folder

# Query functions
def get_all_bpr_scrapping(db: Session, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    from utils.pagination import paginate
    query = db.query(BprScrapping)
    return paginate(query, page=page, per_page=per_page)

def get_bpr_scrapping_detail(db: Session, bpr_id: int) -> Optional[BprScrapping]:
    return db.query(BprScrapping).filter(BprScrapping.id == bpr_id).first()

def get_all_bpr_lainnya(db: Session, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    from utils.pagination import paginate
    query = db.query(BprLainnya)
    return paginate(query, page=page, per_page=per_page)

def get_bpr_lainnya_detail(db: Session, bpr_id: int) -> Optional[BprLainnya]:
    return db.query(BprLainnya).filter(BprLainnya.id == bpr_id).first()

def get_all_d(db: Session, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    from utils.pagination import paginate
    query = db.query(D)
    return paginate(query, page=page, per_page=per_page)

def get_d_detail(db: Session, d_id: int) -> Optional[D]:
    return db.query(D).filter(D.id == d_id).first()
