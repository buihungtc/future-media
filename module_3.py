import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
import os
import re
from urllib.parse import urlparse, parse_qs
import json
from urllib.parse import urlparse, urljoin
import threading
import uuid
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from module_get_info_chanel import get_channel_info_by_url
from module_get_link_video import get_latest_video_links_by_handle
from module_sub_module3 import sub_module3
from module_initialize_driver import init_driver_from_env
from dotenv import load_dotenv
import os

# Global thread registry and stop flags
thread_registry = {}
stop_flags = {}

def extract_hashtags(text):
    hashtags = re.findall(r'#\w+', text)
    return ', '.join(hashtags)
# def fix_youtube_url(url):
#     parsed = urlparse(url)
#     if 'youtube.com' not in parsed.netloc:
#         return url  # Không phải link YouTube thì giữ nguyên

#     # Kiểm tra nếu đã có /videos hoặc /videos/
#     if parsed.path.rstrip('/') == '/videos':
#         return url  # Đã đúng định dạng

#     # Thêm /videos vào cuối path
#     new_url = urljoin(url.rstrip('/') + '/', 'videos')
#     return new_url
def fix_youtube_url(url):
    parsed = urlparse(url)
    if 'youtube.com' not in parsed.netloc:
        return url  # Không phải link YouTube thì giữ nguyên

    # Trích xuất channel handle từ path (phần @username)
    match = re.search(r'/@([^/]+)', parsed.path)
    if match:
        channel_handle = match.group(1)
        # Tạo URL mới với format chuẩn + /videos
        base_url = f"{parsed.scheme}://{parsed.netloc}/@{channel_handle}"
        return f"{base_url}/videos"
    
    # Nếu không tìm thấy pattern @username, kiểm tra format cũ
    if '/channel/' in parsed.path or '/c/' in parsed.path or '/user/' in parsed.path:
        # Lấy phần path cho đến khi gặp dấu / thứ 2
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            base_path = f"/{path_parts[0]}/{path_parts[1]}"
            base_url = f"{parsed.scheme}://{parsed.netloc}{base_path}"
            return f"{base_url}/videos"
    
    return url  # Trả về URL gốc nếu không match pattern nào
def extract_video_id_from_url(url):
    """Trích xuất video ID từ URL dạng YouTube"""
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    return parse_qs(parsed.query).get("v", [None])[0]


def get_channel_info(userId, url):
    load_dotenv("backend2/.env")
    CHATGPT_KEY = os.getenv("CHATGPT_KEY")
    today = datetime.now()
    ngay_thang_nam = today.strftime("%d%m%Y")
    fields = ['title', 'description', 'publishedAt', 'thumbnails',
            'subscriberCount', 'viewCount', 'videoCount', 'country']
    info = get_channel_info_by_url(url, fields)
    ten_kenh = info['title']
    mo_ta = info['description']
    ngay_tao = info['publishedAt']
    avata = info['thumbnails']
    tong_sub = info['subscriberCount']
    tong_view = info['viewCount']
    tong_video = info['videoCount']
    quoc_gia = info['country']
    hashtags = extract_hashtags(mo_ta)
    
    try:
        API_URL = 'https://api.openai.com/v1/chat/completions'

        # 1️⃣ Prompt nhận diện ngôn ngữ
        lang_prompt = f"Văn bản sau viết bằng ngôn ngữ nào? Trả lời CHỈ bằng tên ngôn ngữ. Không thêm bất kỳ chữ nào khác:\n\n{mo_ta}"
        headers = {
            "Authorization": f"Bearer {CHATGPT_KEY}",
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
                "max_tokens": 100
            }
            response = requests.post(API_URL, headers=headers, json=data)
            # if response.status_code == 200:
            #     result = response.json()
            #     # return result['choices'][0]['message']['content'].strip()
            # else:
            #     # return f"[Lỗi: {response.status_code}]"
            #     return ""
        # 👉 Nhận diện ngôn ngữ
        language = chat_with_gpt(lang_prompt)
    except:
        language = ""

    start_date = datetime.strptime(ngay_tao, "%Y-%m-%d")
    delta = datetime.today() - start_date
    tan_suat_dang = round(int(tong_video) / (delta.days / 7), 1)
    
    driver = init_driver_from_env()
    driver.get(url)
    sleep(5)

    try:
        tab_elements = driver.find_elements(By.CLASS_NAME, 'yt-tab-shape-wiz__tab')
        texts = [el.text.strip() for el in tab_elements if el.text.strip()]
        contains_video = any("Video" in text for text in texts)
        contains_shorts = any("Shorts" in text for text in texts)
        channel_genre = "hybrid" if contains_video and contains_shorts else "long" if contains_video else "Shorts" if contains_shorts else "unknown"
    except:
        channel_genre = "unknown"

    try:
        wait = WebDriverWait(driver, 10)
        button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space(text())='View channel stats']")))
        button.click()
        class_selector = ".vidiq-c-fvFDqp.vidiq-c-fvFDqp-hyvuql-weight-bold.vidiq-c-fvFDqp-hkUmio-size-4xl.vidiq-c-fvFDqp-ihwNaBc-css"
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, class_selector)))
        views_30d, subs_30d, video_30d = elements[0].text, elements[1].text, elements[2].text
    except:
        views_30d, subs_30d, video_30d = '', '', ''

    try:
        elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "keyword-inner")))
        texts = [el.text.strip() for el in elements if el.text.strip()]
        tu_khoa_SEO = ", ".join(texts)
    except:
        tu_khoa_SEO = ''
    fixed_url = fix_youtube_url(url)
    driver.get(fixed_url)
    sleep(2)
    h = 1
    href =''
    while h <10:
        try:
            print("thuw lan thu ", h)
            element = driver.find_element(
                By.CSS_SELECTOR,
                '#video-title-link.yt-simple-endpoint.focus-on-expand.style-scope.ytd-rich-grid-media'
            )
            href = element.get_attribute('href')
            print("Link video đầu tiên:", href)
            break
        except:
            print("Không tìm thấy phần tử phù hợp.")
            sleep(1)
            h+=1
        
    driver.quit()
    
    # Lấy video ID mới nhất để truyền vào thread (không lưu vào JSON)
    parsed_url = urlparse(href)
    last_video_id = parse_qs(parsed_url.query).get("v", [None])[0]
    print("video gaanf nhaat tim duoc laf" , last_video_id)
    cleaned_url = re.sub(r'[\\/:*?"<>|]', '_', url)
    print(cleaned_url)
    file_path = f"backend2/function3/{cleaned_url}.json"
    data = []

    new_data = {
        "opponentUrl": url,
        "channel_name": ten_kenh,
        "avata": avata,
        "channel_description": mo_ta,
        "quoc_gia": quoc_gia,
        "channel_creation_date": ngay_tao,
        "channel_genre": channel_genre,
        "posting_frequency": tan_suat_dang,
        "total_video": tong_video,
        "video_30d": video_30d,
        "language": language,
        "total_view": tong_view,
        "views_30d": views_30d,
        "total_sub": tong_sub,
        "subs_30d": subs_30d,
        "hashtags": hashtags,
        "SEO_keywords": tu_khoa_SEO,
        "videos": []
    }
    data.append(new_data)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    thread_id = str(uuid.uuid4())
    stop_event = threading.Event()
    # Thay đổi parameter từ tong_video sang last_video_id
    t = threading.Thread(target=loop_check_new_video, args=(url, last_video_id, stop_event, file_path), daemon=False)
    thread_registry[thread_id] = t
    stop_flags[thread_id] = stop_event
    t.start()

    def update_thread_in_db():
        try:
            update_url = "http://123.24.132.227:3001/api/functions/3/update-threadId"
            payload = {"competitorUrl": url, "threadId": thread_id}
            response = requests.post(update_url, json=payload)
            print(f"[UPDATE] Status: {response.status_code}, Message: {response.text}")
        except Exception as e:
            print(f"[ERROR] Failed to update threadId: {e}")

    threading.Thread(target=update_thread_in_db, daemon=True).start()

    return data

def loop_check_new_video(url, last_video_id, stop_event, file_path):
    while not stop_event.is_set():
        sleep(3600)
        try:
            fixed_url = fix_youtube_url(url)
            driver = init_driver_from_env()
            driver.get(fixed_url)
            # driver.execute_script("window.scrollBy(0, window.innerHeight);")
            # sleep(2)
            # Lấy 10 phần tử video đầu tiên
            elements = driver.find_elements(
                By.CSS_SELECTOR,
                '#video-title-link.yt-simple-endpoint.focus-on-expand.style-scope.ytd-rich-grid-media'
            )[:10]

            # Lấy href -> chuyển thành video ID
            video_ids = []
            for el in elements:
                href = el.get_attribute("href")
                video_id = extract_video_id_from_url(href)
                if video_id:
                    video_ids.append(video_id)

            # So sánh với last_video_id, lấy các video mới hơn (nằm trước nó)
            if last_video_id in video_ids:
                index = video_ids.index(last_video_id)
                latest_video_ids= video_ids[:index]  # Các video mới hơn
            else:
                latest_video_ids = video_ids  # Nếu không tìm thấy, giả sử tất cả là mới
            
            new_video_ids = latest_video_ids
            new_video_count = len(latest_video_ids)
            
            if new_video_count > 0:
                print(f'🎯 Tìm được {new_video_count} video mới')   
                print(f'New video IDs: {new_video_ids}')
                
                # Sử dụng trực tiếp video IDs làm video links
                video_links = new_video_ids
                
                print(f'Video links: {video_links}')
                
                # Chạy thread xử lý video mới
                t = threading.Thread(target=sub_module3, args=(video_links, file_path, url), daemon=True)
                t.start()
                
                # Cập nhật total_video mới nhất vào JSON file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Lấy total_video hiện tại từ API
                    fields = ['videoCount']
                    info = get_channel_info_by_url(url, fields)
                    current_total_video = info['videoCount']
                    
                    # Cập nhật total_video với giá trị mới nhất
                    if data and len(data) > 0:
                        data[0]["total_video"] = current_total_video
                        
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                        
                        print(f"✅ Updated total_video to {current_total_video} in {file_path}")
                
                except Exception as e:
                    print(f"❌ Error updating total_video: {e}")
                
                # Cập nhật biến local
                last_video_id = latest_video_ids[0]
            else:
                print("ℹ️ Không có video mới")
            
        except Exception as e:
            print(f"❌ Error in loop_check_new_video: {e}")
        driver.quit()
        print('🔄 Chạy vòng lặp tiếp theo sau 1 giờ')
        # sleep(3600)  # 1 giờ = 3600 giây
        # sleep(1200)
if __name__ == "__main__":
    # Test function
    get_channel_info("2","https://www.youtube.com/@truyenhinh4k")
