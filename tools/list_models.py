"""Liệt kê các mô hình khóa Groq của bạn dùng được (đọc GROQ_API_KEY từ .env).

Chạy: python tools/list_models.py
Rồi đặt GROQ_MODEL=<tên mô hình> trong .env.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qa import llm  # noqa: E402,F401  (nạp .env)

key = os.environ.get("GROQ_API_KEY")
if not key:
    sys.exit("Chưa có GROQ_API_KEY trong .env")
req = urllib.request.Request("https://api.groq.com/openai/v1/models",
                             headers={"authorization": f"Bearer {key}", "user-agent": "nvqs-qa/1.0"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        models = json.loads(r.read().decode("utf-8"))["data"]
except Exception as e:
    sys.exit(f"Lỗi: {e}")
print(f"{'Mô hình':45} {'Context':>9}")
for m in sorted(models, key=lambda m: m["id"]):
    print(f"{m['id']:45} {m.get('context_window', '?'):>9}")
