import re
import isodate
from datetime import datetime
from dateutil import parser
from module_youtube_api_manager import YouTubeAPIManager  # Đảm bảo class này tồn tại

# ------------------- LẤY DANH SÁCH VIDEO MỚI -------------------
manager = YouTubeAPIManager()

def get_channel_id_from_url(url):
    """Lấy channel ID từ URL với các định dạng khác nhau"""
    url = url.split('?')[0].rstrip('/')

    matchers = [
        (r'youtube\.com/channel/([^/]+)', True),
        (r'youtube\.com/user/([^/]+)', False),
        (r'youtube\.com/@([^/]+)', False),
        (r'youtube\.com/c/([^/]+)', False),
    ]

    for pattern, is_id in matchers:
        match = re.search(pattern, url)
        if match:
            query = match.group(1)
            if is_id:
                return query  # Đã là channel ID
            else:
                return search_channel_id(query)  # Tìm channel ID từ query

    # Nếu không khớp pattern nào, lấy phần cuối của URL làm query
    query = url.split('/')[-1]
    return search_channel_id(query)

def search_channel_id(query):
    """Tìm channel ID từ query (handle, username, custom name)"""
    params = {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "maxResults": 1
    }
    url = "https://www.googleapis.com/youtube/v3/search"
    search_response = manager.make_request(url, params)

    if 'items' not in search_response or not search_response['items']:
        raise ValueError(f"❌ Không tìm thấy kênh từ query: {query}")

    return search_response['items'][0]['id']['channelId']

def get_video_ids_by_channel(url, max_results=20):
    try:
        channel_id = get_channel_id_from_url(url)
    except ValueError:
        return []

    # Lấy video mới nhất
    videos_url = "https://www.googleapis.com/youtube/v3/search"
    video_params = {
        "part": "id",
        "channelId": channel_id,
        "order": "date",
        "maxResults": max_results,
        "type": "video"
    }

    videos_response = manager.make_request(videos_url, params=video_params)
    return [item['id']['videoId'] for item in videos_response.get('items', [])]


# ------------------- TÍNH THỜI LƯỢNG TRUNG BÌNH -------------------

def get_average_video_duration(video_ids):
    durations = []

    for i in range(0, len(video_ids), 50):  # Batch size = 50
        batch_ids = ','.join(video_ids[i:i + 50])
        video_url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "contentDetails",
            "id": batch_ids
        }

        response = manager.make_request(video_url, params=params)
        for item in response.get('items', []):
            iso_duration = item['contentDetails']['duration']
            seconds = isodate.parse_duration(iso_duration).total_seconds()
            durations.append(seconds)

    if not durations:
        return 0

    return sum(durations) / len(durations)


def format_duration(seconds):
    mins, secs = divmod(int(seconds), 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs}h {mins}m {secs}s" if hrs else f"{mins}m {secs}s"


# ------------------- LẤY THÔNG TIN KÊNH -------------------

def get_channel_info_by_url(url):
    try:
        channel_id = get_channel_id_from_url(url)
    except ValueError as e:
        return str(e)

    # Lấy thông tin channel
    channel_url = "https://www.googleapis.com/youtube/v3/channels"
    channel_params = {
        "part": "snippet,statistics",
        "id": channel_id
    }

    channel_response = manager.make_request(channel_url, params=channel_params)
    if 'items' not in channel_response or not channel_response['items']:
        return "❌ Không thể truy vấn thông tin chi tiết từ channelId."

    data = channel_response['items'][0]
    snippet = data['snippet']
    stats = data['statistics']

    ten_kenh = snippet.get('title')
    ngay_tao = snippet.get('publishedAt')
    dt_obj = parser.parse(ngay_tao)
    ngay_dinh_dang = dt_obj.strftime("%Y-%m-%d")
    avata = snippet.get('thumbnails', {}).get('default', {}).get('url')
    tong_sub = stats.get('subscriberCount', 'Ẩn')
    tong_view = stats.get('viewCount')
    tong_video = stats.get('videoCount')
    quoc_gia = snippet.get('country', 'Không rõ')

    return ten_kenh, ngay_dinh_dang, avata, tong_sub, tong_view, tong_video, quoc_gia