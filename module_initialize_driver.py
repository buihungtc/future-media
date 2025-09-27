from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from dotenv import load_dotenv
import os
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# def init_driver_from_env(env_path=".env", headless=False, wait_between=1, window_layout="top"):
def init_driver_from_env(env_path=".env", headless=False, wait_between=1, window_layout=None):
    """
    Đọc các user-data-dir từ file .env và thử khởi tạo driver với từng profile.
    
    :param env_path: Đường dẫn tới file .env
    :param headless: Bật/tắt chế độ headless
    :param wait_between: Giây chờ giữa các lần thử
    :param window_layout: Vị trí/kích thước cửa sổ (top/bottom/top_half/bottom_half). Mặc định 'top'.
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
            if not window_layout:
                options.add_argument("--start-fullscreen")
            if headless:
                options.add_argument("--headless=new")

            driver = webdriver.Chrome(service=service,options=options)
            # Đặt vị trí/kích thước cửa sổ nếu có yêu cầu
            if not headless and window_layout:
                try:
                    aw, ah = driver.execute_script("return [window.screen.availWidth, window.screen.availHeight];")
                    half_h = int(ah // 2)
                    if str(window_layout).lower() in ["top", "top_half", "top-half"]:
                        driver.set_window_position(0, 0)
                        driver.set_window_size(int(aw), half_h)
                    elif str(window_layout).lower() in ["bottom", "bottom_half", "bottom-half"]:
                        driver.set_window_position(0, half_h)
                        driver.set_window_size(int(aw), ah - half_h)
                except Exception:
                    pass
            print(f"[+] Dùng profile: {path}")
            return driver

        except WebDriverException as e:
            print(f"[!] Không thể dùng profile {path}: {e}")
            time.sleep(wait_between)
            continue

    print("[x] Không khởi tạo được driver từ bất kỳ profile nào.")
    return None