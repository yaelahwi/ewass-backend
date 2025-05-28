from database import SessionLocal, Base, engine
from object.models import BprScrapping
from datetime import datetime
import random

# Create tables
Base.metadata.create_all(bind=engine)

# Sample data
provinces = ['Jawa Barat', 'Jawa Tengah', 'Jawa Timur']
cities = ['Bandung', 'Semarang', 'Surabaya']
months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

def create_test_data():
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(BprScrapping).count() > 0:
            print("Test data already exists")
            return

        # Create 50 test records
        for i in range(50):
            bpr = BprScrapping(
                waktu_diambil=datetime.utcnow(),
                tahun=2023,
                bulan=random.choice(months),
                nama_provinsi=random.choice(provinces),
                nama_kota=random.choice(cities),
                sandi=f"BPR{i+1:03d}",
                nama=f"BPR Test {i+1}",
                asset=random.uniform(1000000, 10000000),
                kyd=random.uniform(500000, 5000000),
                total_hutang=random.uniform(400000, 4000000),
                laba_tahun_lalu=random.uniform(10000, 100000),
                laba_saat_ini=random.uniform(15000, 150000),
                npl_net=random.uniform(0.5, 5.0),
                kpmm=random.uniform(8.0, 20.0),
                ldr=random.uniform(70.0, 90.0),
                roa=random.uniform(0.5, 4.0),
                kap=random.uniform(70.0, 95.0),
                ppap=random.uniform(80.0, 100.0),
                bopo=random.uniform(60.0, 90.0),
                cr=random.uniform(15.0, 30.0),
                direksi="John Doe, Jane Smith",
                dewan_komisaris="Alice Johnson, Bob Wilson"
            )
            db.add(bpr)
        
        db.commit()
        print("Successfully created 50 test records")
        
    except Exception as e:
        print(f"Error creating test data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
