#!/usr/bin/env python3
from csv_to_db.csv_parser import parse_bpr_scrapping_csv
from csv_to_db.xlsx_parser import parse_bpr_lainnya_xlsx, parse_d_xlsx

print("Testing BPR Scrapping CSV parser...")
try:
    bpr_data = parse_bpr_scrapping_csv('dummy_data/dummy_bpr_scrapping.csv')
    print(f"Successfully parsed {len(bpr_data)} BPR Scrapping records")
    print("Sample data:", bpr_data[0])
except Exception as e:
    print(f"Error parsing BPR Scrapping CSV: {str(e)}")

print("\nTesting BPR Lainnya XLSX parser...")
try:
    bpr_lainnya_data = parse_bpr_lainnya_xlsx('dummy_data/dummy_bpr_lainnya.xlsx')
    print(f"Successfully parsed {len(bpr_lainnya_data)} BPR Lainnya records")
    print("Sample data:", bpr_lainnya_data[0])
except Exception as e:
    print(f"Error parsing BPR Lainnya XLSX: {str(e)}")

print("\nTesting D Entity XLSX parser...")
try:
    d_data = parse_d_xlsx('dummy_data/dummy_d.xlsx')
    print(f"Successfully parsed {len(d_data)} D Entity records")
    print("Sample data:", d_data[0])
except Exception as e:
    print(f"Error parsing D Entity XLSX: {str(e)}")
