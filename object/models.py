from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid

class BprScrapping(Base):
    __tablename__ = "bpr_scrapping"
    
    id = Column(Integer, primary_key=True, index=True)
    waktu_diambil = Column(DateTime, nullable=False, default=datetime.now)
    tahun = Column(Integer, nullable=False)
    bulan = Column(String, nullable=False)
    nama_provinsi = Column(String, nullable=False)
    nama_kota = Column(String, nullable=False)
    sandi = Column(String, nullable=False)
    nama = Column(String, nullable=False)
    asset_saat_ini = Column(Float, nullable=False)
    asset_tahun_lalu = Column(Float, nullable=False)
    kyd_saat_ini = Column(Float, nullable=False)
    kyd_tahun_lalu = Column(Float, nullable=False)
    hutang_saat_ini = Column(Float, nullable=False)
    hutang_tahun_lalu = Column(Float, nullable=False)
    laba_tahun_tahun_lalu_saat_ini = Column(Float, nullable=False)
    laba_tahun_tahun_lalu_sebelumnya = Column(Float, nullable=False)
    laba_saat_ini = Column(Float, nullable=False)
    laba_tahun_lalu = Column(Float, nullable=False)
    tabungan_saat_ini = Column(Float, nullable=False)
    tabungan_tahun_lalu = Column(Float, nullable=False)
    deposito_saat_ini = Column(Float, nullable=False)
    deposito_tahun_lalu = Column(Float, nullable=False)
    penempatan_pada_bank_lain_saat_ini = Column(Float, nullable=False)
    penempatan_pada_bank_lain_tahun_lalu = Column(Float, nullable=False)
    total_ekuitas = Column(Float, nullable=False)
    total_ekuitas_tahun_lalu = Column(Float, nullable=False)
    simpanan_dari_bank_lain_saat_ini = Column(Float, nullable=False)
    simpanan_dari_bank_lain_tahun_lalu = Column(Float, nullable=False)
    laba_desember_tahun_sebelum = Column(Float, nullable=False)
    npl_net = Column(Float, nullable=False)
    kpmm = Column(Float, nullable=False)
    ldr = Column(Float, nullable=False)
    roa = Column(Float, nullable=False)
    kap = Column(Float, nullable=False)
    ppap = Column(Float, nullable=False)
    bopo = Column(Float, nullable=False)
    nim = Column(Float, nullable=False)
    cr = Column(Float, nullable=False)
    direksi = Column(String, nullable=True)
    dewan_komisaris = Column(String, nullable=True)

    def __repr__(self):
        return f"<BprScrapping(id={self.id}, nama={self.nama})>"

class BprLabeled(Base):
    __tablename__ = "bpr_labeled"
    
    id = Column(Integer, primary_key=True, index=True)
    waktu_diambil = Column(DateTime, nullable=False, default=datetime.now)
    tahun = Column(Integer, nullable=False)
    bulan = Column(String, nullable=False)
    nama_provinsi = Column(String, nullable=False)
    nama_kota = Column(String, nullable=False)
    sandi = Column(String, nullable=False)
    nama = Column(String, nullable=False)
    asset_saat_ini = Column(Float, nullable=False)
    asset_tahun_lalu = Column(Float, nullable=False)
    kyd_saat_ini = Column(Float, nullable=False)
    kyd_tahun_lalu = Column(Float, nullable=False)
    hutang_saat_ini = Column(Float, nullable=False)
    hutang_tahun_lalu = Column(Float, nullable=False)
    laba_tahun_tahun_lalu_saat_ini = Column(Float, nullable=False)
    laba_tahun_tahun_lalu_sebelumnya = Column(Float, nullable=False)
    laba_saat_ini = Column(Float, nullable=False)
    laba_tahun_lalu = Column(Float, nullable=False)
    tabungan_saat_ini = Column(Float, nullable=False)
    tabungan_tahun_lalu = Column(Float, nullable=False)
    deposito_saat_ini = Column(Float, nullable=False)
    deposito_tahun_lalu = Column(Float, nullable=False)
    penempatan_pada_bank_lain_saat_ini = Column(Float, nullable=False)
    penempatan_pada_bank_lain_tahun_lalu = Column(Float, nullable=False)
    total_ekuitas = Column(Float, nullable=False)
    total_ekuitas_tahun_lalu = Column(Float, nullable=False)
    simpanan_dari_bank_lain_saat_ini = Column(Float, nullable=False)
    simpanan_dari_bank_lain_tahun_lalu = Column(Float, nullable=False)
    laba_desember_tahun_sebelum = Column(Float, nullable=False)
    npl_net = Column(Float, nullable=False)
    kpmm = Column(Float, nullable=False)
    ldr = Column(Float, nullable=False)
    roa = Column(Float, nullable=False)
    kap = Column(Float, nullable=False)
    ppap = Column(Float, nullable=False)
    bopo = Column(Float, nullable=False)
    nim = Column(Float, nullable=False)
    cr = Column(Float, nullable=False)
    direksi = Column(String, nullable=True)
    dewan_komisaris = Column(String, nullable=True)
    status = Column(String, nullable=False)

    def __repr__(self):
        return f"<BprLabeling(id={self.id}, nama={self.nama})>"

class BprLainnya(Base):
    __tablename__ = "bpr_lainnya"
    
    id = Column(Integer, primary_key=True, index=True)
    sandi = Column(String, nullable=False, unique=True)
    nama_bpr = Column(String, nullable=False)
    alamat_bpr = Column(String, nullable=True)
    kota_kabupaten = Column(String, nullable=False)
    provinsi = Column(String, nullable=False)
    no_telepon = Column(String, nullable=True)
    email = Column(String, nullable=True)
    wilayah_kerja_ojk = Column(String, nullable=True)

    def __repr__(self):
        return f"<BprLainnya(id={self.id}, nama_bpr={self.nama_bpr})>"

class RAC(Base):
    __tablename__ = "rac"
    
    id = Column(Integer, primary_key=True, index=True)
    npl_net = Column(Float, nullable=False)
    laba_sebelum = Column(Float, nullable=False)
    laba_sekarang = Column(Float, nullable=False)
    kap = Column(Float, nullable=False)
    kpmm = Column(Float, nullable=False)
    asset = Column(Float, nullable=False)
    roa = Column(Float, nullable=False)
    bopo = Column(Float, nullable=False)

    def __repr__(self):
        return f"<RAC(id={self.id}, npl_net={self.npl_net})>"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, nullable=False, unique=True, default=uuid.uuid4().hex) #
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    nama = Column(String, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, nama={self.nama})>"

class FetchHistory(Base):
    __tablename__ = 'fetch_history'

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.now())
    end_time = Column(DateTime, nullable=True)
    periode = Column(String)
    status = Column(String)
    user = Column(String)

    def __repr__(self):
        return f"<FetchHistory(id={self.id}, periode={self.periode})>"