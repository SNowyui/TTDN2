"""Đo hiệu quả prompt caching của long-context (Nhiệm vụ 3).

Hỏi 3 câu liên tiếp và ghi token + thời gian vào docs/caching_result.md.
Kỳ vọng: câu 1 có cache_write lớn; câu 2, 3 có cache_read lớn, input_tokens nhỏ, thời gian giảm.
Chạy: python tools/measure_caching.py   (cần khóa API trong .env)
"""
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa import long_context  # noqa: E402
from qa.llm import LLMError, model_name  # noqa: E402

QUESTIONS = [
    "Độ tuổi gọi nhập ngũ là bao nhiêu?",
    "Những trường hợp nào được tạm hoãn gọi nhập ngũ?",
    "Thời gian khám sức khỏe nghĩa vụ quân sự hằng năm là khi nào?",
]

rows = []
for q in QUESTIONS:
    try:
        r = long_context.answer(q)
    except LLMError as e:
        sys.exit(f"Lỗi: {e.message}")
    u = r["usage"]
    rows.append(f"| {q} | {u['input_tokens']} | {u['cache_write_tokens']} | "
                f"{u['cache_read_tokens']} | {u['output_tokens']} | {r['seconds']} |")
    print(rows[-1])

out = ROOT / "docs" / "caching_result.md"
out.parent.mkdir(exist_ok=True)
out.write_text(
    f"# Kết quả đo prompt caching\n\nMô hình: `{model_name()}`, đo lúc {datetime.now():%Y-%m-%d %H:%M}.\n\n"
    "| Câu hỏi | input | cache_write | cache_read | output | Giây |\n|---|---|---|---|---|---|\n"
    + "\n".join(rows) + "\n\nGhi chú: cache mặc định sống 5 phút và được làm mới mỗi lần đọc trúng.\n",
    encoding="utf-8")
print(f"Đã ghi {out}")
