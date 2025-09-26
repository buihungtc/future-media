import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import datetime
from module_sub_module_5 import get_channel_info_by_url, get_video_ids_by_channel, get_average_video_duration, format_duration
from module_initialize_driver import init_driver_from_env
from module_youtube_api_manager import YouTubeAPIManager
yt_api = YouTubeAPIManager()
import re

def update_existing_data(old_data, new_data):
    """
    Cập nhật dữ liệu cũ với dữ liệu mới, chỉ ghi đè các trường có giá trị mới
    """
    for key, new_value in new_data.items():
        # Chỉ cập nhật nếu giá trị mới không rỗng/None/0
        if new_value and new_value != "" and new_value != 0 and new_value != 0.0:
            old_data[key] = new_value
        # Đặc biệt cho timestamp, luôn cập nhật
        elif key == "time_stamp":
            old_data[key] = new_value
    
    return old_data

def get_channel_module_5(userId, url):
    today = datetime.now()
    ngay_thang_nam = today.strftime("%d%m%Y")
    timestamp = today.strftime("%d%m%Y_%H%M%S")
    
    # Khởi tạo các biến với giá trị mặc định
    ten_kenh = avata = quoc_gia = ngay_tao = tong_sub = tong_view = tong_video = ""
    views_30d = subs_30d = thoi_luong_TB = ""
    tan_suat_dang = 0.0

    try:
        # Lấy thông tin kênh
        channel_info = get_channel_info_by_url(url)
        if channel_info:
            ten_kenh, ngay_tao, avata, tong_sub, tong_view, tong_video, quoc_gia = channel_info
    except Exception as e:
        print(f"Lỗi khi lấy thông tin kênh: {str(e)}")

    try:
        driver = init_driver_from_env()
        if driver:
            driver.get(url)
            sleep(2)
            wait = WebDriverWait(driver, 10)
            
            # Xử lý thống kê 30 ngày
            try:
                button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'View channel stats')]")))
                button.click()
                class_selector = ".vidiq-c-fvFDqp.vidiq-c-fvFDqp-hyvuql-weight-bold.vidiq-c-fvFDqp-hkUmio-size-4xl.vidiq-c-fvFDqp-ihwNaBc-css"
                elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, class_selector)))
                views_30d = elements[0].text if len(elements) > 0 else ""
                subs_30d = elements[1].text if len(elements) > 1 else ""
            except Exception as e:
                print(f"Lỗi khi lấy thống kê 30 ngày: {str(e)}")
            
            driver.quit()
    except Exception as e:
        print(f"Lỗi trong quá trình xử lý trình duyệt: {str(e)}")

    # Xử lý tần suất đăng
    try:
        start_date = datetime.strptime(ngay_tao, "%Y-%m-%d") if ngay_tao else datetime.now()
        delta = datetime.today() - start_date
        n = delta.days if delta.days > 0 else 1
        tan_suat_dang = round(int(tong_video)/(n/7), 1) if tong_video and n else 0.0
    except Exception as e:
        print(f"Lỗi tính tần suất đăng: {str(e)}")

    # Xử lý thời lượng trung bình
    try:
        video_ids = get_video_ids_by_channel(url, max_results=20)
        avg_duration_sec = get_average_video_duration(video_ids) if video_ids else 0
        thoi_luong_TB = format_duration(avg_duration_sec) if avg_duration_sec else ""
    except Exception as e:
        print(f"Lỗi khi lấy thời lượng video: {str(e)}")

    # Tạo dữ liệu mới
    new_data = {
        "opponentUrl": url,
        "channel_name": ten_kenh or "",
        "avata": avata or "",
        "quoc_gia": quoc_gia or "",
        "channel_creation_date": ngay_tao or "",
        "posting_frequency": tan_suat_dang or 0.0,
        "total_video": tong_video or "",
        "average_duration": thoi_luong_TB or "",
        "total_view": tong_view or "",
        "views_30d": views_30d or "",
        "total_sub": tong_sub or "",
        "subs_30d": subs_30d or "",
        "time_stamp": timestamp
    }

    # Xử lý file JSON
    try:
        cleaned_url = re.sub(r'[\\/:*?"<>|]', '_', url)
        file_path = f"function5/{cleaned_url}.json"
        
        data = []
        
        # Đọc dữ liệu cũ
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []

        # Tìm và cập nhật record có cùng opponentUrl
        found = False
        for i, record in enumerate(data):
            if record.get("opponentUrl") == url:
                # Cập nhật record hiện có với dữ liệu mới
                data[i] = update_existing_data(record.copy(), new_data)
                found = True
                break
        
        # Nếu không tìm thấy record nào, thêm mới
        if not found:
            data.append(new_data)

        # Ghi lại file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return data
    except Exception as e:
        print(f"Lỗi khi xử lý file JSON: {str(e)}")
        return []

if __name__ == "__main__":
    # info = get_channel_module_5('10', 'https://www.youtube.com/channel/UCh-A27eKaTrPM_gkfIw_-mA')
    info = get_channel_module_5('10', 'https://www.youtube.com/@AnimalHT2721')

    print(json.dumps(info, indent=2))