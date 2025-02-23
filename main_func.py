"""
Python_ver : 3.8
Selenium_ver : 3.141.0
Playwright_ver : Current

pyautogui : Current

Database
pysql
mysql
sqlalchemy
"""
import subprocess
import sys
from typing import Union, Tuple, Optional

try:
	import selenium
except ImportError:
	subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium=3.141.0"])

try:
	import sshtunnel
except ImportError:
	subprocess.check_call([sys.executable, "-m", "pip", "install", "sshtunnel"])
	import sshtunnel
from sshtunnel import SSHTunnelForwarder


def install_package(package_name: str, version: Optional[int] = None):
	try:
		__import__(package_name)
	except ImportError:
		if version:
			package_name = f"{package_name}=={version}"
		print(f"Installing {package_name}...")
		subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])


install_package("sshtunnel")
install_package("pymysql")
install_package("mysql-connector-python")
install_package("sqlalchemy")

from sshtunnel import SSHTunnelForwarder
import pymysql
import mysql.connector
from sqlalchemy import create_engine


def ssh_connection(
		ssh_host: str,
		ssh_port: int,
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

	server = SSHTunnelForwarder(
		(ssh_host, ssh_port),
		ssh_username,
		ssh_password,
		remote_bind_address,
		local_bind_address
	)
	server.start()  # SSH Tunnel Start
	print(f"SSH tunnel started: {server.local_bind_address}")
	return server


def connect_pymysql(host: str, user: str, password: str, database: str, port: Optional[int] = 3306):
	"""PyMySQL을 사용하여 MySQL 데이터베이스에 연결"""
	connection = pymysql.connect(
		host=host, user=user, password=password, database=database, port=port
	)
	print("Connected to MySQL using PyMySQL")
	return connection


def connect_mysql_connector(
		host: str, user: str, password: str, database: str, port: Optional[int] = 3306
):
	"""mysql-connector-python을 사용하여 MySQL 데이터베이스에 연결"""
	connection = mysql.connector.connect(
		host=host, user=user, password=password, database=database, port=port
	)
	print("Connected to MySQL using mysql-connector-python")
	return connection


def mysql_connect_sqlalchemy(
		host: str, user: str, password: str, database: str, port: Optional[int] = 3306
):
	"""SQLAlchemy를 사용하여 MySQL 데이터베이스에 연결"""
	engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")
	print("Connected to MySQL using SQLAlchemy")
	return engine
