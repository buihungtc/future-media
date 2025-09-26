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
from module_initialize_driver_md2 import init_driver_from_env
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import requests
from openai import OpenAI
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException, StaleElementReferenceException, ElementNotInteractableException
try:
    import pyautogui
except Exception:
    pyautogui = None


def apply_stealth(driver):
    """
    Áp dụng một số kỹ thuật giảm phát hiện Selenium:
    - Gỡ/mask navigator.webdriver
    - Thiết lập User-Agent thật qua CDP
    - Giả lập window.chrome, plugins, languages
    - Giả lập WebGL vendor/renderer phổ biến
    - Điều chỉnh quyền notification
    """
    try:
        # 1) Thiết lập User-Agent thực tế bằng CDP
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        try:
            driver.execute_cdp_cmd("Network.enable", {})
            driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {"userAgent": ua, "platform": "Windows"},
            )
        except Exception:
            pass

        # 2) Gỡ navigator.webdriver và một số dấu vết phổ biến
        js_stealth = r"""
        // navigator.webdriver -> undefined
        Object.defineProperty(Navigator.prototype, 'webdriver', {
            get: () => undefined,
        });

        // window.chrome giả lập đối tượng chrome
        if (!window.chrome) {
            Object.defineProperty(window, 'chrome', {
                value: { runtime: {} },
                configurable: false,
                enumerable: true,
                writable: false,
            });
        }

        // languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });

        // plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        // WebGL vendor/renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(param) {
            if (param === 37445) { // UNMASKED_VENDOR_WEBGL
                return 'Google Inc.';
            }
            if (param === 37446) { // UNMASKED_RENDERER_WEBGL
                return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)';
            }
            return getParameter.call(this, param);
        };

        // Quyền thông báo
        const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
        if (originalQuery) {
            window.navigator.permissions.query = (parameters) => (
                parameters && parameters.name === 'notifications'
                    ? Promise.resolve({ state: 'default' })
                    : originalQuery(parameters)
            );
        }
        """
        driver.execute_script(js_stealth)

        # 3) Kích thước cửa sổ và tương tác nhẹ để giống người dùng
        try:
            driver.set_window_size(1280, 800)
        except Exception:
            pass
    except Exception:
        # Không cứng fail nếu một bước stealth lỗi
        pass

# ====== Tiện ích mô phỏng hành vi người dùng ======
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def human_wait(min_s=0.6, max_s=1.8):
    time.sleep(random.uniform(min_s, max_s))

def human_scroll(driver, steps=3):
    h = driver.execute_script("return window.innerHeight || 800;")
    for _ in range(random.randint(1, steps)):
        delta = random.randint(int(h*0.2), int(h*0.9))
        driver.execute_script(f"window.scrollBy(0, {delta});")
        human_wait(0.4, 1.2)
    # Scroll lên nhẹ
    driver.execute_script("window.scrollBy(0, -150);")
    human_wait(0.3, 0.8)

def human_mouse_move(driver, moves=5):
    try:
        actions = ActionChains(driver)
        for _ in range(random.randint(2, moves)):
            x_off = random.randint(-50, 50)
            y_off = random.randint(-30, 30)
            actions.move_by_offset(x_off, y_off).pause(random.uniform(0.1, 0.3))
        actions.perform()
    except Exception:
        pass

def click_like_human(driver, element):
    """
    Cố gắng mô phỏng thao tác người dùng khi click vào phần tử:
    - Scroll vào giữa màn hình
    - Di chuyển chuột tới phần tử, lắc nhẹ và click giữ-thả
    - Thử click với offset nhỏ
    - Thử gửi phím SPACE/ENTER
    """
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        human_wait(0.12, 0.25)

        actions = ActionChains(driver)
        # Di chuyển tới phần tử và lắc nhẹ
        actions.move_to_element(element).pause(0.12)
        for _ in range(random.randint(1, 2)):
            actions.move_by_offset(random.randint(-3, 3), random.randint(-2, 2)).pause(0.05)
        actions.click_and_hold().pause(0.12).release().perform()
        human_wait(0.08, 0.2)

        # Thử click với offset nhỏ xung quanh tâm
        try:
            actions.move_to_element_with_offset(element, random.randint(-2, 2), random.randint(-2, 2)).click().perform()
        except Exception:
            pass

        # Thử gửi SPACE/ENTER nếu có thể focus
        try:
            element.send_keys(Keys.SPACE)
        except Exception:
            try:
                element.send_keys(Keys.ENTER)
            except Exception:
                pass

        return True
    except Exception:
        return False

def ensure_tab_count(driver, min_count=2, timeout=5):
    """
    Đảm bảo có ít nhất min_count tab. Nếu thiếu sẽ mở thêm tab trống và đợi tối đa timeout giây.
    Trả về True nếu đủ số tab, ngược lại False.
    """
    end = time.time() + timeout
    while time.time() < end:
        try:
            if len(driver.window_handles) >= min_count:
                return True
            # mở thêm tab trống
            driver.execute_script("window.open('about:blank','_blank');")
        except Exception:
            pass
        time.sleep(0.2)
    return len(driver.window_handles) >= min_count

def switch_to_tab(driver, index):
    """
    Chuyển sang tab theo index một cách an toàn. Trả về True/False.
    """
    try:
        handles = driver.window_handles
        if index < len(handles):
            driver.switch_to.window(handles[index])
            return True
    except Exception:
        pass
    return False

def wait_and_click_turnstile_checkbox_pyauto(driver, timeout=12):
    """
    Dùng pyautogui điều khiển chuột thật tới vị trí checkbox và click.
    Tính toán toạ độ màn hình tuyệt đối dựa trên rect của #cf-turnstile-wrapper,
    devicePixelRatio, và độ lệch inner/outer của cửa sổ trình duyệt.
    """
    if pyautogui is None:
        return False

    end = time.time() + timeout
    while time.time() < end:
        try:
            wrapper = driver.find_element(By.ID, "cf-turnstile-wrapper")
            # Lấy thông tin cần thiết trong một lần JS
            info = driver.execute_script(
                """
                const el = arguments[0];
                const r = el.getBoundingClientRect();
                const dpr = window.devicePixelRatio || 1;
                const viewportX = window.screenX + (window.outerWidth - window.innerWidth);
                const viewportY = window.screenY + (window.outerHeight - window.innerHeight);
                return {
                    left: r.left, top: r.top, width: r.width, height: r.height,
                    dpr, viewportX, viewportY
                };
                """,
                wrapper,
            )
            if not info or info["width"] <= 0 or info["height"] <= 0:
                time.sleep(0.3)
                continue

            # Ước lượng checkbox nằm lệch trái ~ 32-44px và giữa theo trục dọc
            offset_x = int(max(32, min(44, info["width"] * 0.12)))
            offset_y = int(info["height"] * 0.5)

            screen_x = int(info["viewportX"] + (info["left"] + offset_x) * info["dpr"])
            screen_y = int(info["viewportY"] + (info["top"] + offset_y) * info["dpr"])

            try:
                # Di chuyển với duration để trông tự nhiên hơn
                # Áp dụng offset tương đối: sang trái 5px và xuống 10px
                adjusted_x = screen_x - 5
                adjusted_y = screen_y + 10
                pyautogui.moveTo(adjusted_x, adjusted_y, duration=0.25)
                pyautogui.click()
                print("Đã click checkbox Turnstile bằng pyautogui (chuột thật) với offset (-5, +10)")
                return True
            except Exception:
                pass
        except Exception:
            pass
        time.sleep(0.4)
    return False

def click_via_cdp_center_of_element(driver, element):
    """
    Click the visual center of a given element using Chrome DevTools Protocol coordinates.
    This works even when the element is inside a closed Shadow DOM or cross-origin iframe overlay
    because the click is dispatched at page coordinates.
    """
    try:
        # Compute element's center in page coordinates via JS
        x, y = driver.execute_script(
            """
            const el = arguments[0];
            const rect = el.getBoundingClientRect();
            const x = rect.left + rect.width / 2 + window.scrollX;
            const y = rect.top + rect.height / 2 + window.scrollY;
            return [Math.floor(x), Math.floor(y)];
            """,
            element,
        )

        # Move + press + release
        try:
            driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                "type": "mouseMoved",
                "x": int(x),
                "y": int(y),
                "buttons": 1,
            })
        except Exception:
            pass

        driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": int(x),
            "y": int(y),
            "button": "left",
            "buttons": 1,
            "clickCount": 1,
        })
        driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": int(x),
            "y": int(y),
            "button": "left",
            "buttons": 1,
            "clickCount": 1,
        })
        return True
    except Exception:
        return False

def wait_and_click_turnstile_checkbox(driver, timeout=12):
    """
    Đợi Turnstile (wrapper #cf-turnstile-wrapper) hiển thị và click vào vị trí checkbox
    theo tương đối của widget (bên trái, giữa theo trục y). Chỉ thực hiện 1 lần.
    Sử dụng CDP để click theo toạ độ màn hình.
    """
    end = time.time() + timeout
    clicked = False
    while time.time() < end and not clicked:
        try:
            wrapper = driver.find_element(By.ID, "cf-turnstile-wrapper")
            # Kiểm tra hiển thị và lấy rect
            rect = driver.execute_script(
                """
                const el = arguments[0];
                const r = el.getBoundingClientRect();
                return {left: r.left + window.scrollX, top: r.top + window.scrollY, width: r.width, height: r.height, display: getComputedStyle(el).display, vis: getComputedStyle(el).visibility};
                """,
                wrapper,
            )
            if rect and rect["width"] > 0 and rect["height"] > 0 and rect["display"] != "none" and rect["vis"] != "hidden":
                # Ước lượng vị trí checkbox: lệch vào 24-30px từ mép trái, ở giữa theo trục y
                x = int(rect["left"] + max(24, min(36, rect["width"] * 0.1)))
                y = int(rect["top"] + rect["height"] / 2)
                try:
                    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y, "buttons": 1})
                except Exception:
                    pass
                driver.execute_cdp_cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y, "button": "left", "buttons": 1, "clickCount": 1})
                driver.execute_cdp_cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y, "button": "left", "buttons": 1, "clickCount": 1})
                print("Đã click checkbox Turnstile theo toạ độ ước lượng")
                clicked = True
                break
        except Exception:
            pass
        time.sleep(0.4)
    return clicked

def wait_and_click_turnstile_checkbox_human(driver, timeout=12):
    """
    Phiên bản 'giống người thật': dùng ActionChains di chuyển chuột với jitter nhẹ
    và click vào vị trí ước lượng của checkbox bên trong #cf-turnstile-wrapper.
    Không dùng CDP. Trả về True nếu đã click.
    """
    end = time.time() + timeout
    while time.time() < end:
        try:
            wrapper = driver.find_element(By.ID, "cf-turnstile-wrapper")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", wrapper)
            time.sleep(0.3)
            rect = driver.execute_script(
                """
                const el = arguments[0];
                const r = el.getBoundingClientRect();
                return {width: r.width, height: r.height};
                """,
                wrapper,
            )
            if not rect or rect["width"] <= 0 or rect["height"] <= 0:
                time.sleep(0.3)
                continue

            # Ước lượng toạ độ tương đối (offset từ góc trái-trên của wrapper)
            x_off = int(max(30, min(70, rect["width"] * 0.12)))
            y_off = int(rect["height"] * 0.5)

            actions = ActionChains(driver)
            actions.move_to_element_with_offset(wrapper, x_off, y_off).pause(0.12)
            # Jitter nhẹ xung quanh vị trí
            for _ in range(2):
                actions.move_by_offset( random.randint(-2, 2), random.randint(-2, 2) ).pause(0.06)
            actions.click_and_hold().pause(0.12).release()
            actions.perform()
            print("Đã click checkbox Turnstile bằng ActionChains (giống người)")
            return True
        except Exception:
            pass
        time.sleep(0.4)
    return False

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
    # target_count = 140  # Số lượng phần tử mong muốn
    target_count = 4
    
    for attempt in range(max_attempts):
        print(f"Lần thử {attempt + 1}/{max_attempts}")
        
        # Khởi tạo trình duyệt
        driver = init_driver_from_env()
        # Áp dụng stealth chống phát hiện bot cho phiên làm việc hiện tại
        apply_stealth(driver)
        
        try:
            driver.get(url)
            # Mở trình duyệt toàn màn hình để vị trí tương đối ổn định
            try:
                driver.maximize_window()
            except Exception:
                pass
            # input('Press Enter when ready...')
            # Đợi trang tải + hành vi người dùng
            time.sleep(random.uniform(7.5, 12.5))
            human_mouse_move(driver)
            human_scroll(driver, steps=4)
            human_wait(0.8, 1.6)
            # Thử theo thứ tự: pyautogui (chuột thật) -> ActionChains (giống người) -> CDP (toạ độ)
            if not wait_and_click_turnstile_checkbox_pyauto(driver, timeout=10):
                if not wait_and_click_turnstile_checkbox_human(driver, timeout=8):
                    wait_and_click_turnstile_checkbox(driver, timeout=6)
            # Đợi trang: tìm .vs-content (tối đa 10 lần)
            vs_content_div = None
            for _ in range(10):
                try:
                    vs_content_div = driver.find_element(By.CLASS_NAME, "vs-content")
                    break
                except Exception:
                    time.sleep(1.2)
            if not vs_content_div:
                raise Exception("Không tìm thấy phần tử .vs-content sau 10 lần thử")

            # Lấy tất cả các thẻ <a> là con của div trên
            a_tags = vs_content_div.find_elements(By.TAG_NAME, "a")
            human_wait(0.4, 1.0)
            # x = 0
            driver.execute_script("window.open('https://example.com', '_blank');")
            # Đảm bảo có ít nhất 2 tab để thao tác (tránh IndexError)
            ensure_tab_count(driver, min_count=2, timeout=3)
            
            # Loop qua tất cả các thẻ <a>
            for a_tag in a_tags:
                # if x > 3:
                #     break
                try:
                    # Thêm hành vi người dùng ngẫu nhiên trước khi thao tác phần tử
                    if random.random() < 0.5:
                        human_mouse_move(driver, moves=3)
                    if random.random() < 0.6:
                        human_scroll(driver, steps=2)
                    human_wait(0.3, 1.2)

                    # Tìm div có class = vs-item font-medium trong mỗi thẻ <a>
                    vs_item_div = a_tag.find_element(By.CSS_SELECTOR, ".vs-item.font-medium")
                    # In ra text của class này
                    rank = vs_item_div.text.strip()
                    
                    vs_item_div = a_tag.find_element(By.CSS_SELECTOR, ".vs-channel-name")
                    channel_name = vs_item_div.text.strip()
                    
                    vs_item_div = a_tag.find_element(By.CSS_SELECTOR, ".vs-channel-id")
                    url_channel = 'https://www.youtube.com/' + vs_item_div.text.strip()
                    
                    fields = ['thumbnails', 'description']
                    info = get_channel_info_by_url(url_channel, fields)
                    
                    # Chuyển sang tab thứ 2 một cách an toàn
                    if not ensure_tab_count(driver, min_count=2, timeout=3):
                        raise Exception("Không thể mở tab thứ 2 để truy cập kênh")
                    if not switch_to_tab(driver, 1):
                        raise Exception("Không thể chuyển sang tab thứ 2")
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
                    
                    # Quay lại tab đầu tiên một cách an toàn (nếu còn)
                    switch_to_tab(driver, 0)
                    human_wait(0.4, 1.0)
                    
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
                        human_wait(0.2, 0.6)
                        
                    except:
                        topic = ''
                    
                    if type[:4] == 'subs':
                        new_sub = a_tag.find_element(By.CSS_SELECTOR, ".vs-item.vs-item--green")
                        new_subs = new_sub.text.strip()
                        total_sub = new_sub.find_element(By.XPATH, "following-sibling::div").text.strip()
                        total_view = a_tag.find_element(By.CSS_SELECTOR, ".vs-item.hide-on-mobile-lg").text.strip()
                        
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
                        new_view = a_tag.find_element(By.CSS_SELECTOR, ".vs-item.vs-item--green")
                        new_views = new_view.text.strip()
                        total_views = new_view.find_element(By.XPATH, "following-sibling::div").text.strip()
                        total_subs = a_tag.find_element(By.CSS_SELECTOR, ".vs-item.hide-on-mobile-lg").text.strip()
                        
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
