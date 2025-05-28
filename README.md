# BPR Data Management API

A Flask-based REST API for managing BPR (Bank Perkreditan Rakyat) data, including data from CSV/XLSX uploads and user management.

> **For detailed documentation, please refer to [Documentation](docs/documentation.md)**

## Project Structure

```
project_root/
│
├── asset/                # Temporary storage for uploaded CSV/XLSX files
├── controller/           # Flask Blueprints for API endpoints
├── csv_to_db/           # CSV/XLSX parsing logic
├── dto/                 # Data Transfer Object schemas
├── object/              # SQLAlchemy ORM models
├── service/            # Business logic layer
├── venv/               # Virtual environment
├── .env                # Environment variables
├── .gitignore         # Git ignore rules
├── database.py        # Database connection setup
├── main.py            # Application entry point
└── requirements.txt   # Project dependencies
```

## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
- Copy `.env.example` to `.env`
- Update the values in `.env` with your configuration

4. Initialize database:
- Create PostgreSQL database
- Update DATABASE_URL in .env
- Tables will be created automatically when running the application

## Running the Application

```bash
flask run
```

Or directly:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### BPR Scrapping
- `POST /bpr_scrapping/upload` - Upload BPR Scrapping CSV file
- `GET /bpr_scrapping/` - Get all BPR Scrapping records
- `GET /bpr_scrapping/<id>` - Get BPR Scrapping detail

### BPR Lainnya
- `POST /bpr_lainnya/upload` - Upload BPR Lainnya XLSX file
- `GET /bpr_lainnya/` - Get all BPR Lainnya records
- `GET /bpr_lainnya/<id>` - Get BPR Lainnya detail

### D Entity
- `POST /d/upload` - Upload D entity XLSX file
- `GET /d/` - Get all D entity records
- `GET /d/<id>` - Get D entity detail

### User Management
- `POST /user/register` - Register new user
- `POST /user/login` - User login
- `GET /user/` - Get all users
- `GET /user/<id>` - Get user detail

## File Upload Formats

### BPR Scrapping (CSV)
Required columns:
- tahun
- bulan
- nama_provinsi
- nama_kota
- sandi
- nama
- asset
- kyd
- total_hutang
- laba_tahun_lalu
- laba_saat_ini
- npl_net
- kpmm
- ldr
- roa
- kap
- ppap
- bopo
- cr
- direksi
- dewan_komisaris

### BPR Lainnya (XLSX)
Required columns:
- sandi
- nama_bpr
- alamat_bpr
- kota_kabupaten
- provinsi
- no_telepon
- email
- wilayah_kerja_ojk

### D Entity (XLSX)
Required columns:
- npl_nett
- laba_tahun
- laba_bulan
- kap
- kpmm
- asset
- roa
- bopo

## Error Handling

The API returns appropriate HTTP status codes and error messages:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Security

- Passwords are hashed before storage
- File uploads are validated for type and content
- Temporary files are cleaned up after processing

## Dummy Data for Testing

The `dummy_data/` folder contains sample files for testing the CSV and Excel parsers:

### Available Dummy Files
- `dummy_bpr_scrapping.csv`: Sample BPR Scrapping data with realistic financial metrics
- `dummy_bpr_lainnya.xlsx`: Sample BPR Lainnya data with contact information
- `dummy_d.xlsx`: Sample D entity data with financial indicators

### Data Generation
To regenerate dummy data files:
```bash
python dummy_data_generator.py
```

### Testing Parser Functionality
1. Test CSV parsing for BPR Scrapping data:
```python
from csv_to_db.csv_parser import parse_bpr_scrapping_csv
data = parse_bpr_scrapping_csv('dummy_data/dummy_bpr_scrapping.csv')
```

2. Test Excel parsing for BPR Lainnya data:
```python
from csv_to_db.xlsx_parser import parse_bpr_lainnya_xlsx
data = parse_bpr_lainnya_xlsx('dummy_data/dummy_bpr_lainnya.xlsx')
```

3. Test Excel parsing for D entity data:
```python
from csv_to_db.xlsx_parser import parse_d_xlsx
data = parse_d_xlsx('dummy_data/dummy_d.xlsx')
```

### Sample Data Details

#### BPR Scrapping CSV Sample
Contains realistic financial metrics:
- Asset values in billions (e.g., 10B, 12B)
- Profit values in millions (e.g., 500M, 600M)
- Ratios as percentages (e.g., NPL: 2.5%, KPMM: 15.5%)
- Management information with multiple names

#### BPR Lainnya Excel Sample
Contains formatted contact information:
- Phone numbers in standard format (e.g., "(022) 123-4567")
- Valid email addresses
- Complete addresses with districts
- Proper regional classifications

#### D Entity Excel Sample
Contains representative financial indicators:
- NPL ratios between 2-4%
- Profit values in millions
- Asset values in billions
- Standard financial ratios (ROA, BOPO, etc.)
