from openai import OpenAI
import os

# Lấy API key từ biến môi trường hoặc nhập trực tiếp
# api_key = os.getenv("CHATGPT_KEY")  # Cách 1: qua biến môi trường
api_key = "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"        # Cách 2: nhập thẳng key (không khuyến nghị)

def test_openai_key():
    try:
        client = OpenAI(api_key=api_key)

        # Gửi request test đơn giản
        response = client.models.list()

        print("✅ API key hoạt động bình thường!")
        print("Danh sách vài model khả dụng:")
        for model in response.data[:5]:
            print("-", model.id)

    except Exception as e:
        print("❌ API key không hợp lệ hoặc có lỗi khi kết nối:")
        print(e)

if __name__ == "__main__":
    test_openai_key()
