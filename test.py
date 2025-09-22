import requests
import re
from urllib.parse import urlparse, parse_qs

class YouTubeChannelStats:
    def __init__(self, api_key):
        """
        Khởi tạo class với API key từ Google Cloud Console
        
        Args:
            api_key (str): API key từ Google Cloud Console với YouTube Data API v3 enabled
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    def extract_channel_id(self, channel_url):
        """
        Trích xuất channel ID từ URL kênh YouTube
        
        Args:
            channel_url (str): URL của kênh YouTube
            
        Returns:
            str: Channel ID hoặc None nếu không tìm thấy
        """
        # Các pattern URL khác nhau của YouTube
        patterns = [
            r'/channel/([a-zA-Z0-9_-]+)',
            r'/c/([a-zA-Z0-9_-]+)',
            r'/user/([a-zA-Z0-9_-]+)',
            r'/@([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, channel_url)
            if match:
                identifier = match.group(1)
                
                # Nếu là channel ID (bắt đầu bằng UC), trả về luôn
                if identifier.startswith('UC'):
                    return identifier
                
                # Nếu là username hoặc custom URL, cần convert
                return self.get_channel_id_from_username(identifier)
        
        return None
    
    def get_channel_id_from_username(self, username):
        """
        Lấy channel ID từ username hoặc custom URL
        
        Args:
            username (str): Username hoặc custom name
            
        Returns:
            str: Channel ID hoặc None
        """
        # Thử với forUsername
        url = f"{self.base_url}/channels"
        params = {
            'part': 'id',
            'forUsername': username,
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['id']
        
        # Thử với forHandle (cho @username)
        params = {
            'part': 'id',
            'forHandle': username,
            'key': self.api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['id']
        
        return None
    
    def get_channel_stats(self, channel_url):
        """
        Lấy thống kê của kênh YouTube
        
        Args:
            channel_url (str): URL của kênh YouTube
            
        Returns:
            dict: Thống kê kênh hoặc None nếu có lỗi
        """
        try:
            # Trích xuất channel ID
            channel_id = self.extract_channel_id(channel_url)
            
            if not channel_id:
                return {"error": "Không thể trích xuất channel ID từ URL"}
            
            # Gọi API để lấy thống kê
            url = f"{self.base_url}/channels"
            params = {
                'part': 'statistics,snippet',
                'id': channel_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                return {"error": f"API request failed: {response.status_code}"}
            
            data = response.json()
            
            if 'items' not in data or len(data['items']) == 0:
                return {"error": "Không tìm thấy kênh hoặc kênh không công khai"}
            
            channel_info = data['items'][0]
            stats = channel_info['statistics']
            snippet = channel_info['snippet']
            
            return {
                "channel_name": snippet.get('title', 'N/A'),
                "channel_id": channel_id,
                "total_views": int(stats.get('viewCount', 0)),
                "total_subscribers": int(stats.get('subscriberCount', 0)),
                "total_videos": int(stats.get('videoCount', 0)),
                "description": snippet.get('description', '')[:200] + "..." if len(snippet.get('description', '')) > 200 else snippet.get('description', ''),
                "published_at": snippet.get('publishedAt', 'N/A'),
                "country": snippet.get('country', 'N/A')
            }
            
        except Exception as e:
            return {"error": f"Đã xảy ra lỗi: {str(e)}"}
    
    def format_number(self, num):
        """
        Format số với đơn vị K, M, B
        
        Args:
            num (int): Số cần format
            
        Returns:
            str: Số đã được format
        """
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return str(num)
    
    def print_stats(self, stats):
        """
        In thống kê kênh một cách đẹp mắt
        
        Args:
            stats (dict): Thống kê kênh
        """
        if "error" in stats:
            print(f"❌ Lỗi: {stats['error']}")
            return
        
        print("=" * 60)
        print(f"📺 Tên kênh: {stats['channel_name']}")
        print(f"🆔 Channel ID: {stats['channel_id']}")
        print(f"👀 Tổng lượt xem: {self.format_number(stats['total_views'])} ({stats['total_views']:,})")
        print(f"👥 Tổng subscriber: {self.format_number(stats['total_subscribers'])} ({stats['total_subscribers']:,})")
        print(f"🎬 Tổng video: {self.format_number(stats['total_videos'])} ({stats['total_videos']:,})")
        print(f"📅 Ngày tạo: {stats['published_at']}")
        print(f"🌍 Quốc gia: {stats['country']}")
        print(f"📝 Mô tả: {stats['description']}")
        print("=" * 60)

# Ví dụ sử dụng
def main():
    # Thay YOUR_API_KEY bằng API key thực tế của bạn
    API_KEY = "AIzaSyBEuYV9U0U9zF_OYGq5iDHqSggAs065yZQ"
    
    # Khởi tạo class
    youtube_stats = YouTubeChannelStats(API_KEY)
    
    # Các ví dụ URL kênh YouTube
    channel_urls = [
        "https://www.youtube.com/@MrBeast",
        "https://www.youtube.com/@truyenhinh4k",
        "https://www.youtube.com/c/pewdiepie"
    ]
    
    for url in channel_urls:
        print(f"\n🔍 Đang lấy thống kê cho: {url}")
        stats = youtube_stats.get_channel_stats(url)
        youtube_stats.print_stats(stats)

if __name__ == "__main__":
    main()