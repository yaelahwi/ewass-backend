from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class BprScrapping(Base):
    __tablename__ = "bpr_scrapping"
    
    id = Column(Integer, primary_key=True, index=True)
    waktu_diambil = Column(DateTime, nullable=False, default=datetime.utcnow)
    tahun = Column(Integer, nullable=False)
    bulan = Column(String, nullable=False)
    nama_provinsi = Column(String, nullable=False)
    nama_kota = Column(String, nullable=False)
    sandi = Column(String, nullable=False)
    nama = Column(String, nullable=False)
    asset = Column(Float, nullable=False)
    kyd = Column(Float, nullable=False)
    total_hutang = Column(Float, nullable=False)
    laba_tahun_lalu = Column(Float, nullable=False)
    laba_saat_ini = Column(Float, nullable=False)
    npl_net = Column(Float, nullable=False)
    kpmm = Column(Float, nullable=False)
    ldr = Column(Float, nullable=False)
    roa = Column(Float, nullable=False)
    kap = Column(Float, nullable=False)
    ppap = Column(Float, nullable=False)
    bopo = Column(Float, nullable=False)
    cr = Column(Float, nullable=False)
    direksi = Column(String, nullable=False)
    dewan_komisaris = Column(String, nullable=False)

    def __repr__(self):
        return f"<BprScrapping(id={self.id}, nama={self.nama})>"

class BprLainnya(Base):
    __tablename__ = "bpr_lainnya"
    
    id = Column(Integer, primary_key=True, index=True)
    sandi = Column(String, nullable=False, unique=True)
    nama_bpr = Column(String, nullable=False)
    alamat_bpr = Column(String, nullable=False)
    kota_kabupaten = Column(String, nullable=False)
    provinsi = Column(String, nullable=False)
    no_telepon = Column(String, nullable=False)
    email = Column(String, nullable=False)
    wilayah_kerja_ojk = Column(String, nullable=False)

    def __repr__(self):
        return f"<BprLainnya(id={self.id}, nama_bpr={self.nama_bpr})>"

class D(Base):
    __tablename__ = "d"
    
    id = Column(Integer, primary_key=True, index=True)
    npl_nett = Column(Float, nullable=False)
    laba_tahun = Column(Float, nullable=False)
    laba_bulan = Column(Float, nullable=False)
    kap = Column(Float, nullable=False)
    kpmm = Column(Float, nullable=False)
    asset = Column(Float, nullable=False)
    roa = Column(Float, nullable=False)
    bopo = Column(Float, nullable=False)

    def __repr__(self):
        return f"<D(id={self.id}, npl_nett={self.npl_nett})>"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    nama = Column(String, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
