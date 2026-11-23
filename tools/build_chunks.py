"""Tạo data/chunks.json từ 3 file .md do người 1 gửi (BẢN TẠM thay cho Nhiệm vụ 2).

Khi người 1 có chunks.json chính thức (cùng schema), chép đè lên data/chunks.json là xong.
Không cần cài gói nào. Thứ tự 3 file không quan trọng, script tự nhận diện văn bản.

Dùng: python tools/build_chunks.py file1.md file2.md file3.md
"""
import json
import re
import sys
from pathlib import Path

# (tên viết tắt dùng trong nhãn, dấu hiệu nhận diện văn bản trong 40 dòng đầu file)
SOURCES = [
    ("LUAT_NVQS/2015", "78/2015/QH13"),
    ("TT148/2018", "36/VBHN-BQP"),
    ("TT105/2023", "88/VBHN-BQP"),
]

ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!<>|~])")
DIEU = re.compile(r"^Điều (\d+)\.\s*(.*)$")
KHOAN = re.compile(r"^(\d+)\.\s*(.*)$")


def clean(line):
    """Bỏ chú thích [n] / [^n], ký hiệu đậm/nghiêng, &nbsp;, <br> và dấu escape của Markdown."""
    line = re.sub(r"\\\[\d+\\\]|\[\^\d+\]|\[\d+\]", "", line)  # chú thích: \[2\], [^2], [2]
    line = ESCAPE.sub(r"\1", line)
    line = line.replace("&nbsp;", " ").replace("<br>", " ").replace("**", "")
    line = re.sub(r"(?<!\w)_|_(?!\w)", "", line)  # _nghiêng_
    return re.sub(r"[ \t]+", " ", line).strip()


def parse(lines, code):
    chunks, dieu, title, khoan, buf, last = [], None, "", None, [], 0

    def flush():
        body = "\n".join(l for l in buf if l).strip()
        if dieu is None or not body:
            return
        nhan = f"{code} | Điều {dieu}" + (f" | Khoản {khoan}" if khoan else "")
        chunks.append({"van_ban": code, "dieu": dieu, "dieu_ten": title,
                       "khoan": khoan, "nhan": nhan, "noi_dung": body})

    for raw in lines:
        if "Nơi nhận:" in raw:  # hết phần thân văn bản (phần sau là chú thích cuối trang)
            break
        ln = clean(raw)
        m = DIEU.match(ln)
        if m:
            flush()
            dieu, title, khoan, buf, last = m.group(1), m.group(2).strip(), None, [], 0
            continue
        if dieu is None or ln.startswith("|"):  # bỏ phần đầu văn bản và bảng đầu trang
            continue
        m = KHOAN.match(ln)
        # Chỉ coi là Khoản mới khi đánh số liền kề; còn lại là nội dung tiếp nối.
        if m and int(m.group(1)) == last + 1:
            flush()
            last = int(m.group(1))
            khoan, buf = str(last), [m.group(2)]
        else:
            buf.append(ln)
    flush()
    return chunks


def detect(text):
    head = "\n".join(text.splitlines()[:40])
    for code, marker in SOURCES:
        if marker in head:
            return code
    raise SystemExit("Không nhận diện được văn bản (mong đợi Luật 78/2015, 36/VBHN-BQP hoặc 88/VBHN-BQP).")


def main(paths, out):
    by_code = {}
    for p in paths:
        text = Path(p).read_text(encoding="utf-8")
        by_code[detect(text)] = text.splitlines()
    missing = [c for c, _ in SOURCES if c not in by_code]
    if missing:
        raise SystemExit(f"Thiếu văn bản: {missing}")
    all_chunks = []
    for code, _ in SOURCES:
        all_chunks += parse(by_code[code], code)
    labels = [c["nhan"] for c in all_chunks]
    dup = {l for l in labels if labels.count(l) > 1}
    assert not dup, f"Nhãn trùng: {dup}"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(all_chunks, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Đã ghi {len(all_chunks)} đơn vị vào {out}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(sys.argv[1:4], Path(__file__).resolve().parents[1] / "data" / "chunks.json")
