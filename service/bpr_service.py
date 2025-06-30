import os
from typing import List, Dict, Any, Optional, Tuple
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from datetime import datetime
from utils.pagination import paginate
from sqlalchemy import func, distinct
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
    file_path = file.name #ini kalau abis scrapping langsung upload
    # file_path = file #ini kalau upload manual
    
    try:
        # file.save(file_path)
        data_list = parse_bpr_scrapping_csv(file_path)

        for data in data_list:
            status=cek_kesehatan_bpr(db,data['npl_net'], data['laba_desember_tahun_sebelum'], data['laba_saat_ini'], data['kap'], data['kpmm'], data['asset_saat_ini'], data['roa'], data['bopo'])
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

def cek_kesehatan_bpr(db, npl, laba_desember_tahun_sebelum, laba_sekarang, kap, kpmm, asset, roa, bopo) -> str:
    total_skor = 0
    rac_entity = get_rac_detail(db, 1)

    if npl < rac_entity.npl_net:
        total_skor += 10

    if laba_desember_tahun_sebelum >= rac_entity.laba_sebelum:
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
    return db.query(BprScrapping).filter(BprScrapping.sandi == bpr_id).first()

def get_all_bpr_labeled(db: Session, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    query = db.query(BprLabeled)
    return paginate(query, page=page, per_page=per_page)

def get_bpr_labeled_detail(db: Session, bpr_id: int) -> Optional[BprLabeled]:
    return db.query(BprLabeled).filter(BprLabeled.id == bpr_id).first()

def get_all_bpr_lainnya(db: Session, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    query = db.query(BprLainnya)
    return paginate(query, page=page, per_page=per_page)

def get_bpr_lainnya_detail(db: Session, bpr_id: int) -> Optional[BprLainnya]:
    return db.query(BprLainnya).filter(BprLainnya.id == bpr_id).first()

def get_all_rac(db: Session) -> Dict[str, Any]:
    query = db.query(RAC).all()
    return query

def get_rac_detail(db: Session, rac_id: int) -> Optional[RAC]:
    return db.query(RAC).filter(RAC.id == rac_id).first()

def get_bpr_plafon(db: Session, bpr_id: str) -> Optional[Tuple[Any, Any, Any, Any]]:
    tahun = datetime.now().year - 1

    kyd, tabungan, deposito, simpanan_bank_lain = db.query(
        BprLabeled.kyd_saat_ini,
        BprLabeled.tabungan_saat_ini,
        BprLabeled.deposito_saat_ini,
        BprLabeled.simpanan_dari_bank_lain_saat_ini
    ).filter(BprLabeled.sandi == bpr_id,
             BprLabeled.tahun == 2025,
             BprLabeled.bulan == 'Maret').first() #nanti ini diubah

    kebutuhan_dana = kyd/0.95
    dana_tersedia = tabungan + deposito + simpanan_bank_lain
    plafon = kebutuhan_dana - dana_tersedia
    return kyd, tabungan, deposito, simpanan_bank_lain, dana_tersedia, kebutuhan_dana, plafon

def get_top_bpr_by_asset (db: Session) -> Optional[Tuple[Any, Any, Any, Any]]:
    result = (db.query(BprLabeled.nama, BprLabeled.asset_saat_ini, BprLabeled.nama_kota)
              .filter(BprLabeled.asset_saat_ini != None, BprLabeled.tahun == datetime.now().year)
              .order_by(BprLabeled.asset_saat_ini.desc())
              .limit(5))
    return result

def get_top_bpr_by_npl (db: Session) -> Optional[Tuple[Any, Any, Any, Any]]:
    result = (db.query(BprLabeled.nama, BprLabeled.npl_net, BprLabeled.nama_kota)
              .filter(BprLabeled.npl_net != None, BprLabeled.tahun == datetime.now().year)
              .order_by(BprLabeled.npl_net.asc())
              .limit(5))
    return result

def get_filtered_bpr_list(
    db: Session,
    tahun: int,
    bulan: str,
    nama_provinsi: str,
    nama_kota: str,
    nama: str,
    page: int,
    per_page: int
) -> Tuple[List[BprLabeled], int]:
    query = db.query(BprLabeled)
    print(tahun)
    print(bulan)
    print(nama_provinsi)

    if tahun:
        query = query.filter(BprLabeled.tahun == tahun)
    if bulan:
        query = query.filter(BprLabeled.bulan == bulan)
    if nama_provinsi:
        query = query.filter(BprLabeled.nama_provinsi.ilike(f"%{nama_provinsi}%"))
    if nama_kota:
        query = query.filter(BprLabeled.nama_kota.ilike(f"%{nama_kota}%"))
    if nama:
        query = query.filter(BprLabeled.nama.ilike(f"%{nama}%"))

    # print(query)
    total = query.count()
    results = query.offset((page - 1) * per_page).limit(per_page).all()

    return results, total

def count_total_bpr(db: Session) -> int:
    return db.query(BprLabeled).filter(BprLabeled.tahun==2025, BprLabeled.bulan=='Maret').count()

def count_bpr_sehat(db: Session) -> int:
    return db.query(BprLabeled).filter(BprLabeled.tahun==2025, BprLabeled.bulan=='Maret', BprLabeled.status=='SEHAT').count()

def count_bpr_tidak_sehat(db: Session) -> int:
    return db.query(BprLabeled).filter(BprLabeled.tahun==2025, BprLabeled.bulan=='Maret', BprLabeled.status=='TIDAK SEHAT').count()

def count_total_provinsi(db: Session) -> int:
    return db.query(func.count(func.distinct(BprLainnya.provinsi))).scalar()

def get_all_provinsi(db: Session):
    results = db.query(distinct(BprLainnya.provinsi)).all()
    return [row[0] for row in results] 

def get_all_kota(db: Session):
    results = db.query(distinct(BprLainnya.kota_kabupaten)).all()
    return [row[0] for row in results] 

def get_all_nama_bpr(db: Session):
    results = db.query(distinct(BprLainnya.nama_bpr)).all()
    return [row[0] for row in results] 

def get_bpr_asset(db: Session, bpr_id: str):
    return db.query(BprLabeled.tahun, BprLabeled.bulan, BprLabeled.asset_saat_ini).filter(BprLabeled.sandi == bpr_id).all()

def get_bpr_laba(db: Session, bpr_id: str):
    return db.query(BprLabeled.tahun, BprLabeled.bulan, BprLabeled.laba_saat_ini).filter(BprLabeled.sandi == bpr_id).all()

def get_bpr_rac_lain(db: Session, bpr_id: str):
    return db.query(BprLabeled.tahun, BprLabeled.bulan, BprLabeled.npl_net, BprLabeled.kap, BprLabeled.kpmm, BprLabeled.roa, BprLabeled.bopo).filter(BprLabeled.sandi == bpr_id).all()


def update_rac_by_id(db: Session, update_data: dict) -> dict:
    rac = db.query(RAC).filter(RAC.id == 1).first()

    if not rac:
        raise ValueError("RAC not found")

    for key, value in update_data.items():
        if hasattr(rac, key):
            setattr(rac, key, value)

    db.commit()
    db.refresh(rac)

    return {
        "npl_net": rac.npl_net,
        "kap": rac.kap,
        "kpmm": rac.kpmm,
        "roa": rac.roa,
        "bopo": rac.bopo,
        "laba_sebelum": rac.laba_sebelum,
        "laba_sekarang": rac.laba_sekarang,
        "asset": rac.asset
    }