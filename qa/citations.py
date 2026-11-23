"""Nhiệm vụ 5 (BẢN TẠM để app chạy; người 3 thay bằng bản chính thức, giữ nguyên chữ ký hàm).

check_citations(text, chunks) -> [{"label": str, "exists": bool}, ...]  (không trùng, theo thứ tự xuất hiện)
"""
import re

CITATION = re.compile(r"\[([^\[\]|]+(?:\|[^\[\]|]+)+)\]")


def normalize(label):
    return " | ".join(p.strip() for p in label.split("|"))


def extract_citations(text):
    seen, out = set(), []
    for m in CITATION.finditer(text):
        label = normalize(m.group(1))
        if label not in seen:
            seen.add(label)
            out.append(label)
    return out


def check_citations(text, chunks):
    known = {c["nhan"] for c in chunks}
    return [{"label": l, "exists": l in known} for l in extract_citations(text)]
