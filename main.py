
import os
from dotenv import load_dotenv
from openai import OpenAI

# Đọc API Key từ file .env
load_dotenv()

# Kết nối OpenAI
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Gửi câu hỏi đến AI
response = client.responses.create(
    model="gpt-5.5",
    input="Xin chào! Hãy giới thiệu ngắn gọn về Python."
)

# Hiển thị kết quả
print("AI trả lời:")
print(response.output_text)
