"""
Python_ver : 3.8
Selenium_ver : 3.141.0
Playwright_ver : Current

pyautogui : Current

Database Section
pysql X
mysql X
sqlalchemy
"""
import os
import sys
import time
import logging
import subprocess
import configparser
from datetime import datetime
from typing import Union, Tuple, Optional

def install_package(package_name: str, version: Optional[str] = None):
	if version:
		package_name = f"{package_name}=={version}"
	try:
		__import__(package_name)
	except ImportError:
		print(f"Installing {package_name}...")
		subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

install_package(package_name="requests")
install_package(package_name="sshtunnel")
install_package(package_name="sqlalchemy")
install_package(package_name="selenium", version="3.141.0")

import requests
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine

# ===============================================================================
#                               Logger Init
# ===============================================================================
def custom_logger(log_dir, info_log_dir, warning_log_dir):
	"""Custom Logger 생성"""
    # 로그 디렉토리 생성
    for directory in [log_dir, info_log_dir, warning_log_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Logger INIT
    current_date = datetime.now().strftime("%Y%m%d")
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
config = configparser.ConfigParser()
config.read('config.ini')
log_dir = config['PATH']['log_dir']
info_log_dir = config['PATH']['info_log_dir']
warning_log_dir = config['PATH']['warning_log_dir']

logger = custom_logger(log_dir, info_log_dir, warning_log_dir)
# ===============================================================================
#                               SSH Tunnel
# ===============================================================================
def ssh_connection(
        ssh_host: str,
        ssh_port: int, # 22
        ssh_username: str,
        ssh_password: str,
        remote_bind_address: Tuple[str, int],
        local_bind_address: Tuple[str, int] = ("127.0.0.1", 0)
) -> SSHTunnelForwarder:
    """
    SSH 터널을 생성하는 함수 (Python 3.8 버전)

    :param ssh_host: SSH 서버 주소
    :param ssh_port: SSH 포트 (보통 22)
    :param ssh_username: SSH 로그인 ID
    :param ssh_password: SSH 로그인 비밀번호
    :param remote_bind_address: (원격 호스트, 포트) ex) ('127.0.0.1', 3306)
    :param local_bind_address: (로컬 호스트, 포트) 기본값 ('127.0.0.1', 랜덤 포트)
    :return: SSHTunnelForwarder 객체
    """

    tunnel = SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_username,
        ssh_password=ssh_password,
        remote_bind_address=remote_bind_address, # ('localhost', 3306)
        local_bind_address=local_bind_address, # ('0.0.0.0', 3307)
        set_keepalive=30
    )
    tunnel.start()  # SSH Tunnel Start
    print(f"SSH tunnel started: {tunnel.local_bind_address}")
    return tunnel
# ===============================================================================
#                               DB Connection
# ===============================================================================
def mysql_connect_sqlalchemy_ssh(tunnel, username: str, password: str, db_name: str):
    """SSH 터널링을 통한 MySQL 연결"""
    if tunnel:
        engine = create_engine(
			f"mysql+pymysql://{username}:{password}@localhost:3307/{db_name}",
			# echo=True
		)
		return engine
	else:
		return None

def mysql_connect_sqlalchemy(
        host: str,
        user: str,
        password: str,
        database: str,
        port: Optional[int] = 3306,
        tunnel_port: Optional[str] = None):
    """
    SQLAlchemy를 사용하여 MySQL 데이터베이스에 연결
    :param host: 데이터베이스 호스트 주소
    :param user: 데이터베이스 사용자 이름
    :param password: 데이터베이스 비밀번호
    :param database: 데이터베이스 이름
    :param port: 데이터베이스 포트 (기본값 3306)
    :param tunnel_port: SSH 터널링을 사용할 경우 로컬 포트 번호
    :return: SQLAlchemy 엔진 객체
    """
    if tunnel_port:
        engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{tunnel_port}/{database}")
    else:
        engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")
    print("Connected to MySQL using SQLAlchemy")
    return engine


# ===============================================================================
#                               IP Change
# ===============================================================================
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

	for cnt in range(2, 7):
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
	chrome_options.add_argument('--headless')  # 헤드리스 모드
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument('--disable-dev-shm-usage')
	chrome_options.add_argument('--disable-gpu')
	chrome_options.add_argument('--start-maximized')  # 전체 화면으로 시작
	chrome_options.add_argument('--incognito')
	chrome_options.add_argument('--disable-blink-features=AutomationControlled')
	chrome_options.add_argument('--log-level=3')  # 로깅 레벨을 ERROR로 설정
	chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])  # 로깅 비활성화
	chrome_options.add_experimental_option('useAutomationExtension', False)

	# User-Agent 설정
	chrome_options.add_argument(
		'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

	driver = webdriver.Chrome(options=chrome_options)

	# 자동화 감지 방지를 위한 JavaScript 실행
	driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

	return driver