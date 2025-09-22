from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import json
from dotenv import load_dotenv
import openai
from datetime import datetime
from flask import Flask, jsonify
from module_get_info_chanel import get_channel_info_by_url
from module_initialize_driver import init_driver_from_env
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import requests
from openai import OpenAI


def chay(user_id, type):
    # Lấy thời gian hiện tại
    today = datetime.now()
    
    # Format thành chuỗi viết liền: ddmmyyyy
    ngay_thang_nam = today.strftime("%d%m%Y")
    # Tải biến môi trường từ file .env
    load_dotenv('.env')
    CHATGPT_KEY = os.getenv("CHATGPT_KEY")
    
    # Khởi tạo file paths
    file_path = f"backend2/function2/{type}.json"
    file_path_old = f"backend2/function2/{type}_old.json"
    
    # Cách 1: Ghi đè trực tiếp
    with open(file_path_old, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)
    
    # URL của trang web
    if type == 'subs_7d':
        url = "https://www.viewstats.com/top-list?filterBy=subs&interval=ms_weekly&madeForKids=true&movies=true&musicChannels=true&tab=channels"
    elif type == 'subs_30d':
        url = 'https://www.viewstats.com/top-list?filterBy=subs&interval=ms_monthly&madeForKids=true&movies=true&musicChannels=true&tab=channels'
    elif type == 'subs_3m':
        url = 'https://www.viewstats.com/top-list?filterBy=subs&interval=ms_quarterly&madeForKids=true&movies=true&musicChannels=true&tab=channels'
    elif type == "views_7d":
        url = 'https://www.viewstats.com/top-list?filterBy=views&interval=mv_weekly&madeForKids=true&movies=true&musicChannels=true&tab=channels'
    elif type == "views_30d":
        url = 'https://www.viewstats.com/top-list?filterBy=views&interval=mv_monthly&madeForKids=true&movies=true&musicChannels=true&tab=channels'
    elif type == "views_3m":
        url = 'https://www.viewstats.com/top-list?filterBy=views&interval=mv_quarterly&madeForKids=true&movies=true&musicChannels=true&tab=channels'
    
    # VÒNG LẶP CHÍNH VỚI TỐI ĐA 5 LẦN THỬ
    max_attempts = 5
    target_count = 140  # Số lượng phần tử mong muốn
    
    for attempt in range(max_attempts):
        print(f"Lần thử {attempt + 1}/{max_attempts}")
        
        # Khởi tạo trình duyệt
        driver = init_driver_from_env()
        
        try:
            driver.get(url)
            # Đợi trang tải
            time.sleep(10)
            
            # Tìm div có class = vs-content
            vs_content_div = driver.find_element(By.CLASS_NAME, "vs-content")
            
            # Lấy tất cả các thẻ <a> là con của div trên
            a_tags = vs_content_div.find_elements(By.TAG_NAME, "a")
            # x = 0
            driver.execute_script("window.open('https://example.com', '_blank');")
            
            # Loop qua tất cả các thẻ <a>
            for a_tag in a_tags:
                # if x > 3:
                #     break
                try:
                    # Tìm div có class = vs-item font-medium trong mỗi thẻ <a>
                    vs_item_div = a_tag.find_element(By.CLASS_NAME, "vs-item.font-medium")
                    # In ra text của class này
                    rank = vs_item_div.text.strip()
                    
                    vs_item_div = a_tag.find_element(By.CLASS_NAME, "vs-channel-name")
                    channel_name = vs_item_div.text.strip()
                    
                    vs_item_div = a_tag.find_element(By.CLASS_NAME, "vs-channel-id")
                    url_channel = 'https://www.youtube.com/' + vs_item_div.text.strip()
                    
                    fields = ['thumbnails', 'description']
                    info = get_channel_info_by_url(url_channel, fields)
                    
                    tabs = driver.window_handles
                    driver.switch_to.window(tabs[1])
                    driver.get(url_channel)
                    sleep(1)
                    
                    try:
                        wait = WebDriverWait(driver, 10)
                        button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space(text())='View channel stats']")))
                        button.click()
                        elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "keyword-inner")))
                        texts = [el.text.strip() for el in elements if el.text.strip()]
                        tu_khoa_SEO = ", ".join(texts)
                    except:
                        tu_khoa_SEO = ''
                    
                    driver.switch_to.window(driver.window_handles[0])
                    
                    try:
                        API_URL = 'https://api.openai.com/v1/chat/completions'
                        
                        # topic
                        topic = f"""
                        Bạn là một chuyên gia phân tích nội dung YouTube.
                        Dựa vào từ khóa và mô tả dưới đây, hãy suy đoán chủ đề chính của kênh YouTube (ví dụ: Ẩm thực, Công nghệ, Giải trí, Giáo dục, Khoa học, Làm đẹp, Sức khỏe, Du lịch...).
                        Trả lời ngắn gọn bằng một hoặc hai từ.

                        Từ khóa: {tu_khoa_SEO}
                        Mô tả: {info['description']}

                        Chủ đề:
                        """
                        
                        # Cấu hình headers
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
                                "max_tokens": 500
                            }
                            
                            response = requests.post(API_URL, headers=headers, json=data)
                            
                            if response.status_code == 200:
                                result = response.json()
                                return result['choices'][0]['message']['content'].strip()
                            else:
                                return f"[Lỗi: {response.status_code}]"
                        
                        # topic
                        topic = chat_with_gpt(topic)
                        
                    except:
                        topic = ''
                    
                    if type[:4] == 'subs':
                        new_sub = a_tag.find_element(By.CLASS_NAME, "vs-item.vs-item--green")
                        new_subs = new_sub.text.strip()
                        total_sub = new_sub.find_element(By.XPATH, "following-sibling::div").text.strip()
                        total_view = a_tag.find_element(By.CLASS_NAME, "vs-item.hide-on-mobile-lg").text.strip()
                        
                        with open(file_path_old, "r", encoding="utf-8") as f:
                            try:
                                data = json.load(f)
                            except json.JSONDecodeError:
                                data = []
                        
                        new_data = {
                            "rank": rank,
                            "channel_name": channel_name,
                            "url_channel": url_channel,
                            'thumbnails': info['thumbnails'],
                            'description': info['description'],
                            "new_stats": new_subs,
                            "total_sub": total_sub,
                            "total_view": total_view,
                            "SEO_keywords": tu_khoa_SEO,
                            "topic": topic
                        }
                        
                        data.append(new_data)
                        
                        with open(file_path_old, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                    
                    if type[:4] == 'view':
                        new_view = a_tag.find_element(By.CLASS_NAME, "vs-item.vs-item--green")
                        new_views = new_view.text.strip()
                        total_views = new_view.find_element(By.XPATH, "following-sibling::div").text.strip()
                        total_subs = a_tag.find_element(By.CLASS_NAME, "vs-item.hide-on-mobile-lg").text.strip()
                        
                        with open(file_path_old, "r", encoding="utf-8") as f:
                            try:
                                data = json.load(f)
                            except json.JSONDecodeError:
                                data = []
                        
                        new_data = {
                            "rank": rank,
                            "channel_name": channel_name,
                            "url_channel": url_channel,
                            'thumbnails': info['thumbnails'],
                            'description': info['description'],
                            "new_stats": new_views,
                            "total_view": total_views,
                            "total_sub": total_subs,
                            "SEO_keywords": tu_khoa_SEO,
                            "topic": topic
                        }
                        
                        data.append(new_data)
                        
                        with open(file_path_old, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                            
                except Exception as e:
                    # x += 1
                    print(f"Lỗi khi tìm kiếm trong thẻ <a>: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Lỗi khi tìm kiếm trong thẻ <a>: {str(e)}")
            
        finally:
            # Đóng trình duyệt
            driver.quit()
        
        # KIỂM TRA SỐ LƯỢNG PHẦN TỬ TRONG FILE
        try:
            with open(file_path_old, "r", encoding="utf-8") as f:
                data = json.load(f)
                current_count = len(data)
                print(f"Số lượng phần tử hiện tại: {current_count}")
                
                # Nếu đã đạt được số lượng mong muốn, thoát khỏi vòng lặp
                if current_count >= target_count:
                    print(f"Đã đạt được {current_count} phần tử (≥ {target_count}). Dừng vòng lặp.")
                    break
                else:
                    print(f"Chưa đạt mục tiêu ({current_count}/{target_count}). Tiếp tục lần thử tiếp theo...")
                    
        except Exception as e:
            print(f"Lỗi khi đọc file để kiểm tra: {str(e)}")
            
        # Nếu đây là lần thử cuối cùng
        if attempt == max_attempts - 1:
            print(f"Đã thử {max_attempts} lần nhưng chưa đạt được {target_count} phần tử.")
    
    # Đọc dữ liệu cuối cùng từ file
    with open(file_path_old, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Hoàn thành với {len(data)} phần tử trong file.")

    # Ghi đè lên file đích
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)  # data là dict hoặc list tùy nội dung
    return data
if __name__ == "__main__":
    # chay('1','views_7d')
    # chay('1','views_30d')
    # chay('1','views_3m')
    chay('1','subs_7d')
    # chay('1','subs_30d')
    # chay('1','subs_3m')
