"""Nhiệm vụ 4 (BẢN TẠM để app chạy; người 3 thay bằng bản chính thức, giữ nguyên chữ ký hàm).

answer(question) -> cùng dạng kết quả với long_context.answer
"""
import math
import re
from collections import Counter

from .core import load_chunks_cached, run

TOP_K = 8


def tokenize(text):
    words = re.findall(r"\w+", text.lower())
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]  # thêm cặp âm tiết


def retrieve(question, chunks, k=TOP_K, k1=1.5, b=0.75):
    docs = [tokenize(c["noi_dung"] + " " + c.get("dieu_ten", "")) for c in chunks]
    avg = sum(map(len, docs)) / len(docs)
    df = Counter(t for d in docs for t in set(d))
    n = len(docs)
    q = set(tokenize(question))
    scored = []
    for c, d in zip(chunks, docs):
        tf = Counter(d)
        s = sum(math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avg))
                for t in q if t in tf)
        scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    return [c for s, c in scored[:k] if s > 0]


def answer(question):
    chunks = load_chunks_cached()
    found = retrieve(question, chunks)
    return run("bm25", question, found, cache=False,
               retrieved=[c["nhan"] for c in found])
