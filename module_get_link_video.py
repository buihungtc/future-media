import re
from module_youtube_api_manager import YouTubeAPIManager  # đảm bảo bạn có class này


manager = YouTubeAPIManager()
def get_latest_video_links_by_handle(url, max_results=5):
    query = re.search(r'youtube\.com/@([A-Za-z0-9_]+)', url)
    if not query:
        return []

    query = query.group(1)

    # Tìm channelId từ handle
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "maxResults": 1
    }
    search_response = manager.make_request(search_url, params=search_params)

    if 'items' not in search_response or not search_response['items']:
        return []

    channel_id = search_response['items'][0]['id']['channelId']

    # Lấy danh sách video mới nhất
    videos_url = "https://www.googleapis.com/youtube/v3/search"
    video_params = {
        "part": "snippet",
        "channelId": channel_id,
        "order": "date",
        "maxResults": max_results,
        "type": "video"
    }
    videos_response = manager.make_request(videos_url, params=video_params)

    return [
        # f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        f"{item['id']['videoId']}"
        for item in videos_response.get("items", [])
    ]

# ---- MAIN ----
if __name__ == "__main__":
    yt_manager = YouTubeAPIManager()  # Tự động xoay vòng key nếu bị lỗi
    url = "https://www.youtube.com/@hdsinhton"
    N = 5

    try:
        video_links = get_latest_video_links_by_handle(url, N)
        print(video_links)
        for link in video_links:
            print(link)
    except RuntimeError as e:
        print("[FATAL]", str(e))
