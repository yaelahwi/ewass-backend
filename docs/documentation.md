# BPR Data Management System Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Database Models](#database-models)
4. [API Documentation](#api-documentation)
5. [Data Processing](#data-processing)
6. [Security & Authentication](#security--authentication)
7. [Testing](#testing)
8. [Deployment](#deployment)

## Overview

The BPR Data Management System is a Flask-based REST API designed to manage Bank Perkreditan Rakyat (BPR) data. The system handles various data sources including CSV and XLSX file uploads, and provides comprehensive user management capabilities.

### Key Features
- Data import from CSV/XLSX files
- BPR financial data management
- User authentication and authorization
- Comprehensive API endpoints
- Automated data validation
- Secure file handling

## System Architecture

### Project Structure
```
project_root/
│
├── asset/                # File upload storage
├── controller/          # API endpoints & routing
│   ├── bpr_lainnya.py
│   ├── bpr_scrapping.py
│   ├── d.py
│   └── user.py
├── csv_to_db/          # Data parsing logic
│   ├── csv_parser.py
│   └── xlsx_parser.py
├── dto/                # Data Transfer Objects
│   ├── bpr_lainnya_schema.py
│   ├── bpr_scrapping_schema.py
│   ├── d_schema.py
│   └── user_schema.py
├── object/             # Database Models
│   └── models.py
├── service/           # Business Logic
│   ├── bpr_service.py
│   └── user_service.py
└── main.py           # Application Entry Point
```

### Component Interaction
1. Controllers handle HTTP requests and route them to appropriate services
2. Services contain business logic and interact with models
3. DTOs handle data validation and serialization
4. Models define database structure and relationships
5. Parsers handle file processing and data extraction

## Database Models

### User Model
- Handles user authentication and authorization
- Stores user credentials and permissions
- Fields include username, hashed password, and role

### BPR Models
1. BPR Scrapping Model
   - Financial metrics and performance indicators
   - Historical data tracking
   - Management information

2. BPR Lainnya Model
   - Contact information
   - Location details
   - Operational jurisdiction

3. D Entity Model
   - Financial ratios
   - Performance metrics
   - Asset information

## API Documentation

### Pagination

All list endpoints support pagination with the following query parameters:
- `page`: Current page number (default: 1)
- `per_page`: Number of items per page (default: 10)

Example request:
```http
GET /bpr_scrapping/?page=2&per_page=15
```

Response format:
```json
{
    "success": true,
    "pages": 10,          // Total number of pages
    "results": [          // Array of items for current page
        {
            "id": 1,
            "name": "BPR Example",
            ...
        }
    ],
    "total": 150,         // Total number of items
    "current_page": 2,    // Current page number
    "has_next": true,     // Whether there is a next page
    "has_prev": true,     // Whether there is a previous page
    "per_page": 15        // Number of items per page
}
```

### Authentication Endpoints

#### User Registration
```http
POST /user/register
Content-Type: application/json

{
    "username": "string",
    "password": "string",
    "email": "string"
}
```

#### User Login
```http
POST /user/login
Content-Type: application/json

{
    "username": "string",
    "password": "string"
}
```

### API Response Format

All list endpoints now support pagination with the following response format:
```json
{
    "success": true,
    "pages": 10,          // Total number of pages
    "results": [          // Array of items for current page
        {
            "id": 1,
            "name": "Example BPR",
            // ... other fields
        }
    ],
    "total": 150,         // Total number of items
    "current_page": 2,    // Current page number
    "has_next": true,     // Whether there is a next page
    "has_prev": true,     // Whether there is a previous page
    "per_page": 15        // Number of items per page
}
```

### Query Parameters
All list endpoints support the following query parameters:
- `page`: Page number (default: 1)
- `per_page`: Number of items per page (default: 10)

Example:
```http
GET /bpr_scrapping/?page=2&per_page=15
GET /bpr_lainnya/?page=1&per_page=20
GET /d/?page=3&per_page=10
```

### BPR Data Endpoints

#### Upload BPR Scrapping Data
```http
POST /bpr_scrapping/upload
Content-Type: multipart/form-data

file: [CSV File]
```

Required CSV columns:
- tahun
- bulan
- nama_provinsi
- nama_kota
- sandi
- nama
- asset
- kyd
[and other financial metrics]

#### Upload BPR Lainnya Data
```http
POST /bpr_lainnya/upload
Content-Type: multipart/form-data

file: [XLSX File]
```

Required XLSX columns:
- sandi
- nama_bpr
- alamat_bpr
- kota_kabupaten
- provinsi
[and other contact details]

## Data Processing

### CSV Processing
- Located in `csv_to_db/csv_parser.py`
- Handles BPR Scrapping data
- Validates data format and content
- Performs data type conversion
- Example usage:
```python
from csv_to_db.csv_parser import parse_bpr_scrapping_csv
data = parse_bpr_scrapping_csv('path/to/file.csv')
```

### XLSX Processing
- Located in `csv_to_db/xlsx_parser.py`
- Handles BPR Lainnya and D entity data
- Supports multiple sheets
- Example usage:
```python
from csv_to_db.xlsx_parser import parse_bpr_lainnya_xlsx
data = parse_bpr_lainnya_xlsx('path/to/file.xlsx')
```

## Security & Authentication

### Password Security
- Passwords are hashed using secure algorithms
- Salt is automatically generated and stored
- Implementation in user_service.py

### File Upload Security
- File type validation
- Content validation
- Temporary file cleanup
- Secure file storage in asset directory

### API Security
- Token-based authentication
- Role-based access control
- Request validation
- Error handling with appropriate HTTP status codes

## Testing

### Unit Testing
- Test file: `test_parsers.py`
- Tests CSV and XLSX parsing
- Validates data transformation
- Example:
```bash
python -m pytest test_parsers.py
```

### Dummy Data Testing
- Located in `dummy_data/` directory
- Generate test data:
```bash
python dummy_data_generator.py
```

### Available Test Data
1. dummy_bpr_scrapping.csv
   - Contains realistic financial metrics
   - Sample management information
   - Historical data points

2. dummy_bpr_lainnya.xlsx
   - Contact information samples
   - Regional classifications
   - Address formatting examples

3. dummy_d.xlsx
   - Financial ratio examples
   - Performance metric samples
   - Asset value ranges

## Deployment

### Prerequisites
- Python 3.x
- PostgreSQL database
- Virtual environment

### Installation Steps
1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
- Copy .env.example to .env
- Update database credentials
- Set security keys

4. Initialize database:
- Create PostgreSQL database
- Update DATABASE_URL in .env
- Tables auto-create on startup

### Running the Application
Development:
```bash
flask run
```

Production:
```bash
gunicorn main:app
```

### Environment Variables
```
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key
DEBUG=False
```

## Error Handling

### HTTP Status Codes
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

### Error Response Format
```json
{
    "error": "Error message",
    "status_code": 400,
    "details": "Additional error details"
}
```

## Maintenance

### Database Maintenance
- Regular backups recommended
- Index optimization
- Query performance monitoring

### File Storage
- Regular cleanup of temporary files
- Monitoring of storage space
- Backup of uploaded files

### Logging
- Application logs in standard output
- Error logging with stack traces
- Access logging for security

## Support

For technical support or questions:
1. Check existing documentation
2. Review error logs
3. Contact system administrator

---

This documentation is maintained and updated regularly. For the latest version, please check the repository.
