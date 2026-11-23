"""Nhiệm vụ 5: Kiểm tra và xác thực nhãn trích dẫn.

Xác định nhãn trích dẫn nào trong câu trả lời tồn tại trong chunks.json.
Trả về danh sách các nhãn không trùng lặp, theo đúng thứ tự xuất hiện:
check_citations(text, chunks) -> [{"label": str, "exists": bool}, ...]
"""
import re

# Regex nhận diện nhãn trích dẫn trong dấu ngoặc vuông có chứa ký tự '|'
# Cho phép khoảng trắng linh hoạt: [TT148/2018 | Điều 4 | Khoản 1] hoặc [ LUAT_NVQS/2015 | Điều 30 ]
CITATION = re.compile(r"\[\s*([A-Za-z0-9_/-]+(?:\s*\|\s*[^\[\]|]+)+)\s*\]")

# Bảng ánh xạ các dạng viết tắt / biến thể của tên văn bản sang mã chuẩn thống nhất
DOC_CANONICAL = {
    "luat_nvqs/2015": "LUAT_NVQS/2015",
    "luat_nvqs_2015": "LUAT_NVQS/2015",
    "luật_nvqs/2015": "LUAT_NVQS/2015",
    "luat nvqs 2015": "LUAT_NVQS/2015",
    "luật nvqs 2015": "LUAT_NVQS/2015",
    "luat nvqs": "LUAT_NVQS/2015",
    "luật nvqs": "LUAT_NVQS/2015",
    "luat 2015": "LUAT_NVQS/2015",
    "luật 2015": "LUAT_NVQS/2015",
    "tt148/2018": "TT148/2018",
    "tt_148/2018": "TT148/2018",
    "tt 148/2018": "TT148/2018",
    "tt148": "TT148/2018",
    "thông tư 148/2018": "TT148/2018",
    "thong tu 148/2018": "TT148/2018",
    "tt105/2023": "TT105/2023",
    "tt_105/2023": "TT105/2023",
    "tt 105/2023": "TT105/2023",
    "tt105": "TT105/2023",
    "thông tư 105/2023": "TT105/2023",
    "thong tu 105/2023": "TT105/2023",
}


def normalize_part(idx, part):
    """Chuẩn hóa từng phần tử cấu thành nhãn: văn bản, Điều, Khoản/Bảng."""
    p = part.strip()
    if idx == 0:
        # Chuẩn hóa tên văn bản
        low = p.lower()
        if low in DOC_CANONICAL:
            return DOC_CANONICAL[low]
        return p.upper()
    elif idx == 1:
        # Chuẩn hóa tiêu đề Điều
        match = re.match(r"(?i)^điều\s*(\d+)$", p)
        if match:
            return f"Điều {match.group(1)}"
        return p
    elif idx == 2:
        # Chuẩn hóa tiêu đề Khoản hoặc Bảng
        match_k = re.match(r"(?i)^khoản\s*(\d+)$", p)
        if match_k:
            return f"Khoản {match_k.group(1)}"
        match_b = re.match(r"(?i)^bảng\s*(\d+)$", p)
        if match_b:
            return f"Bảng {match_b.group(1)}"
        return p
    return p


def normalize(label):
    """Chuẩn hóa khoảng trắng và định dạng nhãn theo chuẩn thống nhất."""
    raw = label.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1].strip()
    parts = [normalize_part(i, p) for i, p in enumerate(raw.split("|"))]
    return " | ".join(parts)


def extract_citations(text):
    """Trích xuất tất cả nhãn trích dẫn trong văn bản, không trùng lặp, giữ thứ tự xuất hiện."""
    seen = set()
    out = []
    for m in CITATION.finditer(text):
        label = normalize(m.group(1))
        if label not in seen:
            seen.add(label)
            out.append(label)
    return out


def check_citations(text, chunks):
    """Kiểm tra nhãn trích dẫn trong văn bản có tồn tại trong dữ liệu chunks.json hay không.
    
    Trả về danh sách dict: [{'label': nhãn_chuẩn, 'exists': True/False}, ...]
    Đảm bảo không trùng lặp và giữ nguyên thứ tự xuất hiện đầu tiên.
    """
    known_labels = {c["nhan"] for c in chunks}
    known_lower_map = {c["nhan"].lower(): c["nhan"] for c in chunks}
    
    extracted = extract_citations(text)
    results = []
    
    for l in extracted:
        # Khớp chính xác
        if l in known_labels:
            results.append({"label": l, "exists": True})
            continue
        
        # Khớp không phân biệt chữ hoa/thường
        low = l.lower()
        if low in known_lower_map:
            results.append({"label": known_lower_map[low], "exists": True})
            continue
            
        # Không tồn tại trong cơ sở dữ liệu chunks
        results.append({"label": l, "exists": False})
        
    return results


def is_valid_citation(label, chunks):
    """Kiểm tra nhanh xem một nhãn đơn lẻ có hợp lệ và tồn tại trong chunks không."""
    norm = normalize(label)
    known_labels = {c["nhan"] for c in chunks}
    if norm in known_labels:
        return True
    known_lower = {c["nhan"].lower() for c in chunks}
    return norm.lower() in known_lower


def get_chunk_by_label(label, chunks):
    """Tìm và trả về chunk tương ứng với nhãn trích dẫn, trả về None nếu không tìm thấy."""
    norm = normalize(label)
    for c in chunks:
        if c["nhan"] == norm:
            return c
    norm_low = norm.lower()
    for c in chunks:
        if c["nhan"].lower() == norm_low:
            return c
    return None
