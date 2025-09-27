import re
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime
from module_youtube_api_manager import YouTubeAPIManager
import uuid
from module_get_info_chanel import get_channel_info_by_url
import threading
import traceback
import time
from module_initialize_driver import init_driver_from_env

yt_api = YouTubeAPIManager()
file_lock = threading.Lock()
def parse_number_from_string(s):
    """Chuyển đổi chuỗi như '1.2K', '5M', '1,145' thành số nguyên"""
    s = s.strip().upper()
    
    # Loại bỏ dấu phẩy trong số
    s = s.replace(',', '')
    
    match = re.match(r'^([\d\.]+)([KM]?)', s)
    if not match:
        return None

    number, suffix = match.groups()
    try:
        number = float(number)
        if suffix == 'K':
            number *= 1_000
        elif suffix == 'M':
            number *= 1_000_000
        return int(number)
    except:
        return None
def sub_module3(video_ids, file_path, url):
    print('=== FIXED RACE CONDITION VERSION ===')
    print('So video tim duoc la:', video_ids)
    
    for item in video_ids:
        # CRITICAL FIX: Tạo ID duy nhất TRONG LOCK
        with file_lock:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding='utf-8') as f:
                    records = json.load(f)
            else:
                records = [{"videos": []}]  # Đảm bảo structure đúng
            
            # Tìm max ID hiện tại
            videos = records[0]["videos"]
            max_id = max((video["id_video"] for video in videos), default=0)
            id_video = max_id + 1
            
            print(f"🔒 [LOCKED] Creating video ID {id_video} for YouTube {item}")
            
            try:  # FIX: Thêm dấu : sau try
                # Lấy thông tin video
                # urlyt = "https://www.googleapis.com/youtube/v3/videos"
                # params = {"part": "snippet,statistics", "id": item}
                
                # res = yt_api.make_request(urlyt, params=params)
                # if 'items' not in res or not res['items']:
                #     print(f"⚠️ Không tìm thấy video {item}")
                #     continue
                    
                # video = res['items'][0]
                # snippet = video.get('snippet', {})
                driver = init_driver_from_env()
                driver.get(f'https://www.youtube.com/watch?v={item}')
                print(f"🔗 Đang truy cập video: https://www.youtube.com/watch?v={item}")
                sleep(1)
                element = driver.find_element(By.CSS_SELECTOR, 'yt-formatted-string.style-scope.ytd-watch-metadata')
                tieu_de = element.text
                print("Text:", element.text)

                # Tạo record mới
                new_record = {
                    "id_video": id_video,
                    "url_video": f'https://www.youtube.com/watch?v={item}',
                    "tieu_de": tieu_de,
                    "track": [],
                    "debug_info": {
                        "youtube_id": item,  # CRITICAL: Lưu YouTube ID gốc
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "thread_will_track": f"VideoTracker-{id_video}",
                        "created_timestamp": time.time()
                    }
                }

                # Thêm vào records NGAY TRONG LOCK
                records[0]["videos"].insert(0, new_record)

                # Lưu ngay
                with open(file_path, "w", encoding='utf-8') as f:
                    json.dump(records, f, indent=4, ensure_ascii=False)
                
                print(f"✅ [LOCKED] Saved video: ID={id_video}, YouTube={item}")
                driver.quit()
                sleep(5)
                # Tạo thread SAU KHI ĐÃ LƯU
                print(f"🚀 Starting thread for video ID {id_video}")
                t = threading.Thread(
                    target=loop_component_fixed, 
                    args=(file_path, item, id_video, url), 
                    daemon=False,
                    name=f"VideoTracker-{id_video}-{item[:8]}"  # Thêm YouTube ID vào tên
                )
                t.start()
                sleep(5)  # Tránh tạo thread quá nhanh
                
            except Exception as e:  # FIX: Di chuyển except ra ngoài with block và đúng thụt lề
                print(f"❌ Lỗi khi xử lý video {item}: {str(e)}")
                traceback.print_exc()


def loop_component_fixed(file_path, youtube_id, id_video, url_kenh):
    thread_name = threading.current_thread().name
    print(f"🚀 [{thread_name}] BẮT ĐẦU - Video ID: {id_video}, YouTube: {youtube_id}")
    
    # Verify target video tồn tại
    with file_lock:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                records = json.load(f)
            
            target_video = None
            for video in records[0]["videos"]:
                if (video["id_video"] == id_video and 
                    video["debug_info"]["youtube_id"] == youtube_id):
                    target_video = video
                    break
            
            if not target_video:
                print(f"❌ [{thread_name}] KHÔNG TÌM THẤY target video!")
                return
            
            print(f"✅ [{thread_name}] Verified target: {target_video['debug_info']['youtube_id']}")
    
    for loop_count in range(48):
        try:
            print(f"\n🕐 [{thread_name}] Loop {loop_count + 1}/48")
            driver = init_driver_from_env()
            driver.get(f'https://www.youtube.com/watch?v={youtube_id}')
            driver.implicitly_wait(10)
            # driver.execute_script("window.scrollBy(0, window.innerHeight);")

            # # Lấy dữ liệu
            fields = ['subscriberCount']
            info = get_channel_info_by_url(url_kenh, fields)
            
            if not info or 'subscriberCount' not in info:
                print(f"⚠️ [{thread_name}] Không lấy được subscriber count")
                continue
                
            tong_sub = info['subscriberCount']
            print(f"👥 [{thread_name}] Tổng subscribers: {tong_sub}")
            
            # urlyt = "https://www.googleapis.com/youtube/v3/videos"
            # params = {"part": "snippet,statistics", "id": youtube_id}  # Dùng youtube_id cố định
            
            # res = yt_api.make_request(urlyt, params=params)
            # if 'items' not in res or not res['items']:
            #     print(f"⚠️ [{thread_name}] Không tìm thấy video {youtube_id}")
            #     continue
                
            # video = res['items'][0]
            # stats_video = video.get('statistics', {})
            driver.execute_script("window.scrollBy(0, window.innerHeight * 4);")
            sleep(5)

            try:
                # 1. Lấy phần tử yt-formatted-string[id="info"]
                info_element = driver.find_element(By.CSS_SELECTOR, 'yt-formatted-string#info')

                # 2. Tìm span đầu tiên bên trong nó
                span = info_element.find_element(By.TAG_NAME, 'span')
                span_text = span.text
                print("🔤 Text gốc trong span:", span_text)

                # 3. Lấy phần trước dấu cách đầu tiên
                first_part = span_text.split(' ')[0]

                # 4. Chuyển thành số nguyên sau khi xử lý K/M
                luot_xem = parse_number_from_string(first_part)

            except Exception as e:
                print(f"❌ Lỗi khi xử lý: {e}")
                luot_xem = None

            try:
                # 1. Tìm phần tử đầu tiên khớp với class
                element = driver.find_element(By.CSS_SELECTOR,
                    '.yt-spec-button-shape-next.yt-spec-button-shape-next--tonal.'
                    'yt-spec-button-shape-next--mono.yt-spec-button-shape-next--size-m.'
                    'yt-spec-button-shape-next--icon-leading.yt-spec-button-shape-next--segmented-start.'
                    'yt-spec-button-shape-next--enable-backdrop-filter-experiment'
                )

                # 2. Lấy giá trị aria-label
                aria_label = element.get_attribute("aria-label")
                print("🔤 aria-label:", aria_label)

                # 3. Bỏ hết ký tự trừ số
                digits_only = re.sub(r'[^\d]', '', aria_label)

                # 4. Chuyển sang int nếu có số
                if digits_only:
                    luot_thich = int(digits_only)
                    print("✅ Kết quả:", luot_thich)
                else:
                    print("⚠️ Không có số hợp lệ trong aria-label.")

            except Exception as e:
                print(f"❌ Lỗi: {e}")
                luot_thich = None

            try:
                # 1. Tìm phần tử chứa số bình luận
                container = driver.find_element(By.CSS_SELECTOR, '.count-text.style-scope.ytd-comments-header-renderer')

                # 2. Lấy span đầu tiên bên trong
                span = container.find_element(By.TAG_NAME, 'span')
                span_text = span.text
                print("🔤 Text trong span:", span_text)

                # 3. Tách phần trước dấu cách
                count_text = span_text.split(' ')[0]

                # 4. Phân tích số lượng
                comment_count = parse_number_from_string(count_text)
                
                if comment_count is not None:
                    print("✅ Số bình luận:", comment_count)
                else:
                    print("⚠️ Không phân tích được số bình luận.")

            except Exception as e:
                print(f"❌ Lỗi: {e}")
                comment_count = None


            data_entry = {
                "luot_xem": luot_xem,
                "luot_thich": luot_thich,
                "binh_luan": comment_count,
                "sub_now": tong_sub,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "loop_number": loop_count + 1,
                "debug_info": {
                    "thread_name": thread_name,
                    "target_video_id": id_video,
                    "youtube_id": youtube_id,  # CRITICAL: Luôn dùng youtube_id gốc
                    "timestamp": time.time()
                }
            }
            
            # CRITICAL: Tìm video chính xác
            success = False
            with file_lock:
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding='utf-8') as f:
                        records = json.load(f)
                    
                    for video in records[0]["videos"]:
                        # DOUBLE CHECK: Cả ID và YouTube ID phải khớp
                        if (video["id_video"] == id_video and 
                            video["debug_info"]["youtube_id"] == youtube_id):
                            
                            print(f"✅ [{thread_name}] Found correct video!")
                            video["track"].append(data_entry)
                            
                            # Sắp xếp theo loop_number cho video này
                            video["track"].sort(key=lambda x: x["loop_number"])
                            
                            success = True
                            break
                    
                    if success:
                        with open(file_path, "w", encoding='utf-8') as f:
                            json.dump(records, f, indent=4, ensure_ascii=False)
                    else:
                        print(f"❌ [{thread_name}] KHÔNG TÌM THẤY video phù hợp!")
                        print(f"🔍 Tìm: ID={id_video}, YouTube={youtube_id}")
                        
                        # Debug: In ra tất cả videos
                        for i, v in enumerate(records[0]["videos"]):
                            print(f"  Video {i}: ID={v['id_video']}, YouTube={v['debug_info']['youtube_id']}")
            driver.quit()
            if success:
                print(f"✅ [{thread_name}] Saved loop {loop_count + 1}")
            
            # Ngủ (trừ lần cuối)
            if loop_count < 47:
                print(f"😴 [{thread_name}] Sleep...")
                # sleep(1200)  # Test với 1 phút
                sleep(3600)  # Production: 1 giờ
                
        except Exception as e:
            print(f"❌ [{thread_name}] Lỗi loop {loop_count + 1}: {str(e)}")
            traceback.print_exc()
            if loop_count < 47:
                sleep(3600)  # sleep(3600)
                # sleep(3600)  # Production: 1 giờ
        finally:
            if 'driver' in locals():
                driver.quit()
    
    print(f"🏁 [{thread_name}] HOÀN THÀNH!")


# BONUS: Hàm kiểm tra và sửa dữ liệu bị lỗi
def fix_corrupted_data(file_path):
    """Sửa dữ liệu bị mix-up giữa các video"""
    print("🔧 Đang sửa dữ liệu bị lỗi...")
    
    with open(file_path, "r", encoding='utf-8') as f:
        records = json.load(f)
    
    for video in records[0]["videos"]:
        video_id = video["id_video"]
        expected_youtube_id = video["debug_info"]["youtube_id"]
        
        print(f"\n🔍 Checking video ID {video_id} (YouTube: {expected_youtube_id})")
        
        # Tách track thành các nhóm theo youtube_id
        correct_tracks = []
        wrong_tracks = []
        
        for track in video["track"]:
            track_youtube_id = track["debug_info"]["youtube_id"]
            if track_youtube_id == expected_youtube_id:
                correct_tracks.append(track)
            else:
                wrong_tracks.append(track)
                print(f"  ❌ Found wrong track: {track_youtube_id} (loop {track['loop_number']})")
        
        # Chỉ giữ lại tracks đúng
        video["track"] = correct_tracks
        video["track"].sort(key=lambda x: x["loop_number"])
        
        print(f"  ✅ Kept {len(correct_tracks)} correct tracks, removed {len(wrong_tracks)} wrong tracks")
    
    # Lưu lại
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(records, f, indent=4, ensure_ascii=False)
    
    print("🔧 Hoàn thành sửa dữ liệu!")