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
from dotenv import load_dotenv
import requests
import json
import isodate
from datetime import timedelta
from datetime import datetime
from module_initialize_driver import init_driver_from_env
from module_youtube_api_manager import YouTubeAPIManager
yt_api = YouTubeAPIManager()

def get_video_transcript(id_video):
    params = {
        'part': 'snippet',
        'id': id_video,
    }
    url = 'https://www.googleapis.com/youtube/v3/videos'
    data = yt_api.make_request(url, params=params)
    
    if 'items' not in data or not data['items']:
        return "Không tìm thấy video hoặc ID không hợp lệ."
    
    return data['items'][0]['snippet']['description']

def get_video_info(id_video):
    params = {
        'part': 'snippet,statistics,contentDetails',
        'id': id_video,
    }
    url = 'https://www.googleapis.com/youtube/v3/videos'
    data = yt_api.make_request(url, params=params)

    if 'items' not in data or not data['items']:
        return "Không tìm thấy video hoặc ID không hợp lệ."

    video_data = data['items'][0]

    published_at = video_data['snippet'].get('publishedAt', 'Không rõ ngày đăng')
    stats = video_data.get('statistics', {})
    iso_duration = video_data['contentDetails']['duration']
    thoi_luong = str(isodate.parse_duration(iso_duration) - timedelta(seconds=1))
    like_count = stats.get('likeCount', 'Không có')
    comment_count = stats.get('commentCount', 'Không có')

    return {
        "published_at": published_at,
        "duration": thoi_luong,
        "like_count": like_count,
        "comment_count": comment_count
    }

def main(nation, userId=1):
    load_dotenv(".env")
    CHATGPT_KEY = os.getenv("CHATGPT_KEY")
    today = datetime.now()

    # Format thành chuỗi viết liền: ddmmyyyy
    ngay_thang_nam = today.strftime("%d%m%Y%H%M%S")
    # Kiểm tra và khởi tạo file module_2.json
    file_path = f"function1/{nation}.json"
    file_path_old = f"function1/{nation}_{ngay_thang_nam}.json"

    # Vòng lặp để retry khi file rỗng
    max_retries = 3  # Giới hạn số lần thử để tránh vòng lặp vô hạn
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"Lần thử {retry_count + 1}/{max_retries}")
            
            # Cách 1: Ghi đè trực tiếp
            with open(file_path_old, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)

            driver = init_driver_from_env()
            sleep(1)
            driver.get("https://www.youtube.com")
            sleep(10)  # Đợi trình duyệt tải xong
            

            span_element = driver.find_element(By.XPATH, "//span[text()='Most Viewed' or text()='Được Xem Nhiều Nhất']")
            driver.execute_script("arguments[0].click();", span_element)

            sleep(2)
            
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, ".css-pksui6.es0z3u0")
                if len(elements) >= 6:
                    parent2 = elements[1]
                    child_div = parent2.find_element(By.XPATH, ".//div[normalize-space(text())='Any'or normalize-space(text())='Bất kỳ']")
                    child_div.click()
                    input_element = driver.find_element(By.ID, "vidiq-filter-selector-section-radio-2")
                    driver.execute_script("arguments[0].click();", input_element)
                    save_button = parent2.find_element(By.XPATH, ".//button[normalize-space(text())='Save'or normalize-space(text())='Lưu']")
                    driver.execute_script("arguments[0].click();", save_button)

                    parent = elements[5]
                    select = parent.find_element(By.TAG_NAME, "select")
                    select = Select(select)
                    select.select_by_visible_text(nation)
                else:
                    print("Không đủ 6 phần tử")
            except Exception as e:
                print(f"Lỗi: {str(e)}")
            
            sleep(2)
            i = 0

            try:
                # Vòng lặp while
                while i <= 11:
                    load_more_button = driver.find_element(By.XPATH, "//button[normalize-space(text())='Load more' or normalize-space(text())='Tải thêm']")
                    driver.execute_script("arguments[0].click();", load_more_button)
                    sleep(2)
                    i += 1
            except Exception as e:
                print(f"Lỗi khi tải thêm: {str(e)}")
            # Tìm elements và kiểm tra số lượng
            elements = driver.find_elements(By.CSS_SELECTOR, ".css-181vzoo.en4nady3")
            total_elements = len(elements)
            print(f"Tổng số phần tử tìm được: {total_elements}")
            
            # Xác định số phần tử cần xử lý (tối đa 200 hoặc số phần tử có sẵn)
            max_process = min(200, total_elements)
            print(f"Sẽ xử lý {max_process} phần tử")
            
            t = 0
            driver.execute_script("window.open('https://example.com', '_blank');")

            # Thay đổi điều kiện vòng lặp
            while t < max_process:
                try:
                    # Kiểm tra xem phần tử có tồn tại không trước khi truy cập
                    if t >= len(elements):
                        print(f"Đã hết phần tử tại vị trí {t}, dừng vòng lặp")
                        break
                    
                    print(f"Đang xử lý video {t + 1}/{max_process}")
                    
                    ten_kenh = elements[t].find_element(By.CSS_SELECTOR, ".css-g9bmdd.e1pit9a0").text
                    tieu_de = elements[t].find_element(By.CSS_SELECTOR, ".css-1thvnkg.en4nady0").text
                    img_element = elements[t].find_element(By.TAG_NAME, "img")
                    img_src = img_element.get_attribute("src")
                    id_video = img_src[-25:-14]
                    link_video = f"https://www.youtube.com/watch?v={id_video}"
                    child_elements = elements[t].find_elements(By.CSS_SELECTOR, ".css-1m551jz.e1pit9a0")
                    tong_view = child_elements[0].text
                    engagement_rate = child_elements[1].text
                    view_per_hour = elements[t].find_element(By.CSS_SELECTOR, ".css-xyox1z.e1pit9a0").text

                    tabs = driver.window_handles
                    driver.switch_to.window(tabs[1])
                    driver.get(link_video)
                    
                    while driver.current_url != link_video:
                        # print(f"🔁 Đường dẫn hiện tại là: {driver.current_url} — chưa khớp, đang vào lại...")
                        driver.get(link_video)
                        sleep(11)
                    sleep(1)

                    for i in range(2):
                        driver.execute_script("window.scrollBy(0, window.innerHeight);")
                        # print(f"📜 Scrolled {i + 1} time(s)")
                        sleep(1)

                    try:
                        transcript = get_video_transcript(id_video)
                        full_text = tieu_de + ' ' + transcript 
                        API_URL = 'https://api.openai.com/v1/chat/completions'

                        lang_prompt = f"Văn bản sau viết bằng ngôn ngữ nào? Trả lời CHỈ bằng tên ngôn ngữ. Không thêm bất kỳ chữ nào khác:\n\n{full_text}"
                        summary_prompt = f"""Tóm tắt ngắn gọn đoạn văn sau, giới hạn trong 300 từ. Chỉ trả về phần nội dung tóm tắt, không thêm bất kỳ thông tin hay lời giải thích nào khác. Nếu đoạn văn có các từ hoặc cụm từ lặp đi lặp lại (ví dụ: "music... music... music..."), hãy chỉ giữ lại một lần duy nhất (ví dụ: "music"). Đoạn văn cần tóm tắt là: \n\n{full_text}"""

                        headers = {
                            "Authorization": f"Bearer {CHATGPT_KEY}",
                            "Content-Type": "application/json"
                        }

                        def chat_with_gpt(prompt):
                            data = {
                                "model": "gpt-4o",
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0,
                                "max_tokens": 500
                            }
                            response = requests.post(API_URL, headers=headers, json=data)
                            if response.status_code == 200:
                                result = response.json()
                                return result['choices'][0]['message']['content'].strip()
                            else:
                                return f"[Lỗi: {response.status_code}]"

                        language = chat_with_gpt(lang_prompt)
                        summary = chat_with_gpt(summary_prompt)
                    except (TranscriptsDisabled, NoTranscriptFound):
                        summary = ""
                        language = ""
                    
                    info = get_video_info(id_video)
                    wait = WebDriverWait(driver, 10)
                    sleep(1)
                    
                    try:
                        first_divs = wait.until(EC.presence_of_all_elements_located((
                            By.CLASS_NAME,
                            "vidiq-c-bXbWpx.vidiq-c-bXbWpx-ejCoEP-direction-row.vidiq-c-bXbWpx-XefLA-wrap-true.vidiq-c-bXbWpx-iPJLV-css"
                        )))

                        second_div = first_divs[1]
                        divs = wait.until(lambda d: second_div.find_elements(
                                            By.XPATH, './/div[@class="css-1mcrx57 e4agnlm2"]'
                                        ))
                        results = []
                        sleep(0.5)

                        for div in divs:
                            try:
                                value_1 = div.find_element(By.CLASS_NAME, "vidiq-c-bXbWpx.vidiq-c-bXbWpx-ejCoEP-direction-row.vidiq-c-bXbWpx-ibdcynl-css").text.strip()
                            except:
                                pass

                            try:
                                value_2 = div.find_element(By.CLASS_NAME, "vidiq-c-bXbWpx.vidiq-c-bXbWpx-ejCoEP-direction-row.vidiq-c-bXbWpx-iBWeSx-css").text.strip()
                                value_2_float = float(value_2)
                            except:
                                value_2_float = -1

                            try:
                                value_3 = div.find_element(By.CLASS_NAME, "vidiq-c-bXbWpx.vidiq-c-bXbWpx-ejCoEP-direction-row.vidiq-c-bXbWpx-iliWTHm-css").text.strip()
                                value_3_digits = re.sub(r'\D', '', value_3)
                                value_3_int = int(value_3_digits)
                                print(value_3_int)
                            except:
                                value_3_int = float('inf')

                            if value_1:
                                results.append({
                                    "value_1": value_1,
                                    "value_2": value_2_float,
                                    "value_3": value_3_int
                                })
                        
                        min_value_3 = min(item['value_3'] for item in results)
                        candidates = [item for item in results if item['value_3'] == min_value_3]
                        best = max(candidates, key=lambda x: x['value_2'])
                        keywords = best['value_1']
                        hashtag = ','.join(item['value_1'] for item in results if item['value_1'] != keywords)
                    except:
                        keywords = ""
                        hashtag = ""

                    if os.path.exists(file_path_old):
                        with open(file_path_old, "r", encoding="utf-8") as f:
                            try:
                                data = json.load(f)
                            except json.JSONDecodeError:
                                data = []
                    else:
                        data = []

                    new_data = {
                        "channel_name": ten_kenh,
                        "title": tieu_de,
                        "link_video": link_video,
                        "total_views": tong_view,
                        "engagement_rate": engagement_rate,
                        "view_per_hour": view_per_hour,
                        "duration": info['duration'],
                        "summary": summary,
                        "language": language,
                        "img_src": img_src,
                        "published_at": info["published_at"],
                        "like_count": info['like_count'],
                        "comment_count": info['comment_count'],
                        "keywords": keywords,
                        "hashtag": hashtag
                    }
                    data.append(new_data)

                    with open(file_path_old, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    
                    driver.switch_to.window(driver.window_handles[0])
                    t += 1
                    print(f"Hoàn thành xử lý video {t}/{max_process}")
                    
                except Exception as e:
                    print(f"Lỗi khi xử lý phần tử thứ {t + 1}: {str(e)}")
                    t += 1  # Vẫn tăng t để tránh vòng lặp vô hạn
                    continue

            driver.quit()
            
            # Kiểm tra file có rỗng không
            with open(file_path_old, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if len(data) > 0:  # Nếu file không rỗng thì thoát vòng lặp
                print(f"✅ Thành công! Đã lấy được {len(data)} bản ghi.")
                break
            else:
                print(f"⚠️ File JSON rỗng, thử lại lần {retry_count + 1}")
                retry_count += 1
                sleep(5)  # Chờ 5 giây trước khi thử lại
        except Exception as main_error:
            print(f"Lỗi chính: {str(main_error)}")
            try:
                driver.quit()
            except:
                pass
            sleep(5)
            retry_count += 1
    
    if retry_count >= max_retries:
        print("❌ Đã thử tối đa số lần cho phép nhưng vẫn không lấy được dữ liệu.")
        return []
    
    # Ghi đè lên file đích
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return data

if __name__ == "__main__":
    main('United States','10')