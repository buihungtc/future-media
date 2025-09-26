from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from dotenv import load_dotenv
import chromedriver_autoinstaller
import os
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def init_driver_from_env(env_path=".env", headless=False, wait_between=1):
    """
    Đọc các user-data-dir từ file .env và thử khởi tạo driver với từng profile.
    
    :param env_path: Đường dẫn tới file .env
    :param headless: Bật/tắt chế độ headless
    :param wait_between: Giây chờ giữa các lần thử
    :return: driver Selenium nếu thành công, ngược lại None
    """
    load_dotenv(env_path)
    userdata_raw = os.getenv("USERDATA_PATHS", "")
    userdata_paths = [p.strip() for p in userdata_raw.split(",") if p.strip()]
    
    # chromedriver_autoinstaller.install()

    for path in userdata_paths:
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            # Tự động tải và cài đặt chromedriver
            service = Service(ChromeDriverManager().install())
            profile = 'Profile 1'
            options = webdriver.ChromeOptions()
            options.add_argument(f"--user-data-dir={path}")
            options.add_argument(f"--profile-directory={profile}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # Thêm mới
            options.add_argument("--start-fullscreen")
            if headless:
                options.add_argument("--headless=new")

            driver = webdriver.Chrome(service=service,options=options)
            print(f"[+] Dùng profile: {path}")
            return driver

        except WebDriverException as e:
            print(f"[!] Không thể dùng profile {path}: {e}")
            time.sleep(wait_between)
            continue

    print("[x] Không khởi tạo được driver từ bất kỳ profile nào.")
    return None