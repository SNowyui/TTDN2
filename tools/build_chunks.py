"""Tạo data/chunks.json từ 3 file .md chuẩn của nhóm (Nhiệm vụ 2).

Chuyển các file .md thành dữ liệu có cấu trúc chunks.json:
- Mỗi đơn vị gồm: van_ban, dieu, dieu_ten, khoan, nhan, noi_dung.
- Nhãn không trùng lặp, nội dung không rỗng.
- UTF-8 không thoát ký tự Unicode (ensure_ascii=False).

Chạy:
    python tools/build_chunks.py
hoặc:
    python tools/build_chunks.py Luật_NVQS_2015.md 36_VBHN-BQP_670379_tt148___68_.md 88_VBHN-BQP_681511__tt_105___106_.md
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOC_CONFIG = [
    ("LUAT_NVQS/2015", ["Luật_NVQS_2015.md", "78/2015/QH13"]),
    ("TT148/2018", ["36_VBHN-BQP_670379_tt148___68_.md", "36/VBHN-BQP"]),
    ("TT105/2023", ["88_VBHN-BQP_681511__tt_105___106_.md", "88/VBHN-BQP"]),
]


def detect_doc_code(file_path):
    text = Path(file_path).read_text(encoding="utf-8")
    head = "\n".join(text.splitlines()[:50])
    for code, hints in DOC_CONFIG:
        for hint in hints:
            if hint in head or hint in Path(file_path).name:
                return code
    raise ValueError(f"Không nhận diện được mã văn bản cho file: {file_path}")


def parse_markdown_to_chunks(file_path, doc_code):
    lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    chunks = []
    cur_dieu_ten = ""
    cur_label = None
    cur_content = []

    label_pattern = re.compile(rf"^\[{re.escape(doc_code)} \| Điều (\d+)(?: \| Khoản (\d+))?\]$")
    dieu_pattern = re.compile(r"^##\s*Điều\s*(\d+)\.\s*(.*)$")

    def flush():
        nonlocal cur_content
        if cur_label:
            body = "\n".join(cur_content).strip()
            # Loại bỏ đánh dấu footnote [^n]
            body = re.sub(r"\[\^\d+\]", "", body).strip()
            if body:
                m = label_pattern.match(cur_label)
                if m:
                    dieu_num = m.group(1)
                    khoan_num = m.group(2) if m.group(2) else None
                    chunks.append({
                        "van_ban": doc_code,
                        "dieu": dieu_num,
                        "dieu_ten": cur_dieu_ten,
                        "khoan": khoan_num,
                        "nhan": cur_label[1:-1],
                        "noi_dung": body
                    })
        cur_content = []

    for line in lines:
        if line.startswith("Nơi nhận:") or line.startswith("| Nơi nhận:"):
            break
        dm = dieu_pattern.match(line.strip())
        if dm:
            cur_dieu_ten = dm.group(2).strip()
            continue
        lm = label_pattern.match(line.strip())
        if lm:
            flush()
            cur_label = line.strip()
            continue
        if cur_label:
            cur_content.append(line)
    flush()
    return chunks


def build(file_paths, output_path):
    all_chunks = []
    found_docs = {}
    for p in file_paths:
        code = detect_doc_code(p)
        found_docs[code] = p

    for code, _ in DOC_CONFIG:
        if code not in found_docs:
            raise RuntimeError(f"Thiếu file cho văn bản: {code}")
        chunks = parse_markdown_to_chunks(found_docs[code], code)
        print(f"[{code}] {len(chunks)} chunks từ {found_docs[code]}")
        all_chunks.extend(chunks)

    labels = [c["nhan"] for c in all_chunks]
    dup = {l for l in labels if labels.count(l) > 1}
    assert not dup, f"Nhãn bị trùng: {dup}"
    assert all(c["noi_dung"].strip() for c in all_chunks), "Có chunk bị rỗng nội dung!"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Hoàn thành: Đã ghi {len(all_chunks)} chunks vào {output_path}")


def main():
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = [
            ROOT / "Luật_NVQS_2015.md",
            ROOT / "36_VBHN-BQP_670379_tt148___68_.md",
            ROOT / "88_VBHN-BQP_681511__tt_105___106_.md"
        ]
    build(files, ROOT / "data" / "chunks.json")


if __name__ == "__main__":
    main()
