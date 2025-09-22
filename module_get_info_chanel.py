import re
from dateutil import parser
from module_youtube_api_manager import YouTubeAPIManager

manager = YouTubeAPIManager()

def get_channel_info_by_url(url, fields=None, debug=True):
    """
    Lấy thông tin kênh từ URL YouTube với debug mode
    """
    original_url = url
    url = url.split('?')[0].rstrip('/')
    
    if debug:
        print(f"🔍 URL gốc: {original_url}")
        print(f"🔍 URL đã clean: {url}")

    # Improved matchers với thứ tự ưu tiên
    matchers = [
        # 1. Handle @username format (mới nhất)
        (r'youtube\.com/@([^/]+)', 'handle'),
        # 2. Channel ID format (chính xác nhất)
        (r'youtube\.com/channel/([^/]+)', 'channel_id'),
        # 3. Custom URL format
        (r'youtube\.com/c/([^/]+)', 'custom_url'),
        # 4. Legacy user format
        (r'youtube\.com/user/([^/]+)', 'username'),
    ]

    for pattern, url_type in matchers:
        match = re.search(pattern, url)
        if match:
            query = match.group(1)
            if debug:
                print(f"✅ Phát hiện {url_type}: {query}")
            
            if url_type == 'channel_id':
                return get_channel_info(query, fields, debug)
            elif url_type == 'handle':
                return get_channel_by_handle(query, fields, debug)
            elif url_type == 'username':
                return get_channel_by_username(query, fields, debug)
            else:  # custom_url
                return search_channel(query, fields, debug)

    # Fallback: lấy phần cuối URL
    query = url.split('/')[-1]
    if debug:
        print(f"⚠️  Fallback search với query: {query}")
    return search_channel(query, fields, debug)

def get_channel_by_handle(handle, fields=None, debug=True):
    """
    Lấy kênh theo handle (@username) - phương pháp mới nhất
    """
    if debug:
        print(f"🔍 Tìm kiếm theo handle: @{handle}")
    
    # Thử với forHandle parameter (YouTube API v3 mới)
    params = {
        "part": "snippet,statistics",
        "forHandle": handle
    }
    
    url = "https://www.googleapis.com/youtube/v3/channels"
    
    try:
        response = manager.make_request(url, params)
        
        if 'items' in response and response['items']:
            channel_id = response['items'][0]['id']
            if debug:
                print(f"✅ Tìm thấy channel ID từ handle: {channel_id}")
            return get_channel_info(channel_id, fields, debug)
        else:
            if debug:
                print(f"❌ Không tìm thấy kênh với handle: @{handle}")
            # Fallback to search
            return search_channel(handle, fields, debug)
    
    except Exception as e:
        if debug:
            print(f"❌ Lỗi khi tìm theo handle: {e}")
        return search_channel(handle, fields, debug)

def get_channel_by_username(username, fields=None, debug=True):
    """
    Lấy kênh theo username cũ
    """
    if debug:
        print(f"🔍 Tìm kiếm theo username: {username}")
    
    params = {
        "part": "snippet,statistics",
        "forUsername": username
    }
    
    url = "https://www.googleapis.com/youtube/v3/channels"
    
    try:
        response = manager.make_request(url, params)
        
        if 'items' in response and response['items']:
            channel_id = response['items'][0]['id']
            if debug:
                print(f"✅ Tìm thấy channel ID từ username: {channel_id}")
            return get_channel_info(channel_id, fields, debug)
        else:
            if debug:
                print(f"❌ Không tìm thấy kênh với username: {username}")
            # Fallback to search
            return search_channel(username, fields, debug)
    
    except Exception as e:
        if debug:
            print(f"❌ Lỗi khi tìm theo username: {e}")
        return search_channel(username, fields, debug)

def search_channel(query, fields=None, debug=True):
    """
    Tìm kiếm kênh - chỉ dùng khi không có cách khác
    """
    if debug:
        print(f"🔍 Tìm kiếm kênh với query: {query}")
    
    params = {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "maxResults": 5  # Lấy nhiều kết quả để so sánh
    }
    url = "https://www.googleapis.com/youtube/v3/search"
    
    try:
        search_response = manager.make_request(url, params)
        
        if 'items' not in search_response or not search_response['items']:
            raise ValueError(f"❌ Không tìm thấy kênh từ query: {query}")

        # Debug: hiển thị tất cả kết quả tìm kiếm
        if debug:
            print(f"🔍 Tìm thấy {len(search_response['items'])} kênh:")
            for i, item in enumerate(search_response['items']):
                channel_title = item['snippet']['title']
                channel_id = item['id']['channelId']
                print(f"  {i+1}. {channel_title} (ID: {channel_id})")
        
        # Lấy kênh đầu tiên (có thể không chính xác)
        channel_id = search_response['items'][0]['id']['channelId']
        
        if debug:
            print(f"⚠️  Chọn kênh đầu tiên: {search_response['items'][0]['snippet']['title']}")
            print(f"⚠️  Channel ID: {channel_id}")
        
        return get_channel_info(channel_id, fields, debug)
    
    except Exception as e:
        if debug:
            print(f"❌ Lỗi tìm kiếm: {e}")
        return None

def get_channel_info(channel_id, fields=None, debug=True):
    """
    Lấy thông tin chi tiết kênh từ channel ID
    """
    if debug:
        print(f"📊 Lấy thông tin chi tiết cho channel ID: {channel_id}")
    
    if fields is None:
        fields = [
            'title', 'description', 'publishedAt', 'thumbnails',
            'subscriberCount', 'viewCount', 'videoCount', 'country', 'channelId'
        ]

    # Xác định parts cần thiết
    parts = set()
    if any(f in ['title', 'description', 'publishedAt', 'thumbnails', 'country'] for f in fields):
        parts.add('snippet')
    if any(f in ['subscriberCount', 'viewCount', 'videoCount'] for f in fields):
        parts.add('statistics')

    part_str = ','.join(parts)

    params = {
        "part": part_str,
        "id": channel_id
    }
    url = "https://www.googleapis.com/youtube/v3/channels"
    
    try:
        channel_response = manager.make_request(url, params)
        
        if 'items' not in channel_response or not channel_response['items']:
            raise ValueError(f"❌ Không thể lấy thông tin từ channel ID: {channel_id}")

        data = channel_response['items'][0]
        snippet = data.get('snippet', {})
        stats = data.get('statistics', {})

        if debug:
            print(f"✅ Lấy thành công thông tin kênh: {snippet.get('title', 'N/A')}")

        result = {}

        for f in fields:
            if f == 'title':
                result['title'] = snippet.get('title')
            elif f == 'description':
                result['description'] = snippet.get('description')
            elif f == 'publishedAt':
                raw_date = snippet.get('publishedAt')
                result['publishedAt'] = parser.parse(raw_date).strftime('%Y-%m-%d') if raw_date else None
            elif f == 'thumbnails':
                result['thumbnails'] = snippet.get('thumbnails', {}).get('default', {}).get('url')
            elif f == 'country':
                result['country'] = snippet.get('country', 'Không rõ')
            elif f == 'subscriberCount':
                sub_count = stats.get('subscriberCount')
                if sub_count and sub_count.isdigit():
                    result['subscriberCount'] = int(sub_count)
                else:
                    result['subscriberCount'] = 'Ẩn'
            elif f == 'viewCount':
                view_count = stats.get('viewCount')
                if view_count and view_count.isdigit():
                    result['viewCount'] = int(view_count)
                else:
                    result['viewCount'] = 0
            elif f == 'videoCount':
                video_count = stats.get('videoCount')
                if video_count and video_count.isdigit():
                    result['videoCount'] = int(video_count)
                else:
                    result['videoCount'] = 0
            elif f == 'channelId':
                result['channelId'] = channel_id

        return result
    
    except Exception as e:
        if debug:
            print(f"❌ Lỗi lấy thông tin kênh: {e}")
        return None

def verify_channel_match(url, channel_info):
    """
    Xác minh kênh tìm được có khớp với URL không
    """
    if not channel_info:
        return False
    
    print(f"\n🔍 VERIFICATION:")
    print(f"URL yêu cầu: {url}")
    print(f"Kênh tìm được: {channel_info.get('title', 'N/A')}")
    print(f"Channel ID: {channel_info.get('channelId', 'N/A')}")
    
    # Lấy expected name từ URL
    expected_name = None
    if '/@' in url:
        expected_name = url.split('/@')[-1]
    elif '/c/' in url:
        expected_name = url.split('/c/')[-1]
    elif '/user/' in url:
        expected_name = url.split('/user/')[-1]
    
    if expected_name:
        channel_title = channel_info.get('title', '').lower()
        expected_name = expected_name.lower()
        
        print(f"Tên mong đợi: {expected_name}")
        print(f"Tên thực tế: {channel_title}")
        
        # Simple matching
        if expected_name in channel_title or channel_title in expected_name:
            print("✅ Kênh khớp!")
            return True
        else:
            print("❌ Kênh KHÔNG khớp!")
            return False
    
    return True  # Không thể verify, coi như đúng

# Test function
def test_specific_channel():
    """
    Test với các URL cụ thể
    """
    test_urls = [
        "https://www.youtube.com/@MrBeast",
        "https://www.youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast channel ID
        "https://www.youtube.com/@pewdiepie",
        "https://www.youtube.com/c/pewdiepie",
    ]
    
    for url in test_urls:
        print(f"\n{'='*80}")
        print(f"🧪 TESTING: {url}")
        print(f"{'='*80}")
        
        fields = ['title', 'channelId', 'subscriberCount', 'viewCount', 'videoCount']
        
        try:
            channel_info = get_channel_info_by_url(url, fields, debug=True)
            
            if channel_info:
                verify_channel_match(url, channel_info)
                print(f"\n📊 RESULT:")
                print(f"Tên kênh: {channel_info.get('title')}")
                print(f"Subscribers: {channel_info.get('subscriberCount')}")
                print(f"Views: {channel_info.get('viewCount')}")
                print(f"Videos: {channel_info.get('videoCount')}")
            else:
                print("❌ Không lấy được thông tin kênh")
                
        except Exception as e:
            print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    test_specific_channel()