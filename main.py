import os
import sys
import time
import ctypes
import shutil
import datetime
import configparser
from custom_modules import *
from custom_chromedriver import *

try:
    from sqlalchemy.orm import sessionmaker
except ImportError:
    install_package('sqlalchemy')
    from sqlalchemy.orm import sessionmaker
# ===============================================================================
#                                 Configuration
# ===============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.ini')
if not check_chromedriver():
    install_chromedriver()  # 크롬 드라이버 설치
# Database_URL =
config = configparser.ConfigParser()
config.read(config_path)
log_dir = config['PATH']['log_dir']
info_log_dir = config['PATH']['info_log_dir']
warning_log_dir = config['PATH']['warning_log_dir']
db_info_path = config['PATH']['db_info_path']
json_file_path = config['SHEET']['json_file_path']
url = config['SHEET']['url']
sheet_name = config['SHEET']['sheet_name']
sheet_index = config['SHEET']['sheet_index']
db_name = config['DB']['db_name']
logger = custom_logger(log_dir, info_log_dir, warning_log_dir)
# logger.info(), logger.error(), logger.warning(), logger.debug()

# db_info.txt 파일에서 사용자 이름과 비밀번호 읽기
with open(db_info_path, 'r') as f:
    ssh_host = f.readline().strip()
    ssh_username = f.readline().strip()
    ssh_password = f.readline().strip()


# ===============================================================================
#                                 Main Code
# ===============================================================================
def main():
    try:
        worksheet = get_spreadsheet(json_file_path=json_file_path, url=url, sheet_name=sheet_name,
                                    sheet_index=sheet_index)
        data = worksheet.get_all_values()
    except Exception as e:
        logger.error(f"Google Sheet 오류: {e}")
        return
    try:
        tunnel = create_ssh_tunnel(ssh_host=ssh_host, ssh_username=ssh_username, ssh_password=ssh_password)
        engine = create_db_connection(tunnel, username=ssh_username, password=ssh_password, db_name=db_name)
        driver = setup_driver()
        try:
            Session = sessionmaker(bind=engine)
            session = Session()
            insert_query(session, data)
        except Exception as e:
            logger.error(f"DB 세션 오류: {e}")
            return
    except Exception as e:
        logger.error(f"Process Error: {e}")
        return
    finally:
        if driver: driver.quit()
        if tunnel: tunnel.close()
        if engine: engine.dispose()
        if session: session.close()


# ===============================================================================
#                                 Scheduling
# ===============================================================================
def should_run():
    config = configparser.ConfigParser()
    config.read('config.ini')

    current_time = datetime.datetime.now()
    start_time = datetime.datetime.strptime(config['TIME']['start_date'], '%H:%M').time()

    # 현재 시간이 시작 시간보다 이전이면 다음 날로 설정
    if current_time.time() < start_time:
        next_run = datetime.datetime.combine(current_time.date() + datetime.timedelta(days=1), start_time)
    else:
        next_run = datetime.datetime.combine(current_time.date(), start_time)

    # 다음 실행 시간까지 대기
    wait_seconds = (next_run - current_time).total_seconds()
    if wait_seconds > 0:
        print(f"다음 실행까지 {wait_seconds / 3600:.1f}시간 대기 중...")
        time.sleep(wait_seconds)

    return True


# ===============================================================================
#                            Program information
# ===============================================================================
__author__ = '김동기'
__requester__ = '플랫폼 운영팀'
__latest_editor__ = '김동기'
__registration_date__ = '250324'
__latest_update_date__ = '250324'
__version__ = 'v1.0.0'
__title__ = 'Title'
__desc__ = 'Title'
__changeLog__ = {
    'v1.0.0': ['Initial Release.'],
}
version_lst = list(__changeLog__.keys())

full_version_log = '\n'
short_version_log = '\n'

for ver in __changeLog__:
    full_version_log += f'{ver}\n' + '\n'.join(['    - ' + x for x in __changeLog__[ver]]) + '\n'

if len(version_lst) > 5:
    short_version_log += '.\n.\n.\n'
    short_version_log += f'{version_lst[-2]}\n' + '\n'.join(
        ['    - ' + x for x in __changeLog__[version_lst[-2]]]) + '\n'
    short_version_log += f'{version_lst[-1]}\n' + '\n'.join(
        ['    - ' + x for x in __changeLog__[version_lst[-1]]]) + '\n'

# ===============================================================================
#                                 Main Code
# ===============================================================================

if __name__ == "__main__":
    terminal_width = shutil.get_terminal_size().columns
    print('=' * terminal_width)
    ctypes.windll.kernel32.SetConsoleTitleW(f'{__title__} {__version__} ({__latest_update_date__})')
    sys.stdout.write(f'{__title__} {__version__} ({__latest_update_date__})\n')
    sys.stdout.write(f'제작자: {__author__}\n')
    sys.stdout.write(f'최종 수정자: {__latest_editor__}\n')
    sys.stdout.write(f'{short_version_log if short_version_log.strip() else full_version_log}\n')
    print('=' * terminal_width)
    last_run_date = None
    while True:
        try:
            today = datetime.datetime.now().date()

            if last_run_date != today and should_run():  # 같은 날 두 번 실행되지 않도록 체크
                main()
                last_run_date = today
                logger.info("데이터 수집 완료. 다음 실행을 기다립니다...")

            time.sleep(60)  # 루프가 너무 빨리 돌지 않도록 1분 대기

        except Exception as e:
            logger.error(f"오류 발생: {e}")
            time.sleep(5)
