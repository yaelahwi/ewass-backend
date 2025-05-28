import json, time, re, os, threading, logging, csv
from queue import Queue
from datetime import datetime
from collections import OrderedDict
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
    with open(f'data/data{current_date}.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        headers = [
            'Waktu Diambil', 'Tahun', 'Bulan', 'Nama Provinsi', 'Nama Kota', 'Nama Bank',
            'Total Aset Saat Ini', 'Total Aset Tahun Sebelumnya',
            'Kredit yang Diberikan Saat Ini', 'Kredit yang Diberikan Tahun Sebelumnya',
            'Total Hutang Saat Ini', 'Total Hutang Tahun Sebelumnya',
            'Laba (Rugi) Tahun-tahun Lalu Saat Ini', 'Laba (Rugi) Tahun-tahun Lalu Tahun Sebelumnya',
            'Laba (Rugi) Tahun Berjalan Saat Ini', 'Laba (Rugi) Tahun Berjalan Tahun Sebelumnya', 'Tabungan Saat ini', 'Tabungan Tahun Sebelumnya',
            'Deposito Saat Ini', 'Deposito Tahun Sebelumnya',
            'NPL (neto)','KPMM','KAP', 'PPAP', 'ROA', 'Cash Ratio', 'LDR', 'BOPO', 'NIM'
            'Direksi', 'Dewan Komisaris'
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

def setup_driver():
    """Set up Chrome WebDriver with headless options"""
    chrome_options = Options()
    for arg in ['--headless', '--no-sandbox', '--disable-dev-shm-usage', 
               '--window-size=1920,1080', '--disable-gpu', '--disable-extensions']:
        chrome_options.add_argument(arg)
    return webdriver.Chrome(options=chrome_options)

def wait_and_click(driver, by, value, timeout=10):
    """Wait for element and click it"""
    try:
        element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(3)
        element.click()
        return element
    except Exception:
        return None

def click_dropdown_trigger(driver, dropdown_id, timeout=10):
    """Click dropdown trigger element"""
    try:
        trigger = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"#{dropdown_id}-triggerWrap .x-form-trigger")))
        driver.execute_script("arguments[0].scrollIntoView(true);", trigger)
        time.sleep(3)
        trigger.click()
        return trigger
    except Exception:
        return None

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
        print(report_url)
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
                    }
       
        if 'BPK-901-000005' in report_url:
            direksi, komisaris = extract_direksi_komisaris(response.text)
     
        
        # Process financial data from HTML tables
        soup = BeautifulSoup(response.text, 'html.parser')
        clean_value = lambda val: ('' if not val or val == '&nbsp;' else 
                                  (('-' + val[1:-1]) if val.startswith('(') and val.endswith(')') 
                                   else val.replace('\xa0', '').replace(',', '').replace(' ', '')))
        
        for tr in soup.find_all('tr', valign='top'):
           
            if 'BPK-901-000001' in report_url:
                tds = tr.find_all('td')
                if len(tds) < 4: continue
                label = tds[1].get_text(strip=True)
                label_clean = re.sub(r'^[a-z0-9]\.\s*', '', label.replace('-/-', '')).strip()
                
                raw3, raw4 = tds[2].get_text(strip=True), tds[3].get_text(strip=True)
                raw3=raw3+"000"
                raw4=raw4+"000"
                if label_clean == 'Total Aset':
                    extracted['Total Aset']['current'] = clean_value(raw3)
                    extracted['Total Aset']['previous'] = clean_value(raw4)
                elif label_clean == 'Jumlah':
                    extracted['Kredit yang Diberikan']['current'] = clean_value(raw3)
                    extracted['Kredit yang Diberikan']['previous'] = clean_value(raw4)
                elif label_clean == 'Total Liabilitas':
                    extracted['Total Hutang']['current'] = clean_value(raw3)
                    extracted['Total Hutang']['previous'] = clean_value(raw4)
                elif label_clean == 'Tahun-tahun Lalu':
                    extracted['Laba (Rugi) Tahun-tahun Lalu']['current'] = clean_value(raw3)
                    extracted['Laba (Rugi) Tahun-tahun Lalu']['previous'] = clean_value(raw4)
                elif label_clean == 'Tahun Berjalan':
                    extracted['Laba (Rugi) Tahun Berjalan']['current'] = clean_value(raw3)
                    extracted['Laba (Rugi) Tahun Berjalan']['previous'] = clean_value(raw4)
                elif 'tabungan' in label_clean.lower():
                    extracted['Tabungan']['current'] = clean_value(raw3)
                    extracted['Tabungan']['previous'] = clean_value(raw4)
                elif 'deposito' in label_clean.lower():
                    extracted['Deposito']['current'] = clean_value(raw3)
                    extracted['Deposito']['previous'] = clean_value(raw4)
                
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

                print(extracted_kap)
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
        print(bank_progress)

def get_bank_data(driver, city_name):
    """Get bank data for a specific city"""
    banks = []
    try:
        click_dropdown_trigger(driver, "BankCode")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#treeview-1021-body")))
        time.sleep(4)
        bank_elements = driver.find_elements(By.CSS_SELECTOR, "#treeview-1021-body tr.x-grid-row")
        
        for bank_element in bank_elements:
            try:
                bank_text = bank_element.find_element(By.CSS_SELECTOR, "span.x-tree-node-text").text
                if bank_text and "-" in bank_text:
                    banks.append({
                        "BankCode": bank_text.split("-")[0].strip(),
                        "BankName": bank_text
                    })
            except Exception:
                pass
        
        ActionChains(driver).move_by_offset(0, 0).click().perform()
        time.sleep(3)
    except Exception:
        pass
    
    return banks

def update_city_progress(province_name, city_name, completed=False):
    """Update progress for a specific city"""
    with progress_lock:
        if province_name not in city_progress:
            city_progress[province_name] = {'total': 0, 'completed': 0, 'current': city_name}
        
        if completed:
            city_progress[province_name]['completed'] += 1
        else:
            city_progress[province_name]['current'] = city_name
            city_progress[province_name]['total'] += 1

def get_province_data(driver, province_name, province_code):
    """Get city and bank data for a specific province"""
    try:
        url = "https://cfs.ojk.go.id/cfs/Report.aspx?BankTypeCode=BPK&BankTypeName=BPR+Konvensional"
        driver.get(url)
        time.sleep(7)
        
        click_dropdown_trigger(driver, "ProvinceCode")
        time.sleep(4)
        
        wait_and_click(driver, By.XPATH, f"//li[contains(@class, 'x-boundlist-item') and contains(text(), '{province_name}')]")
        time.sleep(5)
        
        click_dropdown_trigger(driver, "CityCode")
        time.sleep(4)
        
        cities = []
        city_elements = driver.find_elements(By.CSS_SELECTOR, "li.x-boundlist-item")
        total_cities = len([c for c in city_elements if c.text and "Provinsi" not in c.text])
        
        processed_cities = 0
        for city_element in city_elements:
            city_name = city_element.text
            if city_name and "Provinsi" not in city_name:
                update_city_progress(province_name, city_name)
                city_element.click()
                time.sleep(5)
                
                banks = get_bank_data(driver, city_name)
                cities.append({
                    "CityCode": f"DATI{province_code}",
                    "CityName": city_name,
                    "Bank": banks
                })
                
                processed_cities += 1
                update_city_progress(province_name, city_name, completed=True)
                
                click_dropdown_trigger(driver, "CityCode")
                time.sleep(4)
        
        return {
            "ProvinceCode": f"DATI{province_code}",
            "ProvinceName": province_name,
            "City": cities
        }
    except Exception:
        return None

def update_province_progress(province_name, completed=False):
    """Update progress for a specific province"""
    with progress_lock:
        if province_name not in province_progress:
            province_progress[province_name] = {'completed': False, 'current': True}
        
        if completed:
            province_progress[province_name]['completed'] = True
        else:
            province_progress[province_name]['current'] = True

def process_province(province_info):
    """Process a province with own WebDriver instance"""
    province_name, province_code = province_info
    thread_logger = ThreadSafeLogger(logger)
    
    update_province_progress(province_name)
    
    driver = setup_driver()
    try:
        province_data = get_province_data(driver, province_name, province_code)
        update_province_progress(province_name, completed=True)
        return province_data
    except Exception:
        return None
    finally:
        driver.quit()

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
                        # print("EXTRACTED: ", extracted_main)
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
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                row_data = [
                    current_time, year, month['text'], province['ProvinceName'], city['CityName'], bank['BankName'],
                    extracted_main['Total Aset']['current'] or '0', extracted_main['Total Aset']['previous'] or '0',
                    extracted_main['Kredit yang Diberikan']['current'] or '0', extracted_main['Kredit yang Diberikan']['previous'] or '0',
                    extracted_main['Total Hutang']['current'] or '0', extracted_main['Total Hutang']['previous'] or '0',
                    extracted_main['Laba (Rugi) Tahun-tahun Lalu']['current'] or '0', extracted_main['Laba (Rugi) Tahun-tahun Lalu']['previous'] or '0',
                    extracted_main['Laba (Rugi) Tahun Berjalan']['current'] or '0', extracted_main['Laba (Rugi) Tahun Berjalan']['previous'] or '0',
                    extracted_main['Tabungan']['current'] or '0', extracted_main['Tabungan']['previous'] or '0',
                    extracted_main['Deposito']['current'] or '0', extracted_main['Deposito']['previous'] or '0',
                    extracted_kap['NPL (neto)'] or '0',extracted_kap['KPMM'] or '0',extracted_kap['KAP'] or '0',
                    extracted_kap['PPAP'] or '0', extracted_kap['ROA'] or '0', extracted_kap['Cash Ratio'] or '0',
                    extracted_kap['LDR'] or '0', extracted_kap['BOPO'] or '0', extracted_kap['NIM'] or '0',
                    direksi, komisaris
                ]
                data_queue.put(row_data)

        except Exception as e:
            print(e)
            pass
            
        # Update bank as completed
        update_bank_progress(province['ProvinceName'], city['CityName'], bank['BankName'], completed=True)
        progress.update(bank_task_id, advance=1)
        
    except Exception:
        update_bank_progress(province['ProvinceName'], city['CityName'], bank['BankName'], completed=True)
        progress.update(bank_task_id, advance=1)


def process_bank_data(current_month, current_year):
    """Process bank data and collect financial information"""
    if not os.path.exists('bank_data.json'):
        console.print("bank_data.json not found, please run the script without this file first")
        return
    
    # Define months and years to process
    months = [
        {"value": "3", "text": "Maret", "index": 0},
        {"value": "6", "text": "Juni", "index": 1},
        {"value": "9", "text": "September", "index": 2},
        {"value": "12", "text": "Desember", "index": 3}
    ]
    # month = months[(current_month//3)-1]
    month = months[0]
    year = 2023
    
    with open('bank_data.json', 'r', encoding='utf-8') as f:
        bank_data = json.load(f)
    
    # Setup global progress trackers
    global year_progress, month_progress
    
    
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
         
    
    # Signal threads to stop
    data_queue.put(None)
    data_writer_thread.join()

def main():
    console.print("Starting OJK BPR Data Collection")
    
    if not os.path.exists('bank_data.json'):
        # Province data to collect
        provinces = [
            ("Provinsi Jawa Barat", "00101", 0),
            ("Provinsi Banten", "00102", 1),
            ("Provinsi DKI Jakarta", "00103", 2),
            ("Provinsi D.I. Yogyakarta", "00104", 3),
            ("Provinsi Jawa Tengah", "00105", 4),
            ("Provinsi Jawa Timur", "00106", 5),
            ("Provinsi Bengkulu", "00107", 6),
            ("Provinsi Jambi", "00108", 7),
            ("Provinsi NAD", "00109", 8),
            ("Provinsi Sumatera Utara", "00110", 9),
            ("Provinsi Sumatera Barat", "00111", 10),
            ("Provinsi Riau", "00112", 11),
            ("Provinsi Sumatera Selatan", "00113", 12),
            ("Provinsi Kep. Bangka Belitung", "00114", 13),
            ("Provinsi Kep. Riau", "00115", 14),
            ("Provinsi Lampung", "00116", 15),
            ("Provinsi Kalimantan Selatan", "00117", 16),
            ("Provinsi Kalimantan Barat", "00118", 17),
            ("Provinsi Kalimantan Timur", "00119", 18),
            ("Provinsi Kalimantan Tengah", "00120", 19),
            ("Provinsi Sulawesi Tengah", "00121", 20),
            ("Provinsi Sulawesi Selatan", "00122", 21),
            ("Provinsi Sulawesi Utara", "00123", 22),
            ("Provinsi Gorontalo", "00124", 23),
            ("Provinsi Sulawesi Barat", "00125", 24),
            ("Provinsi Sulawesi Tenggara", "00126", 25),
            ("Provinsi Nusa Tenggara Barat", "00127", 26),
            ("Provinsi Bali", "00128", 27),
            ("Provinsi Nusa Tenggara Timur", "00129", 28),
            ("Provinsi Maluku", "00130", 29),
            ("Provinsi Papua", "00131", 30),
            ("Provinsi Maluku Utara", "00132", 31),
            ("Provinsi Papua Barat", "00133", 32),
            ("DI LUAR INDONESIA", "00134", 33)
        ]
        
        console.print("Phase 1:Collecting provincial data structure")
        console.print("This will create bank_data.json with all provinces, cities, and banks")
        
        # Initialize progress display
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=50),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("[cyan]{task.completed}/{task.total}"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            province_task = progress.add_task(total=len(provinces), description="get province")
            
            # Initialize provinces in progress tracking
            for province_name, _, _ in provinces:
                update_province_progress(province_name)
            
            # Collect province data sequentially
            all_data = [None] * len(provinces)
            completed = 0
            for province_name, province_code, index in provinces:
                province_data = process_province((province_name, province_code))
                if province_data:
                    all_data[index] = province_data
                    progress.update(province_task, description=f"{province_name}")
                else:
                    progress.update(province_task, description=f"{province_name} - Tidak ada data")
                
                completed += 1
                progress.update(province_task, completed=completed)
                
                # Show a progress summary after each province
                if province_data:
                    cities = len(province_data.get('City', []))
                    banks = sum(len(city.get('Bank', [])) for city in province_data.get('City', []))
                    console.print(f"{province_name}:{cities} kota/kabupaten, {banks} bank")
                
            # Filter out None values
            all_data = [data for data in all_data if data is not None]
            
            # Save collected data
            with open('bank_data.json', 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            
    
    else:
        current_month = datetime.now().month
        current_year = datetime.now().year
        process_bank_data(current_month, current_year)
    
    # Signal to stop logging
    log_queue.put(None)
    logging_thread.join()
    
    console.print(Panel("[bold green]Data collection completed![/bold green]", 
                      subtitle="Results saved to data.csv"))
    

def threading():
    # Start worker threads
    logging_thread = threading.Thread(target=log_worker, daemon=True)
    data_writer_thread = threading.Thread(target=data_writer_worker, daemon=True)
    logging_thread.start()
    data_writer_thread.start()

    # Run main process
    main()
