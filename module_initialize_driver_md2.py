from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from dotenv import load_dotenv
import chromedriver_autoinstaller
import os
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import random
import tempfile

def _is_profile_locked(user_data_dir: str) -> bool:
    """
    Heuristic check to see if a Chrome user-data-dir is currently in use.
    Chrome creates lock-related files when a profile is open.
    """
    try:
        if not os.path.isdir(user_data_dir):
            return False
        # Common lock file names created by Chrome when profile is in use
        lock_names = [
            "SingletonLock",
            "SingletonCookie",
            "SingletonSocket",
            "LOCK",
        ]
        entries = set(os.listdir(user_data_dir))
        for name in lock_names:
            if name in entries:
                return True
        return False
    except Exception:
        # If anything goes wrong, be conservative and consider it locked
        return True

def _ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except PermissionError as pe:
        raise pe

def _pick_available_profile_dir(preferred_path: str, max_suffix: int = 20) -> str:
    """
    Return a usable user-data-dir. If the preferred path is locked, generate
    a sibling directory by appending _auto<N>. If none are available, fallback
    to a temporary directory.
    """
    try:
        _ensure_dir(preferred_path)
    except PermissionError:
        # If we can't even create the preferred directory, jump to temp dir
        return tempfile.mkdtemp(prefix="chrome_prof_")

    if not _is_profile_locked(preferred_path):
        return preferred_path

    base = preferred_path
    for i in range(1, max_suffix + 1):
        candidate = f"{base}_auto{i}"
        try:
            _ensure_dir(candidate)
        except PermissionError:
            continue
        if not _is_profile_locked(candidate):
            return candidate

    # Last resort
    return tempfile.mkdtemp(prefix="chrome_prof_")

def init_driver_from_env(env_path=".env", headless=False, wait_between=1):
    """
    Đọc các user-data-dir từ file .env và thử khởi tạo driver với từng profile.
    
    :param env_path: Đường dẫn tới file .env
    :param headless: Bật/tắt chế độ headless
    :param wait_between: Giây chờ giữa các lần thử
    :return: driver Selenium nếu thành công, ngược lại None
    """
    load_dotenv(env_path)
    userdata_raw = os.getenv("USERDATA_PATHS", "")
    userdata_paths = [p.strip() for p in userdata_raw.split(",") if p.strip()]
    
    # chromedriver_autoinstaller.install()

    for path in userdata_paths:
        try:
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except PermissionError as pe:
                    print(f"[!] Không có quyền tạo thư mục profile {path}: {pe}. Bỏ qua profile này.")
                    continue
            # Tự động tải và cài đặt chromedriver
            service = Service(ChromeDriverManager().install())
            profile = 'Profile 1'
            options = webdriver.ChromeOptions()
            # Cho phép chỉ định Chrome binary qua ENV để tránh mismatch
            chrome_binary = os.getenv("CHROME_BINARY", "").strip()
            if chrome_binary:
                try:
                    options.binary_location = chrome_binary
                except Exception:
                    pass
            # Chọn một user-data-dir khả dụng (nếu path đang được dùng sẽ tự động chuyển)
            resolved_user_dir = _pick_available_profile_dir(path)
            options.add_argument(f"--user-data-dir={resolved_user_dir}")
            options.add_argument(f"--profile-directory={profile}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # Thêm mới
            options.add_argument("--start-fullscreen")
            # Ẩn cờ automation và extension mặc định của Selenium
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--disable-blink-features=AutomationControlled")
            # Đảm bảo Chrome không tách (detach) khỏi driver, để quit() đóng được cửa sổ
            options.add_experimental_option("detach", False)

            # Tắt gợi ý/auto-save credential
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            }
            options.add_experimental_option("prefs", prefs)

            # Ngôn ngữ và UA
            lang = os.getenv("BROWSER_LANG", "en-US,en;q=0.9")
            options.add_argument(f"--lang={lang}")
            ua = os.getenv(
                "USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36",
            )
            options.add_argument(f"--user-agent={ua}")

            # WebRTC hạn chế rò rỉ IP cục bộ
            options.add_argument("--webrtc-ip-handling-policy=disable_non_proxied_udp")
            options.add_argument("--force-webrtc-ip-handling-policy=default_public_interface_only")

            if headless:
                options.add_argument("--headless=new")

            # Ưu tiên dùng undetected_chromedriver nếu có (có thể cài qua pip: undetected-chromedriver)
            use_uc = os.getenv("USE_UNDETECTED_CHROMEDRIVER", "1") == "1"
            driver = None
            if use_uc:
                try:
                    import undetected_chromedriver as uc
                    # Dùng options riêng cho UC: tối giản tham số để tăng ổn định
                    uc_options = uc.ChromeOptions()
                    # Bổ sung chỉ định binary nếu có
                    if chrome_binary:
                        try:
                            uc_options.binary_location = chrome_binary
                        except Exception:
                            pass
                    uc_options.add_argument("--no-sandbox")
                    uc_options.add_argument("--disable-dev-shm-usage")
                    uc_options.add_argument("--start-fullscreen")
                    uc_options.add_argument(f"--lang={lang}")
                    uc_options.add_argument(f"--user-agent={ua}")
                    uc_options.add_argument(f"--profile-directory={profile}")
                    if headless:
                        uc_options.add_argument("--headless=new")

                    # Chọn user-data-dir cho UC: mặc định dùng resolved_user_dir như Selenium
                    use_temp = os.getenv("UC_USE_TEMP_PROFILE", "0") == "1"
                    uc_user_dir = tempfile.mkdtemp(prefix="uc_prof_") if use_temp else resolved_user_dir

                    # Truyền user_data_dir qua tham số để UC quản lý đúng cách
                    driver = uc.Chrome(options=uc_options, user_data_dir=uc_user_dir, headless=headless, use_subprocess=True)
                    print("[+] Khởi tạo với undetected_chromedriver")
                except Exception as e:
                    # Thử lại 1 lần với cấu hình tối giản hơn (không đụng tới profile-directory)
                    try:
                        import undetected_chromedriver as uc
                        uc_options = uc.ChromeOptions()
                        if chrome_binary:
                            try:
                                uc_options.binary_location = chrome_binary
                            except Exception:
                                pass
                        if headless:
                            uc_options.add_argument("--headless=new")
                        uc_options.add_argument(f"--profile-directory={profile}")
                        use_temp = os.getenv("UC_USE_TEMP_PROFILE", "0") == "1"
                        # Nếu lỗi có thể do profile đang bị khoá, chọn lại một dir khác
                        fallback_user_dir = _pick_available_profile_dir(path)
                        uc_user_dir = tempfile.mkdtemp(prefix="uc_prof_") if use_temp else fallback_user_dir
                        driver = uc.Chrome(options=uc_options, user_data_dir=uc_user_dir, headless=headless, use_subprocess=True)
                        print("[+] Khởi tạo với undetected_chromedriver (cấu hình tối giản)")
                    except Exception as e2:
                        print(f"[!] Khởi tạo undetected_chromedriver thất bại: {e2}. Fallback webdriver.Chrome")
                        driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(service=service, options=options)
            print(f"[+] Dùng profile: {resolved_user_dir}")

            # CDP: override UA (lần nữa), timezone, platform, Accept-Language
            try:
                driver.execute_cdp_cmd("Network.enable", {})
                driver.execute_cdp_cmd(
                    "Network.setUserAgentOverride",
                    {"userAgent": ua, "platform": "Windows"},
                )
                # Đồng bộ Accept-Language để khớp ngôn ngữ
                driver.execute_cdp_cmd(
                    "Network.setExtraHTTPHeaders",
                    {"headers": {"Accept-Language": lang}},
                )
            except Exception:
                pass

            # Timezone mô phỏng (có thể chỉnh qua ENV)
            tz = os.getenv("BROWSER_TZ", "Asia/Ho_Chi_Minh")
            try:
                driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": tz})
            except Exception:
                pass

            # Kích thước cửa sổ ngẫu nhiên trong khoảng hợp lý để tránh đồng nhất
            try:
                w = random.randint(1200, 1400)
                h = random.randint(700, 900)
                driver.set_window_size(w, h)
            except Exception:
                pass

            # Loại bỏ navigator.webdriver và một số dấu vết phổ biến càng sớm càng tốt
            try:
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

                // platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
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

                // WebGL2 compat
                if (window.WebGL2RenderingContext) {
                    const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                    WebGL2RenderingContext.prototype.getParameter = function(param) {
                        if (param === 37445) { return 'Google Inc.'; }
                        if (param === 37446) { return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)'; }
                        return getParameter2.call(this, param);
                    };
                }

                // Quyền thông báo
                const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
                if (originalQuery) {
                    window.navigator.permissions.query = (parameters) => (
                        parameters && parameters.name === 'notifications'
                            ? Promise.resolve({ state: 'default' })
                            : originalQuery(parameters)
                    );
                }

                // Notification.permission
                const originalPermission = Notification && Notification.permission;
                Object.defineProperty(Notification, 'permission', {
                    get: () => 'default'
                });

                // hardwareConcurrency, deviceMemory, maxTouchPoints
                try {
                    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
                } catch(e) {}
                try {
                    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
                } catch(e) {}
                try {
                    Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0 });
                } catch(e) {}

                // userAgentData (nếu có)
                try {
                    if (navigator.userAgentData) {
                        Object.defineProperty(navigator.userAgentData, 'mobile', { get: () => false });
                        Object.defineProperty(navigator.userAgentData, 'platform', { get: () => 'Windows' });
                    }
                } catch(e) {}

                // navigator.connection
                try {
                    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                    if (connection) {
                        Object.defineProperty(connection, 'rtt', { get: () => 50 });
                        Object.defineProperty(connection, 'downlink', { get: () => 10 });
                        Object.defineProperty(connection, 'effectiveType', { get: () => '4g' });
                    }
                } catch(e) {}

                // Canvas fingerprint noise
                try {
                    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
                    HTMLCanvasElement.prototype.toDataURL = function() {
                        const ctx = this.getContext('2d');
                        if (ctx) {
                            const { width, height } = this;
                            const shift = 0.001 + Math.random() * 0.002;
                            ctx.globalCompositeOperation = 'multiply';
                            ctx.fillStyle = `rgba(${Math.floor(255*shift)},0,0,0.01)`;
                            ctx.fillRect(0, 0, width, height);
                            ctx.globalCompositeOperation = 'source-over';
                        }
                        return toDataURL.apply(this, arguments);
                    };
                    const getImageData = CanvasRenderingContext2D.prototype.getImageData;
                    CanvasRenderingContext2D.prototype.getImageData = function() {
                        const imageData = getImageData.apply(this, arguments);
                        const d = imageData.data;
                        for (let i = 0; i < d.length; i += 4*1000) {
                            d[i] = d[i] + 0; // nhẹ nhàng, tránh thay đổi lớn
                        }
                        return imageData;
                    };
                } catch(e) {}

                // Audio fingerprint noise
                try {
                    const getChannelData = AudioBuffer.prototype.getChannelData;
                    AudioBuffer.prototype.getChannelData = function() {
                        const results = getChannelData.apply(this, arguments);
                        if (results && results.length > 0) {
                            const idx = Math.floor(results.length / 100);
                            results[idx] = results[idx] + (Math.random() * 1e-7);
                        }
                        return results;
                    };
                } catch(e) {}
                """
                driver.execute_script(js_stealth)
            except Exception:
                pass

            return driver

        except WebDriverException as e:
            print(f"[!] Không thể dùng profile {path}: {e}")
            time.sleep(wait_between)
            continue

    print("[x] Không khởi tạo được driver từ bất kỳ profile nào.")
    return None
