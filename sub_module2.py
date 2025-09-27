import schedule
import time
from datetime import datetime
from module_2 import chay

# Đây là hàm bạn muốn chạy
def my_task():
    chay('1','views_7d')
    chay('1','views_30d')
    chay('1','views_3m')
    chay('1','subs_7d')
    chay('1','subs_30d')
    chay('1','subs_3m')

# Lên lịch chạy hàm vào 00:00 và 12:00 hàng ngày
schedule.every().day.at("00:00").do(my_task)
schedule.every().day.at("10:34").do(my_task)

print("Đang chạy lịch trình... Nhấn Ctrl+C để dừng.")

# Vòng lặp chính kiểm tra lịch
while True:
    schedule.run_pending()
    time.sleep(1)
