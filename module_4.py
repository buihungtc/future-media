import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
import os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import requests
import json
import isodate
from datetime import timedelta
from module_get_info_chanel import get_channel_info_by_url
from module_get_link_video import get_latest_video_links_by_handle
import threading
from selenium.webdriver.common.keys import Keys
from datetime import datetime
from dotenv import load_dotenv
import os
from module_initialize_driver import init_driver_from_env
import urllib.parse



def extract_hashtags(text):
    hashtags = re.findall(r'#\w+', text)
    return ', '.join(hashtags)
def phan_tich_chu_de(userId,ten_nhom,chuoi_tu_khoa, time_range,view_min = 0,view_max = 10000000000000):
    # api_key = "AIzaSyCNCzV0Nxh2VlPC5Qhdh4mgxWTmPBXVIaw"
    # Lấy thời gian hiện tại
    # file_path = f"function4/{userId}_{ngay_thang_nam}_{tu_khoa}_{time_range}.json"
    load_dotenv(".env")
    CHATGPT_KEY = os.getenv("CHATGPT_KEY")
    today = datetime.now()

    # Format thành chuỗi viết liền: ddmmyyyy
    ngay_thang_nam = today.strftime("%d%m%Y%H%M%S")
    file_path = f"function4/{userId}_{ngay_thang_nam}_{ten_nhom}_{time_range}.json"
    # Ghi vào file input.json
    # Nếu file không tồn tại hoặc rỗng → tạo file với nội dung []
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump([], file, indent=4)
        print(f"Đã tạo mới '{file_path}' với nội dung là list rỗng.")

    # Sau đó mở file để đọc dữ liệu và xử lý tiếp như bình thường
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    tu_khoa_list = [tu_khoa.strip() for tu_khoa in chuoi_tu_khoa.split(',') if tu_khoa.strip() != '']
    driver = init_driver_from_env()
    # driver.get("https://www.youtube.com")
    # driver.execute_script("window.open('https://example.com', '_blank');")
    # Lặp qua từng từ khóa
    for tu_khoa in tu_khoa_list:
        # os.system("taskkill /f /im chrome.exe")
        # os.system("taskkill /f /im chromedriver.exe")
        # Mở trình duyệt với Profile 1
        # file_path = f"function4/{userId}_{ngay_thang_nam}_{tu_khoa}_{time_range}.json"
        # driver = init_driver_from_env()
        driver.get("https://www.youtube.com")
        # driver.refresh()
        sleep(2)  # Đợi trình duyệt tải xong
        # Tìm phần tử theo name
        search_box = driver.find_element(By.NAME, "search_query")
        # search_box.clear()
        # Gửi chuỗi 'xin chao' và nhấn Enter
        search_box.send_keys(tu_khoa)
        search_box.send_keys(Keys.ENTER)
        sleep(5)
        # Tìm phần tử theo thuộc tính aria-label và click
        # filter_button = driver.find_element(By.CSS_SELECTOR, '[aria-label="Bộ lọc tìm kiếm"]')
        filter_button = driver.find_element(By.CSS_SELECTOR, '[aria-label="Bộ lọc tìm kiếm"], [aria-label="Search filters"]')
        filter_button.click()
        sleep(1)
        element = driver.find_element(By.XPATH, '//yt-formatted-string[text()="4 - 20 minutes" or text()="4 — 20 phút"]')
        driver.execute_script("arguments[0].click();", element)
        sleep(1)
        if time_range == "week":
            element = driver.find_element(By.XPATH, '//yt-formatted-string[text()="Tuần này" or text()="This week"]')
            driver.execute_script("arguments[0].click();", element)
        elif time_range == "month":
            element = driver.find_element(By.XPATH, '//yt-formatted-string[text()="Tháng này" or text()="This month"]')
            driver.execute_script("arguments[0].click();", element)
            sleep(1)
        sleep(5)
        for i in range(5):
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            sleep(1)
        # Lấy tất cả phần tử có id = "channel-info"
        # channel_infos = driver.find_elements(By.ID, "channel-info")
        a_tags = driver.find_elements(By.ID, "channel-thumbnail")
        # Duyệt từng phần tử để lấy href từ thẻ <a> con trực tiếp
        # for idx, info in enumerate(channel_infos):
        driver.execute_script("window.open('https://example.com', '_blank');")
        x=1
        processed_urls = []
        for idx, a_tag in enumerate(a_tags):
            
            # print(a_tag.get_attribute("outerHTML"))
            # a_tag = element.find_element(By.ID, "channel-thumbnail")
            url = a_tag.get_attribute("href")
            url = urllib.parse.unquote(url, encoding='utf-8')
            if url in processed_urls:
                print(f"URL {url} đã được xử lý, bỏ qua...")
                continue  # Bỏ qua và chạy lần lặp tiếp theo
            processed_urls.append(url)
            print('dương dan la'+ url)
            
            fields = ['title', 'description', 'publishedAt', 'thumbnails',
                'subscriberCount', 'viewCount', 'videoCount', 'country']
            info = get_channel_info_by_url(url, fields)


            # channelId, ten_kenh, mo_ta, ngay_tao, avata, tong_sub, tong_view, tong_video, quoc_gia = get_channel_info_by_url(url, api_key)
            if int(info['viewCount']) >= int(view_min) and int(info['viewCount']) <= int(view_max):
                pass
            else:
                continue

            start_date_str = info['publishedAt']
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

            # Ngày hiện tại
            today = datetime.today()

            # Tính số ngày chênh lệch
            delta = today - start_date

            n = delta.days
            tan_suat_dang = round(int(info['videoCount']) / (n / 7), 1)
            API_KEY = CHATGPT_KEY
            API_URL = 'https://api.openai.com/v1/chat/completions'
            # 1️⃣ Prompt nhận diện ngôn ngữ
            lang_prompt = f"Văn bản sau viết bằng ngôn ngữ nào? Trả lời CHỈ bằng tên ngôn ngữ. Không thêm bất kỳ chữ nào khác:\n\n{info['description']}"
            # Cấu hình headers
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            # Hàm gọi API OpenAI
            def chat_with_gpt(prompt):
                data = {
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0,
                    "max_tokens": 500
                }
                response = requests.post(API_URL, headers=headers, json=data)
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    return f"[Lỗi: {response.status_code}]"
            # 👉 Nhận diện ngôn ngữ
            language = chat_with_gpt(lang_prompt)
            hashtags = extract_hashtags(info['description'])
            # print(channelId, ten_kenh, mo_ta, ngay_tao, avata, tong_sub, tong_view, tong_video, quoc_gia)
            # Đóng tất cả các Chrome đang mở
            # os.system("taskkill /f /im chrome.exe")
            # os.system("taskkill /f /im chromedriver.exe")
            # Mở trình duyệt với Profile 1
            # driver = open_browser_with_profile()
            tabs = driver.window_handles
            driver.switch_to.window(tabs[1])
            driver.get(url)
            sleep(2)  # Đợi trình duyệt tải xong
            # Lấy tất cả div có class = yt-tab-shape-wiz__tab
            tab_elements = driver.find_elements(By.CLASS_NAME, 'yt-tab-shape-wiz__tab')
            texts = [el.text.strip() for el in tab_elements if el.text.strip()]

            # Kiểm tra nội dung để xác định thể loại kênh
            contains_video = any("Video" in text for text in texts)
            contains_shorts = any("Shorts" in text for text in texts)

            # Gán giá trị genre
            if contains_video and contains_shorts:
                channel_genre = "hybrid"
            elif contains_video:
                channel_genre = "long"
            elif contains_shorts:
                channel_genre = "Shorts"
            else:
                channel_genre = "unknown"
            try:
                wait = WebDriverWait(driver, 10)
                button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[normalize-space(text())='View channel stats']"))
                )
                button.click()
                class_selector = ".vidiq-c-fvFDqp.vidiq-c-fvFDqp-hyvuql-weight-bold.vidiq-c-fvFDqp-hkUmio-size-4xl.vidiq-c-fvFDqp-ihwNaBc-css"
                elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, class_selector)))
                views_30d = elements[0].text
                subs_30d = elements[1].text
                video_30d = elements[2].text
            except:
                views_30d = ''
                subs_30d = ''
                video_30d = ''
            # Chạy đoạn JavaScript trong trình duyệt để thay đổi nội dung
            sleep(1)
            try:
                wait = WebDriverWait(driver, 10)
                menu_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'i.material-icons.menu')))
                
                # Click trực tiếp
                menu_icon.click()
                print("Đã click vào biểu tượng menu.")

                wait = WebDriverWait(driver, 10)
                last_7_days = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//span[normalize-space()="Last 7 Days"]')
                ))
                
                last_7_days.click()
                print("Đã click vào 'Last 7 Days'")
                class_selector = ".vidiq-c-fvFDqp.vidiq-c-fvFDqp-hyvuql-weight-bold.vidiq-c-fvFDqp-hkUmio-size-4xl.vidiq-c-fvFDqp-ihwNaBc-css"

                sleep(2)
                elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, class_selector)))
                views_7d = elements[0].text
                print("Views 7d:", views_7d)
            except:
                views_7d =''
            # Tìm phần tử có class = vidiq-range-selector-head
            # try:
            #     range_selector = driver.find_element(By.CLASS_NAME, 'vidiq-range-selector-head')
            #     print("vidiq-range-selector-head text:", range_selector.text.strip())
            # except Exception as e:
            #     print("Không tìm thấy phần tử hoặc xảy ra lỗi:", str(e))
            print("Views 30d:", views_30d)
            print("Subs 30d:", subs_30d)
            print("Video 30d:", video_30d)
            # Tìm tất cả phần tử có class 'keyword-inner'
            try:
                elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "keyword-inner")))
                # Lấy text và nối thành chuỗi, loại bỏ khoảng trắng thừa
                texts = [el.text.strip() for el in elements if el.text.strip()]
                tu_khoa_SEO = ", ".join(texts)
            except:
                tu_khoa_SEO = ""


            # file_path = f"function4/{userId}_{ngay_thang_nam}_{tu_khoa}_{time_range}.json"
            # if os.path.exists(file_path):
            #     with open(file_path, "w", encoding="utf-8") as f:
            #         json.dump([], f, ensure_ascii=False, indent=2)
            #     data = []
            # else:
            #     data = []
            # Bước 2: Đảm bảo data là list
            # if not isinstance(data, list):
            #     data = [data]
            # new_data = {
            #     "channel_name": info['title'],
            #     "avata": info['thumbnails'],
            #     "channel_description": info['description'],
            #     "languge": language,
            #     "quoc_gia": info['country'],
            #     "channel_creation_date": info['publishedAt'],
            #     "channel_genre": channel_genre,
            #     "posting_frequency": tan_suat_dang,
            #     "total_video": info['videoCount'],
            #     "video_30d": video_30d,
            #     "total_view": info['viewCount'],
            #     "views_7d": views_7d,
            #     "views_30d": views_30d,
            #     "total_sub": info['subscriberCount'],
            #     "subs_30d": subs_30d,
            #     "hashtags": hashtags,
            #     "SEO_keywords": tu_khoa_SEO
            # }
            # Bước 3: Thêm chuỗi mới vào list
            # data.append(new_data)
            # # Bước 4: Ghi lại file
            # with open(file_path, "w", encoding="utf-8") as f:
            #     json.dump(data, f, ensure_ascii=False, indent=4)
            # Bước 1: Đọc file JSON
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            # Bước 2: Xác định tu_khoa mục tiêu
            target_key = tu_khoa

            # Bước 3: Channel mới cần thêm vào
            new_data = {
                "channel_name": info['title'],
                "url":url,
                "avata": info['thumbnails'],
                "channel_description": info['description'],
                "languge": language,
                "quoc_gia": info['country'],
                "channel_creation_date": info['publishedAt'],
                "channel_genre": channel_genre,
                "posting_frequency": tan_suat_dang,
                "total_video": info['videoCount'],
                "video_30d": video_30d,
                "total_view": info['viewCount'],
                "views_7d": views_7d,
                "views_30d": views_30d,
                "total_sub": info['subscriberCount'],
                "subs_30d": subs_30d,
                "hashtags": hashtags,
                "SEO_keywords": tu_khoa_SEO
            }

            # Bước 4: Kiểm tra và thêm
            for item in data:
                if item.get("tu_khoa") == target_key:
                    item["value"].append(new_data)
                    break
            else:
                # Không tìm thấy tu_khoa → tạo mới
                data.append({
                    "tu_khoa": target_key,
                    "value": [new_data]
                })

            # Bước 5: Ghi lại file
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

            # driver.close()
            driver.switch_to.window(driver.window_handles[0])
            if x>=10:
                break
            x+=1
            
    # Đóng trình duyệt
    driver.quit()
    # sleep(2)
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)  # data là dict hoặc list tùy nội dung
    return data

if __name__ == "__main__":
    API_KEY = "AIzaSyCNCzV0Nxh2VlPC5Qhdh4mgxWTmPBXVIaw"
    phan_tich_chu_de('10',"con nguoi","âm nhạc, nghệ thuật", "week")