#!/usr/bin/env python3
import pandas as pd
from datetime import datetime

# BPR Scrapping CSV dummy data
bpr_scrapping_data = [
    {
        "waktu_diambil": datetime.utcnow().isoformat(),
        "tahun": 2023,
        "bulan": "Januari",
        "nama_provinsi": "Jawa Barat",
        "nama_kota": "Bandung",
        "sandi": "BP01",
        "nama": "BPR ABC",
        "asset": 10000000000,  # 10B
        "kyd": 2000000000,    # 2B
        "total_hutang": 15000000000,  # 15B
        "laba_tahun_lalu": 500000000,  # 500M
        "laba_saat_ini": 600000000,   # 600M
        "npl_net": 2.5,
        "kpmm": 15.5,
        "ldr": 80.2,
        "roa": 5.1,
        "kap": 50.5,
        "ppap": 300000000,   # 300M
        "bopo": 75.5,
        "cr": 1.2,
        "direksi": "John Doe, Jane Smith",
        "dewan_komisaris": "Robert Johnson, Mary Williams"
    },
    {
        "waktu_diambil": datetime.utcnow().isoformat(),
        "tahun": 2023,
        "bulan": "Februari",
        "nama_provinsi": "DKI Jakarta",
        "nama_kota": "Jakarta Selatan",
        "sandi": "BP02",
        "nama": "BPR XYZ",
        "asset": 12000000000,  # 12B
        "kyd": 2500000000,    # 2.5B
        "total_hutang": 18000000000,  # 18B
        "laba_tahun_lalu": 450000000,  # 450M
        "laba_saat_ini": 500000000,   # 500M
        "npl_net": 3.0,
        "kpmm": 16.2,
        "ldr": 85.5,
        "roa": 4.5,
        "kap": 55.2,
        "ppap": 350000000,   # 350M
        "bopo": 78.2,
        "cr": 1.3,
        "direksi": "Alice Chen, Bob Wilson",
        "dewan_komisaris": "David Lee, Sarah Brown"
    }
]

print("Generating BPR Scrapping CSV...")
# Format datetime before creating DataFrame
for data in bpr_scrapping_data:
    data['waktu_diambil'] = datetime.strptime(data['waktu_diambil'], "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S")

df = pd.DataFrame(bpr_scrapping_data)
# Write CSV with proper formatting
with open("dummy_data/dummy_bpr_scrapping.csv", "w", newline='') as f:
    headers = list(df.columns)
    # Write headers with proper formatting
    formatted_headers = [f'"{h}"' for h in headers]
    f.write(",".join(formatted_headers) + "\n")
    
    # Write data rows
    for _, row in df.iterrows():
        values = []
        for col in headers:
            val = row[col]
            if isinstance(val, str):
                # Quote string values
                values.append(f'"{val}"')
            elif isinstance(val, float):
                # Format floats with 2 decimal places
                values.append(f"{val:.2f}")
            else:
                values.append(str(val))
        f.write(",".join(values) + "\n")

# BPR Lainnya Excel dummy data
bpr_lainnya_data = [
    {
        "sandi": "BP01",
        "nama_bpr": "BPR ABC",
        "alamat_bpr": "Jalan Merdeka No. 123, Bandung Wetan",
        "kota_kabupaten": "Bandung",
        "provinsi": "Jawa Barat",
        "no_telepon": "(022) 123-4567",
        "email": "contact@bprabc.co.id",
        "wilayah_kerja_ojk": "Jawa Barat"
    },
    {
        "sandi": "BP02",
        "nama_bpr": "BPR XYZ",
        "alamat_bpr": "Jalan Sudirman No. 456, Kebayoran Baru",
        "kota_kabupaten": "Jakarta Selatan",
        "provinsi": "DKI Jakarta",
        "no_telepon": "(021) 765-4321",
        "email": "info@bprxyz.co.id",
        "wilayah_kerja_ojk": "DKI Jakarta"
    },
    {
        "sandi": "BP03",
        "nama_bpr": "BPR DEF",
        "alamat_bpr": "Jalan Thamrin No. 789, Medan Kota",
        "kota_kabupaten": "Medan",
        "provinsi": "Sumatera Utara",
        "no_telepon": "(061) 987-6543",
        "email": "support@bprdef.co.id",
        "wilayah_kerja_ojk": "Sumatera Utara"
    }
]

print("Generating BPR Lainnya Excel...")
df_bpr = pd.DataFrame(bpr_lainnya_data)
with pd.ExcelWriter("dummy_data/dummy_bpr_lainnya.xlsx") as writer:
    df_bpr.to_excel(writer, index=False, sheet_name="BPR_Lainnya")

# D entity Excel dummy data
d_data = [
    {
        "npl_nett": 2.5,
        "laba_tahun": 500000000,  # 500M
        "laba_bulan": 50000000,   # 50M
        "kap": 55.5,
        "kpmm": 16.2,
        "asset": 12000000000,    # 12B
        "roa": 4.5,
        "bopo": 78.5
    },
    {
        "npl_nett": 3.2,
        "laba_tahun": 450000000,  # 450M
        "laba_bulan": 45000000,   # 45M
        "kap": 52.8,
        "kpmm": 15.8,
        "asset": 10500000000,    # 10.5B
        "roa": 4.2,
        "bopo": 80.2
    }
]

print("Generating D Excel...")
df_d = pd.DataFrame(d_data)
with pd.ExcelWriter("dummy_data/dummy_d.xlsx") as writer:
    df_d.to_excel(writer, index=False, sheet_name="D")

# Generate JSON with pagination
print("\nGenerating JSON with pagination...")
import json

# Format numbers appropriately
def format_number(value):
    if isinstance(value, float):
        return round(value, 2)
    elif isinstance(value, int):
        return value  # Keep integers as integers
    return value

# Process data with proper formatting
def process_data(data_list):
    processed = []
    for item in data_list:
        processed_item = {}
        for k, v in item.items():
            if k == "tahun":  # Keep tahun as integer
                processed_item[k] = int(v)
            else:
                processed_item[k] = format_number(v)
        processed.append(processed_item)
    return processed

# Create paginated data structure
json_data = {
    "pagination": {
        "current_page": 1,
        "total_pages": 2,
        "total_records": 7,
        "per_page": 5
    },
    "data": {
        "bpr_scrapping": {
            "current_page": 1,
            "total_pages": 1,
            "total_records": len(bpr_scrapping_data),
            "per_page": 5,
            "records": process_data(bpr_scrapping_data)
        },
        "bpr_lainnya": {
            "current_page": 1,
            "total_pages": 1,
            "total_records": len(bpr_lainnya_data),
            "per_page": 5,
            "records": process_data(bpr_lainnya_data)
        },
        "d_entity": {
            "current_page": 1,
            "total_pages": 1,
            "total_records": len(d_data),
            "per_page": 5,
            "records": process_data(d_data)
        }
    }
}

# Ensure proper JSON formatting
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(obj)

# Create paginated data structure
paginated_data = {
    "pagination": {
        "current_page": 1,
        "total_pages": 2,
        "total_records": 7,
        "per_page": 5
    },
    "data": {
        "bpr_scrapping": {
            "current_page": 1,
            "total_pages": 1,
            "total_records": len(bpr_scrapping_data),
            "per_page": 5,
            "records": process_data(bpr_scrapping_data)
        },
        "bpr_lainnya": {
            "current_page": 1,
            "total_pages": 1,
            "total_records": len(bpr_lainnya_data),
            "per_page": 5,
            "records": process_data(bpr_lainnya_data)
        },
        "d_entity": {
            "current_page": 1,
            "total_pages": 1,
            "total_records": len(d_data),
            "per_page": 5,
            "records": process_data(d_data)
        }
    }
}

def format_datetime(dt):
    """Format datetime object to string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S") if isinstance(dt, datetime) else dt

def format_record(record):
    """Format a record's values to strings."""
    return {k: format_datetime(v) for k, v in record.items()}

# Format records
bpr_scrapping_formatted = [format_record(record) for record in bpr_scrapping_data]
bpr_lainnya_formatted = [format_record(record) for record in bpr_lainnya_data]
d_data_formatted = [format_record(record) for record in d_data]

# Create JSON template
json_template = '''{{
    "pagination": {{
        "current_page": 1,
        "total_pages": 2,
        "total_records": 7,
        "per_page": 5
    }},
    "data": {{
        "bpr_scrapping": {{
            "current_page": 1,
            "total_pages": 1,
            "total_records": {bpr_scrapping_len},
            "per_page": 5,
            "records": {bpr_scrapping_records}
        }},
        "bpr_lainnya": {{
            "current_page": 1,
            "total_pages": 1,
            "total_records": {bpr_lainnya_len},
            "per_page": 5,
            "records": {bpr_lainnya_records}
        }},
        "d_entity": {{
            "current_page": 1,
            "total_pages": 1,
            "total_records": {d_data_len},
            "per_page": 5,
            "records": {d_data_records}
        }}
    }}
}}'''

# Format the JSON string
json_str = json_template.format(
    bpr_scrapping_len=len(bpr_scrapping_formatted),
    bpr_scrapping_records=json.dumps(bpr_scrapping_formatted, indent=4),
    bpr_lainnya_len=len(bpr_lainnya_formatted),
    bpr_lainnya_records=json.dumps(bpr_lainnya_formatted, indent=4),
    d_data_len=len(d_data_formatted),
    d_data_records=json.dumps(d_data_formatted, indent=4)
)

# Fix indentation
json_str = json_str.replace('\n    [', '[\n    ').replace('\n    ]', '\n]')
lines = json_str.splitlines()
formatted_lines = []
for line in lines:
    if line.strip().startswith('"records": ['):
        formatted_lines.append(line)
    elif line.strip().startswith('"'):
        formatted_lines.append('            ' + line.strip())
    else:
        formatted_lines.append(line)

# Write JSON with proper formatting
with open("dummy_data/dummy_bpr_data.json", "w", encoding='utf-8') as f:
    f.write('\n'.join(formatted_lines))

print("All dummy files have been generated successfully!")
