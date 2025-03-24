# ===============================================================================
#                                 Import
# ===============================================================================
import os
import sys
import json
import time
import ctypes
import logging
import datetime
import requests
import subprocess
import configparser
# ===============================================================================
#                               Package Install
# ===============================================================================
def install_package(package_name: str, version: str = None):
	if version:
		package_name = f"{package_name}=={version}"
	try:
		__import__(package_name)
	except ImportError:
		print(f"Installing {package_name}...")
		subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
try:
	import gspread
except ImportError:
	install_package('gspread')
	import gspread
try:
	from google.oauth2.service_account import Credentials
except ImportError:
	install_package('google')
	from google.oauth2.service_account import Credentials
try:
	from sshtunnel import SSHTunnelForwarder
except ImportError:
	install_package('sshtunnel')
	from sshtunnel import SSHTunnelForwarder
try:
	from sqlalchemy import create_engine, text
except ImportError:
	install_package('sqlalchemy')
	from sqlalchemy import create_engine, text
try:
	from selenium import webdriver
except ImportError:
	install_package('selenium', '3.141.0')
	from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
# ===============================================================================
#                               Logger Init
# ===============================================================================
config = configparser.ConfigParser()
config.read('config.ini')
log_dir = config['PATH']['log_dir']
info_log_dir = config['PATH']['info_log_dir']
warning_log_dir = config['PATH']['warning_log_dir']

def custom_logger(log_dir, info_log_dir, warning_log_dir):
	"""Custom Logger 생성"""
    # 로그 디렉토리 생성
	for directory in [log_dir, info_log_dir, warning_log_dir]:
		if not os.path.exists(directory):
			os.makedirs(directory)

	# Logger INIT
	current_date = datetime.datetime.now().strftime("%Y%m%d")
	info_log_file = os.path.join(info_log_dir, f'{current_date}.log')
	warning_log_file = os.path.join(warning_log_dir, f'{current_date}.log')

	# 로거 설정
	logger = logging.getLogger(__name__)
	if logger.hasHandlers():
		logger.handlers.clear()
	logger.setLevel(logging.INFO)

	# INFO 레벨 로그 핸들러 (모든 로그)
	info_handler = logging.FileHandler(info_log_file, encoding='utf-8')
	info_handler.setLevel(logging.INFO)
	info_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
	info_handler.setFormatter(info_formatter)

	# WARNING 레벨 로그 핸들러 (경고 로그만)
	warning_handler = logging.FileHandler(warning_log_file, encoding='utf-8')
	warning_handler.setLevel(logging.WARNING)
	warning_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
	warning_handler.setFormatter(warning_formatter)

	# 콘솔 출력 핸들러
	console_handler = logging.StreamHandler()
	console_handler.setLevel(logging.INFO)
	console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
	console_handler.setFormatter(console_formatter)

	# 핸들러 추가
	logger.addHandler(info_handler)
	logger.addHandler(warning_handler)
	logger.addHandler(console_handler)

	return logger

logger = custom_logger(log_dir, info_log_dir, warning_log_dir)
# ===============================================================================
#                               TXT File Read
# ===============================================================================
def txt_file_read_comma(file_path):
    try:
        with open(file_path, 'r', encoding='cp949') as f:
            lines = f.readlines()
    except:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    if len(lines) == 1:
        return lines[0].strip().split(',')
    else:
        return [line.strip() for line in lines]
def txt_file_read_tab(file_path):
    try:
        with open(file_path, 'r', encoding='cp949') as f:
            lines = f.readlines()
    except:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    return [line.strip().split('\t') for line in lines]
# ===============================================================================
#                               Date Encode & Decode
# ===============================================================================
# 인코딩 함수: YYYY-MM-DD -> MM-DD
def encode_date(date):
    return date.strftime('%m-%d')
"""
encoded_dates = [encode_date(date) for date in date_range]
print("Encoded Dates:", encoded_dates)
"""
# 디코딩 함수: MM-DD -> YYYY-MM-DD
def decode_date(date_str, year):
    return datetime.datetime.strptime(f"{year}-{date_str}", '%Y-%m-%d').date()
"""
decoded_dates = [decode_date(encoded_date, datetime.datetime.now().year) for encoded_date in encoded_dates]
print("Decoded Dates:", decoded_dates)
"""
# ===============================================================================
#                               Date List Generator
# ===============================================================================
def generate_date_list(start_date, end_date):
	"""날짜 범위 생성"""
	date_list = []
	current_date = start_date
	while current_date <= end_date:
		date_list.append(current_date)
		current_date += datetime.timedelta(days=1)
	return date_list
# ===============================================================================
#                               Google Sheet
# ===============================================================================
def get_spreadsheet(json_file_path:str, url: str, sheet_name: str, sheet_index: int):
    file_name = os.path.basename(json_file_path)
    if file_name.split('.')[-1] != 'json':
        raise Exception("json 파일 확장자가 아닙니다.")
    
    service_account_info = json.loads(open(json_file_path,'r').read())
    json_key_list = ['type','project_id','private_key_id','private_key','client_email','client_id','auth_uri','token_uri','auth_provider_x509_cert_url','client_x509_cert_url','universe_domain']
    for _key in json_key_list:
        if _key not in service_account_info.keys():
            raise Exception(f"json 파일 오류:\"{_key}\"키값이 없습니다.")

    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    cred = Credentials.from_service_account_info(service_account_info, scopes=scopes)

    spread_sheet = gspread.authorize(cred).open_by_url(url)

    if sheet_name:
        sheet = spread_sheet.worksheet(sheet_name)
    elif sheet_index:
        sheet = spread_sheet.worksheet(sheet_index)
    else:
        raise Exception("sheet_name 또는 sheet_index 중 하나를 입력해주세요.")
    return sheet
# ===============================================================================
#                               SSH Tunnel
# ===============================================================================
def create_ssh_tunnel(ssh_host: str, ssh_username: str, ssh_password: str):
	"""SSH 터널링 생성"""
	try:
		tunnel = SSHTunnelForwarder(
			(ssh_host, 22),
			ssh_username=ssh_username,
			ssh_password=ssh_password,
			remote_bind_address=('localhost', 3306),
			local_bind_address=('0.0.0.0', 3307),
			set_keepalive=30
		)
		tunnel.start()
		return tunnel
	except Exception as e:
		logger.error(f"SSH 터널링 오류: {e}")
		return None
# ===============================================================================
#                               DB Connection
# ===============================================================================
def create_db_connection(tunnel, username: str, password: str, db_name: str):
	"""SSH 터널링을 통한 MySQL 연결"""
	if tunnel:
		engine = create_engine(
			f'mysql+pymysql://{username}:{password}@localhost:3307/{db_name}',
			echo=True
		)
		return engine
	else:
		logger.error(f"DB 연결 오류")
		return None
# ===============================================================================
#                               SQL Insert
# ===============================================================================
def insert_query(session, data: list):
	"""SQL Insert 쿼리 실행"""
	for row in data:
		row_1, row_2, row_3, row_4 = row
		try:
			session.execute(text(
				"""
				INSERT INTO Table_name(col_1, col_2, col_3, col_4)
				VALUES(:row_1, :row_2, :row_3, :row_4)
				ON DUPLICATE KEY UPDATE
				col_1 = VALUES(col_1),
				col_2 = VALUES(col_2),
				col_3 = VALUES(col_3),
				col_4 = VALUES(col_4)
				"""
			),
			{'row_1': row_1, 'row_2': row_2, 'row_3': row_3, 'row_4': row_4}
			)
			session.commit()
			logger.info(f"Data Insert & Update Success")
		except Exception as e:
			session.rollback()
			logger.error(f"Data Insert & Update Error: {e}")
# ===============================================================================
#                               IP Change
# ===============================================================================
def send_alt_p():
	"""Keyboard Hooking을 위한 Win32 API 설정"""
	user32 = ctypes.windll.user32
	# Alt 키 누르기 (virtual key code 18)
	user32.keybd_event(0x12, 0, 0, 0)  # Alt down
	# P 키 누르기 (virtual key code 80)
	user32.keybd_event(0x50, 0, 0, 0)  # P down
	time.sleep(0.1)
	# P 키 떼기
	user32.keybd_event(0x50, 0, 2, 0)  # P up
	# Alt 키 떼기
	user32.keybd_event(0x12, 0, 2, 0)  # Alt up

def ip_change():
	"""HiIP를 사용한 IP 변경 로직"""
	result_flag = False
	for _ in range(1, 6):
		try:
			old_ip = requests.get("http://ip.wkwk.kr/", timeout=_).text
		except Exception as e:
			try:
				old_ip = requests.get("http://sub.wkwk.kr/ip/", timeout=_).text
			except Exception as e:
				pass
			else:
				break
		else:
			break
		time.sleep(_)
	else:
		return result_flag
	
	ADB_PATH = r"C:\adb\adb.exe"
	if os.path.exists(ADB_PATH):
		subprocess.run([ADB_PATH, "shell", "svc", "data", "disable", "e"])
		time.sleep(1)
		subprocess.run([ADB_PATH, 'shell', 'am', 'start', '-a', 'android.intent.action.MAIN', '-n', 'com.mmaster.mmaster/com.mmaster.mmaster.MainActivity'])
		time.sleep(1)
		subprocess.run([ADB_PATH, 'shell', 'svc', 'data', 'enable'])
		time.sleep(1)
	else:
		send_alt_p()

	for cnt in range(2,7):
		logger.info('인터넷 접속대기중 - {}/5회'.format(cnt), end='')
		time.sleep(cnt)
		try:
			cur_ip = requests.get("http://ip.wkwk.kr/", timeout=cnt).text
		except Exception as e:
			try:
				cur_ip = requests.get("http://sub.wkwk.kr/ip/", timeout=cnt).text
			except Exception as e:
				pass
			else:
				break
		else:
			break

	if old_ip == cur_ip:
		logger.info('\n아이피가 변경되지 않았습니다.')
		return result_flag
	else:
		logger.info(f'\n{old_ip} -> {cur_ip} 변경 완료.')
		result_flag = True
		return result_flag
# ===============================================================================
#                               Driver Setup
# ===============================================================================
def setup_driver():
	"""
	Chrome 드라이버 설정
	driver = setup_driver() 로 생성
	"""
	chrome_options = Options()
	# chrome_options.add_argument('--headless')  # 헤드리스 모드
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument('--disable-gpu')
	chrome_options.add_argument('--disable-dev-shm-usage')
	"""화면 설정"""
	# chrome_options.add_argument('--start-maximized')  # 전체 화면으로 시작
	chrome_options.add_argument("--window-size=960,1080") # 절반 크기
	chrome_options.add_argument("--window-position=0,0") # 왼쪽에 붙임

	chrome_options.add_argument('--incognito') # Secret Mode
	chrome_options.add_argument('--log-level=3')  # 로깅 레벨을 ERROR로 설정
	chrome_options.add_argument('--disable-blink-features=AutomationControlled')
	
	chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])  # 로깅 비활성화
	chrome_options.add_experimental_option('useAutomationExtension', False)
	# User-Agent 설정
	chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
	
	driver = webdriver.Chrome(options=chrome_options)
	
	# 자동화 감지 방지를 위한 JavaScript 실행
	driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

	return driver
