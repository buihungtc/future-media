import threading
import os
import schedule
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from module_1 import main


def worker(country):
    """
    Worker function để chạy trong mỗi thread
    """
    try:
        result = main(country)
        print(result)
        return result
    except Exception as e:
        print(f"Lỗi khi xử lý {country}: {e}")
        return None

def load_countries_from_json():
    """
    Đọc danh sách countries từ file JSON
    """
    config_file = 'config.json'
    
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
            countries = config_data.get('countries', [])
            return countries
    except FileNotFoundError:
        print(f"File {config_file} không tồn tại")
        return []
    except json.JSONDecodeError:
        print(f"Lỗi định dạng JSON trong file {config_file}")
        return []
    except Exception as e:
        print(f"Lỗi khi đọc file {config_file}: {e}")
        return []

def multithread():
    """
    Hàm chính để chạy multithreading job
    """
    print(f"\n=== Bắt đầu job lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # Lấy danh sách các nước từ file JSON
    countries = load_countries_from_json()
    
    if not countries:
        print("Không tìm thấy danh sách countries hoặc danh sách rỗng")
        return
    
    print(f"Danh sách các nước: {countries}")
    
    # Tạo ThreadPoolExecutor với 3 threads
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Chạy function cho tất cả countries song song
        results = list(executor.map(worker, countries))
    
    print("Hoàn thành tất cả các threads!")
    print(f"Kết quả: {results}")
    print(f"=== Kết thúc job lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

def run_scheduler():
    """
    Khởi động scheduler
    """
    # Lên lịch chạy job
    schedule.every().day.at("00:00").do(multithread)  # 0 giờ
    schedule.every().day.at("12:00").do(multithread)  # 12 giờ
    
    print("Scheduler đã được khởi động!")
    print("Chương trình sẽ chạy lúc 00:00 và 12:00 hàng ngày")
    print("Nhấn Ctrl+C để dừng chương trình")
    print("Đang chờ đến giờ chạy...")
    
    # Vòng lặp chờ schedule
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Kiểm tra mỗi 60 giây
    except KeyboardInterrupt:
        print("\nChương trình đã được dừng bởi người dùng")

if __name__ == "__main__":
    run_scheduler()