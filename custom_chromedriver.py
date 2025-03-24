import os
import re
import shutil
import zipfile
import requests
import subprocess


def check_chromedriver():
    """ChromeDriver 설치 여부 확인"""
    return os.path.exists(os.path.join(os.getcwd(), "chromedriver.exe"))


def get_chrome_version():
    """레지스트리에서 Chrome 버전을 가져옴"""
    cmd = r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    match = re.search(r'version\s+REG_SZ\s+([\d.]+)', result.stdout)
    return match.group(1) if match else None


def get_compatible_chromedriver_version(chrome_version):
    """Chrome 버전에 맞는 ChromeDriver 버전 찾기"""
    major_version = chrome_version.split('.')[0]
    if int(major_version) <= 114:
        url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text.strip()
        except requests.exceptions.RequestException as e:
            print(f"ChromeDriver 버전을 찾을 수 없습니다: {e}")
            return None
    else:
        return major_version  # 115 이상은 메이저 버전 그대로 사용


def download_chromedriver(driver_version):
    """ChromeDriver 다운로드 및 설치"""
    if int(driver_version) <= 114:
        driver_zip_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_win32.zip"
    else:
        driver_zip_url = f"https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.35/win64/chromedriver-win64.zip"

    driver_zip_path = "chromedriver.zip"
    driver_extract_path = "chromedriver"

    print(f"ChromeDriver 다운로드 중: {driver_zip_url}")
    response = requests.get(driver_zip_url, stream=True)

    if response.status_code != 200:
        print("ChromeDriver 다운로드 실패!")
        return None

    with open(driver_zip_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    with zipfile.ZipFile(driver_zip_path, "r") as zip_ref:
        zip_ref.extractall(driver_extract_path)

    os.remove(driver_zip_path)
    extracted_driver_path = os.path.join(driver_extract_path, "chromedriver.exe")
    if not os.path.exists(extracted_driver_path):
        extracted_driver_path = os.path.join(driver_extract_path, "chromedriver-win64", "chromedriver.exe")

    if not os.path.exists(extracted_driver_path):
        print("ChromeDriver 실행 파일을 찾을 수 없습니다.")
        return None

    target_path = os.path.join(os.getcwd(), "chromedriver.exe")
    shutil.move(extracted_driver_path, target_path)
    shutil.rmtree(driver_extract_path)

    print(f"ChromeDriver 다운로드 및 설치 완료! ({target_path})")
    return target_path


def install_chromedriver():
    chrome_version = get_chrome_version()
    if chrome_version:
        print(f"Chrome 버전: {chrome_version}")
        driver_version = get_compatible_chromedriver_version(chrome_version)
        if driver_version:
            print(f"ChromeDriver 버전: {driver_version}")
            driver_path = download_chromedriver(driver_version)
            if driver_path:
                print(f"ChromeDriver 설치 완료: {driver_path}")
            else:
                print("ChromeDriver 설치 실패.")
        else:
            print("Chrome 버전에 맞는 ChromeDriver 버전을 찾을 수 없습니다.")
    else:
        print("Chrome 버전을 가져올 수 없습니다.")