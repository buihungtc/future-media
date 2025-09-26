import os
import requests
from dotenv import load_dotenv

class YouTubeAPIManager:
    def __init__(self):
        load_dotenv(".env")  # Load API keys từ file .env
        raw_keys = os.getenv("YT_API_KEYS")
        
        if not raw_keys:
            raise ValueError("Không tìm thấy API keys trong biến môi trường YT_API_KEYS")
        
        self.api_keys = [key.strip() for key in raw_keys.split(",") if key.strip()]
        if not self.api_keys:
            raise ValueError("Danh sách API key trống sau khi xử lý")

        self.current_index = 0
        self.failed_keys = set()  # Track các key đã fail

    def get_current_key(self):
        return self.api_keys[self.current_index]

    def rotate_key(self):
        """Xoay sang key tiếp theo, bỏ qua các key đã fail"""
        attempts = 0
        while attempts < len(self.api_keys):
            if self.current_index < len(self.api_keys) - 1:
                self.current_index += 1
            else:
                self.current_index = 0  # Quay lại key đầu tiên
            
            current_key = self.get_current_key()
            if current_key not in self.failed_keys:
                print(f"[INFO] Đã chuyển sang API key mới: {current_key}")
                return True
            
            attempts += 1
        
        print("[ERROR] Tất cả API key đều đã vượt quá giới hạn quota hoặc invalid.")
        return False

    def mark_key_as_failed(self, key, reason="unknown"):
        """Đánh dấu key là failed để không dùng lại"""
        self.failed_keys.add(key)
        print(f"[WARNING] Đã đánh dấu key {key} là failed (lý do: {reason})")

    def make_request(self, url_template, params=None):
        if params is None:
            params = {}

        # Kiểm tra maxResults nếu có
        if "maxResults" in params:
            try:
                val = int(params["maxResults"])
                params["maxResults"] = max(1, min(50, val))  # Giới hạn trong 1-50
            except ValueError:
                print("[WARNING] Giá trị maxResults không hợp lệ, đặt lại thành 5")
                params["maxResults"] = 5

        max_attempts = len(self.api_keys)
        attempt = 0

        while attempt < max_attempts:
            key = self.get_current_key()
            
            # Bỏ qua key đã fail
            if key in self.failed_keys:
                if not self.rotate_key():
                    break
                continue
            
            params["key"] = key
            print(f"[DEBUG] Đang sử dụng API key: {key}")

            try:
                response = requests.get(url_template, params=params)
                
                # ✅ XỬ LÝ LỖI 403 (Quota exceeded)
                if response.status_code == 403:
                    print(f"[WARNING] API key {key} vượt quota. Đang thử key tiếp theo...")
                    self.mark_key_as_failed(key, "quota_exceeded")
                    if not self.rotate_key():
                        break
                    attempt += 1
                    continue

                # ✅ XỬ LÝ LỖI 400 (Invalid key hoặc bad request)
                if response.status_code == 400:
                    response_text = response.text
                    print(f"[ERROR] Lỗi 400 với key {key}: {response_text}")
                    
                    # Kiểm tra xem có phải lỗi invalid key không
                    if "API key not valid" in response_text or "API_KEY_INVALID" in response_text:
                        print(f"[WARNING] API key {key} không hợp lệ. Đang thử key tiếp theo...")
                        self.mark_key_as_failed(key, "invalid_key")
                        if not self.rotate_key():
                            break
                        attempt += 1
                        continue
                    else:
                        # Lỗi 400 khác (bad request parameters)
                        raise RuntimeError(f"Lỗi yêu cầu không hợp lệ: {response_text}")

                # ✅ XỬ LÝ LỖI 401 (Unauthorized)
                if response.status_code == 401:
                    print(f"[WARNING] API key {key} không có quyền truy cập. Đang thử key tiếp theo...")
                    self.mark_key_as_failed(key, "unauthorized")
                    if not self.rotate_key():
                        break
                    attempt += 1
                    continue

                # ✅ XỬ LÝ CÁC LỖI HTTP KHÁC
                if response.status_code >= 500:
                    print(f"[WARNING] Lỗi server {response.status_code}. Thử lại với key khác...")
                    if not self.rotate_key():
                        break
                    attempt += 1
                    continue

                # ✅ SUCCESS - Trả về kết quả
                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Lỗi khi gọi API với key {key}: {e}")
                self.mark_key_as_failed(key, f"request_exception: {str(e)}")
                if not self.rotate_key():
                    break
                attempt += 1

        # Nếu đã thử hết tất cả key
        raise RuntimeError("Tất cả API keys đều đã bị lỗi hoặc hết quota. Vui lòng kiểm tra lại.")

    def get_status(self):
        """Trả về trạng thái của các API keys"""
        status = {
            "total_keys": len(self.api_keys),
            "current_key_index": self.current_index,
            "current_key": self.get_current_key(),
            "failed_keys": list(self.failed_keys),
            "working_keys": [key for key in self.api_keys if key not in self.failed_keys]
        }
        return status