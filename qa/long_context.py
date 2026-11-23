"""Nhiệm vụ 3: hỏi đáp long-context. Đưa TOÀN BỘ văn bản vào prompt.

Prompt caching (Anthropic: bật bằng cache_control; OpenAI: tự động theo tiền tố): khối system (quy tắc + toàn bộ văn bản) được đánh dấu cache_control,
nên từ câu hỏi thứ hai trở đi (trong ~5 phút) phần này được đọc từ cache thay vì
tính lại: số token đó hiện ở cache_read_tokens, rẻ hơn và nhanh hơn.
Câu hỏi nằm ở message người dùng, nằm SAU phần được cache, nên không làm mất cache.
"""
from .core import load_chunks_cached, run


def answer(question):
    return run("long_context", question, load_chunks_cached(), cache=True)
