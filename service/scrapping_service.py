import json, time, re, os, threading, logging, csv
from queue import Queue
from datetime import datetime
from collections import OrderedDict
from controller import user
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import requests
from bs4 import BeautifulSoup
import urllib.parse
from rich.progress import Progress, TextColumn, BarColumn, TaskID, SpinnerColumn, TimeRemainingColumn
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from rich.tree import Tree
from rich.live import Live
from rich.table import Table
from database import SessionLocal
from object.models import BprLainnya, FetchHistory
from service.user_service import get_current_user

# Configure logging to file instead of console
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.ERROR,  # Only show ERROR level logs or higher
    format='%(asctime)s - %(levelname)s: %(message)s',
    filename='logs/data_extraction.log',
    filemode='w'
)
logger = logging.getLogger(__name__)
log_queue, data_queue = Queue(), Queue()

# Setup rich console
console = Console()

# Shared progress tracking variables
province_progress = {}
city_progress = {}
bank_progress = {}
progress_lock = threading.Lock()

# Global progress trackers
year_progress = None
month_progress = None

def log_worker():
    """Worker to handle logging from multiple threads"""
    while True:
        log_record = log_queue.get()
        if log_record is None: break
        logger.handle(log_record)

def data_writer_worker():
    """Worker to handle ordered data writing to CSV"""
    current_date = datetime.now().strftime('%Y%m%d')
    with open(f'asset/bpr_scrapping/data{current_date}.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        headers = [
            'waktu_diambil', 'tahun', 'bulan', 'nama_provinsi', 'nama_kota', 'sandi', 'nama',
            'asset_saat_ini','asset_tahun_lalu','kyd_saat_ini','kyd_tahun_lalu','hutang_saat_ini',
            'hutang_tahun_lalu','laba_tahun_tahun_lalu_saat_ini','laba_tahun_tahun_lalu_sebelumnya',
            'laba_saat_ini','laba_tahun_lalu','tabungan_saat_ini','tabungan_tahun_lalu','deposito_saat_ini',
            'deposito_tahun_lalu','penempatan_pada_bank_lain_saat_ini','penempatan_pada_bank_lain_tahun_lalu',
            'total_ekuitas','total_ekuitas_tahun_lalu','simpanan_dari_bank_lain_saat_ini',
            'simpanan_dari_bank_lain_tahun_lalu','laba_desember_tahun_sebelum','npl_net','kpmm','ldr','roa','kap','ppap',
            'bopo','nim','cr',
            'direksi', 'dewan_komisaris'
        ]
        writer.writerow(headers)
        while True:
            data = data_queue.get()
            if data is None: 
                break
            writer.writerow(data)
            data_queue.task_done()

class ThreadSafeLogger:
    """Thread-safe logger wrapper"""
    def __init__(self, logger): self.logger = logger
    def info(self, msg): pass  # Suppress info logs
    def error(self, msg): pass  # Suppress error logs

def extract_direksi_komisaris(html):
    """Extract Direksi and Dewan Komisaris from correct table in HTML"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        direksi, komisaris = [], []
        for tr in soup.find_all('tr', valign='top'):
            tds = tr.find_all('td')
            tds = tr.find_all('td')
            if len(tds) < 4: continue
        for table in soup.find_all('table'):
            if table.find(string=lambda t: t and "Anggota Direksi BPR dan Anggota Dewan Komisaris BPR" in t):
                mode = None
                for row in table.find_all('tr'):
                    tds = row.find_all('td')
                    if not tds: continue
                    text = tds[-1].get_text(strip=True)
                    if text.upper() == "DIREKSI": mode = "direksi"
                    elif text.upper() == "DEWAN KOMISARIS": mode = "komisaris"
                    elif mode == "direksi" and text and text[0].isdigit() and '.' in text:
                        direksi.append(text.split('.', 1)[1].strip())
                    elif mode == "komisaris" and text and text[0].isdigit() and '.' in text:
                        komisaris.append(text.split('.', 1)[1].strip())
                break
        return ', '.join(direksi), ', '.join(komisaris)
    except Exception:
        return '', ''

def extract_report_urls(response_text):
    """Extract report URLs from response text"""
    urls = []
    try:
        for match in re.finditer(r"Common\.addFrame\('([^']+)',\s*'([^']+)'", response_text):
            report_type, url = match.group(1), match.group(2)
            parsed_url = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if 'BankCode' in query_params and '-' in query_params['BankCode'][0]:
                query_params['BankCode'] = [query_params['BankCode'][0].split('-', 1)[1]]
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            new_url = urllib.parse.urlunparse((
                parsed_url.scheme, parsed_url.netloc, parsed_url.path, 
                parsed_url.params, new_query, parsed_url.fragment
            ))
            urls.append((report_type, new_url))
    except Exception:
        pass
    return urls

def get_report_data(base_url, report_url, province_name, city_name, bank_name, year, month):
    """Extract financial and management data from report URLs"""
    try:
        if not report_url.startswith(('http://', 'https://')):
            report_url = urllib.parse.urljoin(base_url, report_url)
        
        response = requests.get(report_url, timeout=30)
        response.raise_for_status()
         # Management data extraction
        direksi, komisaris ='', ''
        # Financial data extraction
        extracted_kap = {
                            'KPMM': '',
                            'PPAP': '',
                            'ROA': '',
                            'LDR': '',
                            'BOPO':'',
                            'KAP':'',
                            'Cash Ratio':'',
                            'NPL (neto)':'',
                            'NIM':''
                        }
        extracted = {
                    'Total Aset': {'current': '', 'previous': ''},
                    'Kredit yang Diberikan': {'current': '', 'previous': ''},
                    'Total Hutang': {'current': '', 'previous': ''},
                    'Laba (Rugi) Tahun-tahun Lalu': {'current': '', 'previous': ''},
                    'Laba (Rugi) Tahun Berjalan': {'current': '', 'previous': ''},
                    'Tabungan': {'current': '', 'previous': ''},
                    'Deposito': {'current': '', 'previous': ''},
                    'Penempatan pada Bank Lain': {'current': '', 'previous': ''},
                    'Total Ekuitas': {'current': '', 'previous': ''},
                    'Simpanan dari Bank Lain':{'current': '', 'previous': ''},
                    'Laba (Rugi) Desember Tahun Sebelum':''
                    }
       
        if 'BPK-901-000005' in report_url:
            direksi, komisaris = extract_direksi_komisaris(response.text)
     
        
        # Process financial data from HTML tables
        soup = BeautifulSoup(response.text, 'html.parser')
        clean_value = lambda val: ('' if not val or val == '&nbsp;' else 
                                  (('-' + val[1:-1]).replace('\xa0', '').replace(',', '').replace(' ', '') if val.startswith('(') and val.endswith(')') 
                                   else val.replace('\xa0', '').replace(',', '').replace(' ', '')))
        
        for tr in soup.find_all('tr', valign='top'):
           
            if 'BPK-901-000001' in report_url:
                tds = tr.find_all('td')
                if len(tds) < 4: continue
                label = tds[1].get_text(strip=True)
                label_clean = re.sub(r'^[a-z0-9]\.\s*', '', label.replace('-/-', '')).strip()
                
                raw3, raw4 = tds[2].get_text(strip=True), tds[3].get_text(strip=True)
                clean_raw3=clean_value(raw3)+"000"
                clean_raw4=clean_value(raw4)+"000"
                if label_clean == 'Total Aset':
                    extracted['Total Aset']['current'] = clean_raw3
                    extracted['Total Aset']['previous'] = clean_raw4
                elif label_clean == 'Jumlah':
                    extracted['Kredit yang Diberikan']['current'] = clean_raw3
                    extracted['Kredit yang Diberikan']['previous'] = clean_raw4
                elif label_clean == 'Total Liabilitas':
                    extracted['Total Hutang']['current'] = clean_raw3
                    extracted['Total Hutang']['previous'] = clean_raw4
                elif label_clean == 'Tahun-tahun Lalu':
                    extracted['Laba (Rugi) Tahun-tahun Lalu']['current'] = clean_raw3
                    extracted['Laba (Rugi) Tahun-tahun Lalu']['previous'] = clean_raw4
                elif label_clean == 'Tahun Berjalan':
                    extracted['Laba (Rugi) Tahun Berjalan']['current'] = clean_raw3
                    extracted['Laba (Rugi) Tahun Berjalan']['previous'] = clean_raw4
                elif 'tabungan' in label_clean.lower():
                    extracted['Tabungan']['current'] = clean_raw3
                    extracted['Tabungan']['previous'] = clean_raw4
                elif 'deposito' in label_clean.lower():
                    extracted['Deposito']['current'] = clean_raw3
                    extracted['Deposito']['previous'] = clean_raw4
                elif 'penempatan pada bank lain' in label_clean.lower():
                    extracted['Penempatan pada Bank Lain']['current'] = clean_raw3
                    extracted['Penempatan pada Bank Lain']['previous'] = clean_raw4
                elif 'total ekuitas' in label_clean.lower():
                    extracted['Total Ekuitas']['current'] = clean_raw3
                    extracted['Total Ekuitas']['previous'] = clean_raw4
                elif 'simpanan dari bank lain' in label_clean.lower():
                    extracted['Simpanan dari Bank Lain']['current'] = clean_raw3
                    extracted['Simpanan dari Bank Lain']['previous'] = clean_raw4
                
            elif 'BPK-901-000003' in report_url:
                tds = tr.find_all('td')
                if len(tds) < 8: continue
                
                label = tds[1].get_text(strip=True)
                label_clean = re.sub(r'^[a-z0-9]\.\s*', '', label.replace('-/-', '')).strip()

                raw6='0'
                raw6 = tds[7].get_text(strip=True)
                if 'neto' in label_clean.lower():
                    extracted_kap['NPL (neto)'] = clean_value(raw6)
                elif 'kpmm' in label_clean.lower():
                    extracted_kap['KPMM'] = clean_value(raw6)
                elif 'ldr' in label_clean.lower():
                    extracted_kap['LDR'] = clean_value(raw6)
                elif 'roa' in label_clean.lower():
                    extracted_kap['ROA'] = clean_value(raw6)
                elif 'kap' in label_clean.lower():
                    extracted_kap['KAP'] = clean_value(raw6)
                elif 'ppap' in label_clean.lower():
                    extracted_kap['PPAP'] = clean_value(raw6)
                elif 'bopo' in label_clean.lower():
                    extracted_kap['BOPO'] = clean_value(raw6)
                elif 'cash ratio' in label_clean.lower():
                    extracted_kap['Cash Ratio'] = clean_value(raw6)
                elif 'nim' in label_clean.lower():
                    extracted_kap['NIM'] = clean_value(raw6)
            
        if 'BPK-901-000001' in report_url:
            # print(report_url)
            url_des = report_url.replace(f"Month=3", "Month=12")
            url_des = url_des.replace(f"Year={datetime.now().year}", f"Year={datetime.now().year-1}")
            # print(url_des)
            if not url_des.startswith(('http://', 'https://')):
                url_des = urllib.parse.urljoin(base_url, url_des)
            
            response_des = requests.get(url_des, timeout=30)
            response_des.raise_for_status()
            soup_des = BeautifulSoup(response_des.text, 'html.parser')
            for tr in soup_des.find_all('tr', valign='top'):
                tds = tr.find_all('td')
                if len(tds) < 4: continue
                label = tds[1].get_text(strip=True)
                label_clean = re.sub(r'^[a-z0-9]\.\s*', '', label.replace('-/-', '')).strip()
                
                raw3 = tds[2].get_text(strip=True)
                clean_raw3=clean_value(raw3)+"000"
                if 'tahun berjalan' in label_clean.lower():
                    extracted['Laba (Rugi) Desember Tahun Sebelum'] = clean_raw3


        return extracted, extracted_kap, direksi, komisaris
    except Exception as e:
        print(f"Error occurred: {e}")
        return None,None, '', ''

def update_bank_progress(province_name, city_name, bank_name, completed=False):
    """Update progress for a specific bank"""
    with progress_lock:
        if province_name not in bank_progress:
            bank_progress[province_name] = {}
        if city_name not in bank_progress[province_name]:
            bank_progress[province_name][city_name] = {'total': 0, 'completed': 0, 'current': bank_name}
        
        if completed:
            bank_progress[province_name][city_name]['completed'] += 1
        else:
            bank_progress[province_name][city_name]['current'] = bank_name
            if bank_name not in bank_progress[province_name][city_name]:
                bank_progress[province_name][city_name]['total'] += 1



def process_bank(bank_info, progress, bank_task_id):
    """Process data for a single bank"""
    global month_progress, year_progress
    year, month, province, city, bank = bank_info
    
    # Update progress tracking
    update_bank_progress(province['ProvinceName'], city['CityName'], bank['BankName'])
    
    try:
        # Prepare request data
        base_url = 'https://cfs.ojk.go.id/cfs/'
        url = base_url + 'Report.aspx?BankTypeCode=BPK&BankTypeName=BPR+Konvensional'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0',
            'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd', 'Referer': 'https://cfs.ojk.go.id/',
            'X-Ext.Net': 'delta=true', 
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://cfs.ojk.go.id',
            'DNT': '1', 'Sec-GPC': '1', 'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin'
        }
        
        data = {
            '__EVENTTARGET': 'DefaultResourceManager',
            '__EVENTARGUMENT': 'ShowReportButton|event|Click',
            'Month': month['text'],
            '_Month_state': f'[{{"value":"{month["value"]}","text":"{month["text"]}","index":{month["index"]}}}]',
            'Year': str(year),
            '_Year_state': f'[{{"value":"{year}","text":"{year}","index":0}}]',
            'ProvinceCode': province['ProvinceName'],
            '_ProvinceCode_state': f'[{{"value":"{province["ProvinceCode"]}","text":"{province["ProvinceName"]}","index":0}}]',
            'CityCode': city['CityName'],
            '_CityCode_state': f'[{{"value":"{city["CityCode"]}","text":"{city["CityName"]}","index":0}}]',
            'BankCode': f'{bank["BankCode"]}-{bank["BankName"]}',
            'ReportTree_SM': '[{"nodeID":"BPK-901-000005","clientID":"BPK-901-000005","text":"Laporan Informasi Lainnya","path":"/root/BPK-901-000005","attributes":{"checked":false,"qshowDelay":0}}]',
            'ReportTree_CheckNodes': '[{"nodeID":"BPK-901-000001","clientID":"BPK-901-000001","text":"Laporan Posisi Keuangan","path":"/root/BPK-901-000001","attributes":{"checked":true,"qshowDelay":0}},{"nodeID":"BPK-901-000002","clientID":"BPK-901-000002","text":"Laporan Laba Rugi","path":"/root/BPK-901-000002","attributes":{"checked":false,"qshowDelay":0}},{"nodeID":"BPK-901-000003","clientID":"BPK-901-000003","text":"Laporan Kualitas Aset Produktif","path":"/root/BPK-901-000003","attributes":{"checked":true,"qshowDelay":0}},{"nodeID":"BPK-901-000004","clientID":"BPK-901-000004","text":"Laporan Komitmen dan Kontinjensi","path":"/root/BPK-901-000004","attributes":{"checked":false,"qshowDelay":0}},{"nodeID":"BPK-901-000005","clientID":"BPK-901-000005","text":"Laporan Informasi Lainnya","path":"/root/BPK-901-000005","attributes":{"checked":true,"qshowDelay":0}}]',
            'BankCodeSearchField': '',
            'BankTree_SM': f'[{{"nodeID":"{bank["BankCode"]}","clientID":"{bank["BankCode"]}","text":"{bank["BankCode"]}-{bank["BankName"]}","path":"/root/{bank["BankCode"]}","attributes":{{"checked":null,"qshowDelay":0}}}}]',
            'BankTree_CheckNodes': ''
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=30)
            report_urls = extract_report_urls(response.text)
            
            # Extract data from reports
            data_found = False
            extracted_main = None
            data_found_kap = False
            direksi, komisaris = '', ''
            
            for report_type, report_url in report_urls:
                if 'Year=2015' in report_url:
                    report_url = report_url.replace('Year=2015', f'Year={year}')
                    
                if report_type == "BPK-901-000001":  # Main financial data
                    extracted_main, _, _, _ = get_report_data(base_url, report_url, province['ProvinceName'], 
                                                        city['CityName'], bank['BankName'], year, month['text'])
                    if extracted_main:
                        data_found = True
                
                elif report_type == "BPK-901-000003":  # KAP financial data
                    _, extracted_kap, _, _ = get_report_data(base_url, report_url, province['ProvinceName'], 
                                                        city['CityName'], bank['BankName'], year, month['text'])
                    if extracted_kap:
                        data_found_kap = True
                        
                elif report_type == "BPK-901-000005":  # Management data
                    _, _, direksi, komisaris = get_report_data(base_url, report_url, province['ProvinceName'], 
                                                          city['CityName'], bank['BankName'], year, month['text'])
                    
                if data_found and (direksi or komisaris) and data_found_kap:
                    break

            if data_found and data_found_kap:
                # Prepare and save data row
                current_time = datetime.now().isoformat(timespec='microseconds')
                sandi = bank['BankName'].split('-')[0].strip()
                nama = bank['BankName'].split('-')[1].strip()
                row_data = [
                    current_time, year, month['text'], province['ProvinceName'], city['CityName'], sandi, nama,
                    extracted_main['Total Aset']['current'] or '0', extracted_main['Total Aset']['previous'] or '0',
                    extracted_main['Kredit yang Diberikan']['current'] or '0', extracted_main['Kredit yang Diberikan']['previous'] or '0',
                    extracted_main['Total Hutang']['current'] or '0', extracted_main['Total Hutang']['previous'] or '0',
                    extracted_main['Laba (Rugi) Tahun-tahun Lalu']['current'] or '0', extracted_main['Laba (Rugi) Tahun-tahun Lalu']['previous'] or '0',
                    extracted_main['Laba (Rugi) Tahun Berjalan']['current'] or '0', extracted_main['Laba (Rugi) Tahun Berjalan']['previous'] or '0',
                    extracted_main['Tabungan']['current'] or '0', extracted_main['Tabungan']['previous'] or '0',
                    extracted_main['Deposito']['current'] or '0', extracted_main['Deposito']['previous'] or '0',
                    extracted_main['Penempatan pada Bank Lain']['current'] or '0', extracted_main['Penempatan pada Bank Lain']['previous'] or '0',
                    extracted_main['Total Ekuitas']['current'] or '0', extracted_main['Total Ekuitas']['previous'] or '0',
                    extracted_main['Simpanan dari Bank Lain']['current'] or '0', extracted_main['Simpanan dari Bank Lain']['previous'] or '0',
                    extracted_main['Laba (Rugi) Desember Tahun Sebelum'] or '0',
                    extracted_kap['NPL (neto)'] or '0',extracted_kap['KPMM'] or '0', extracted_kap['LDR'] or '0',extracted_kap['ROA'] or '0', 
                    extracted_kap['KAP'] or '0', extracted_kap['PPAP'] or '0', extracted_kap['BOPO'] or '0', 
                    extracted_kap['NIM'] or '0', extracted_kap['Cash Ratio'] or '0', direksi, komisaris
                ]
                data_queue.put(row_data)

        except Exception as e:
            print("sini: ",e)
            pass
            
        # Update bank as completed
        update_bank_progress(province['ProvinceName'], city['CityName'], bank['BankName'], completed=True)
        progress.update(bank_task_id, advance=1)
        
    except Exception as e:
        update_bank_progress(province['ProvinceName'], city['CityName'], bank['BankName'], completed=True)
        progress.update(bank_task_id, advance=1)
        print("disini: ",e)

def get_bpr_lainnya_data():
    db = SessionLocal()
    try:
        rows = db.query(BprLainnya).all()
        if not rows:
            return None

        data_by_provinsi = {}
        for row in rows:
            provinsi = row.provinsi
            kota = row.kota_kabupaten
            bank = {
                'BankCode': row.sandi,
                'BankName': row.nama_bpr,
            }

            data_by_provinsi.setdefault(provinsi, {})
            data_by_provinsi[provinsi].setdefault(kota, []).append(bank)

        structured_data = []
        for provinsi, cities in data_by_provinsi.items():
            structured_data.append({
                "ProvinceName": provinsi,
                "ProvinceCode": "0",
                "City": [{"CityName": kota,"CityCode":"0", "Bank": banks} for kota, banks in cities.items()]
            })

        return structured_data
    finally:
        db.close()


def process_bank_data(current_month, current_year, data_writer_thread, fetch_history_id):
    """Process bank data and collect financial information"""
    bank_data = get_bpr_lainnya_data()
    db = SessionLocal()
    fetch_record = db.query(FetchHistory).filter(FetchHistory.id == fetch_history_id).first()
    
    if not bank_data:
        console.print("Table 'bpr_lainnya' is empty, please insert data first")
        if fetch_record:
            fetch_record.status = "Failed"
            db.commit()
        db.close()
        return
    
    # Define months and years to process
    months = [
        {"value": "3", "text": "Maret", "index": 0},
        {"value": "6", "text": "Juni", "index": 1},
        {"value": "9", "text": "September", "index": 2},
        {"value": "12", "text": "Desember", "index": 3}
    ]
    # month = months[(current_month//3)-1]
    month = months[3]
    year = 2024
    
    # Setup global progress trackers
    global year_progress, month_progress
    
    if fetch_record:
        fetch_record.periode_pelaporan = f"{month['text']} {year}"
        db.commit()
    try:
        # Process data year by year
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=50),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("[cyan]{task.completed}/{task.total}"),
            TimeRemainingColumn(),
            console=console,
            transient=False,  # Keep the progress bars visible
            refresh_per_second=4  # Update more frequently
        ) as progress:
            # Calculate total banks for this month/year
            total_banks = sum(len(city['Bank']) for province in bank_data for city in province['City'])
            bank_task = progress.add_task(f"{year} {month['text']}...", total=total_banks)
            
            # Build the task list
            console.print(f"Preparing to process {total_banks} banks for {month['text']} {year}...")
            
            # Process banks sequentially
            completed_banks = 0
            for province in bank_data:
                for city in province['City']:
                    for bank in city['Bank']:
                        bank_info = (year, month, province, city, bank)
                        process_bank(bank_info, progress, bank_task)
                        completed_banks += 1
                        progress.update(bank_task, completed=completed_banks, total=total_banks)
                        if completed_banks == 5:
                            break
                    if completed_banks == 5:
                            break
                if completed_banks == 5:
                            break

        # Signal threads to stop
        data_queue.put(None)
        data_writer_thread.join()
        if fetch_record:
                fetch_record.status = "Success"
                db.commit()
            
    except Exception as e:
        console.print(f"Error during bank data processing: {e}")
        if fetch_record:
            fetch_record.status = "Failed"
            db.commit()
        raise
    finally:
        db.close()


def main(logging_thread, data_writer_thread):
    db = SessionLocal()
    fetch_history_record = None
    user = get_current_user(db)
    print(user)
    try:
        console.print("Starting OJK BPR Data Collection")
        current_month = datetime.now().month
        current_year = datetime.now().year
        now = datetime.now()
        fetch_history_record = FetchHistory(
            fetch_date=now.date(),
            fetch_time=now.time(),
            periode="N/A",  # Will be updated later in process_bank_data
            status="On Progress",
            user=user.nama
        )
        db.add(fetch_history_record)
        db.commit()
        db.refresh(fetch_history_record)
        process_bank_data(current_month, current_year, data_writer_thread, fetch_history_record.id)
        # Signal to stop logging
        log_queue.put(None)
        logging_thread.join()
        
        console.print("Data collection completed!")
    except Exception as e:
            console.print(f"Error in main: {e}")
            # If an error occurs, set status to "Failed"
            if fetch_history_record:
                fetch_history_record.status = "Failed"
                db.commit()
            raise
    finally:
        db.close()

    

def thread_scrapping():
    # Start worker threads
    logging_thread = threading.Thread(target=log_worker, daemon=True)
    data_writer_thread = threading.Thread(target=data_writer_worker, daemon=True)
    logging_thread.start()
    data_writer_thread.start()

    # Run main process
    main(logging_thread, data_writer_thread)

    return "Scrapping dijalankan"
