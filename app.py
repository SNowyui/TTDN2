"""Nhiệm vụ 9: máy chủ web cục bộ cho giao diện hỏi đáp.

Chạy: python app.py [cổng]   rồi mở http://127.0.0.1:8000
Giao diện chỉ gọi long_context.answer / bm25.answer / check_citations, không viết lại logic.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from qa import bm25, long_context
from qa.core import load_chunks_cached
from qa.citations import normalize
from qa.llm import LLMError, key_name, model_name

STATIC = Path(__file__).resolve().parent / "static"
MODES = {"long_context": long_context.answer, "bm25": bm25.answer}
MAX_QUESTION = 1000


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path == "/":
                self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif url.path == "/api/status":
                self._send(200, {"api_key": bool(os.environ.get(key_name()) or os.environ.get("QA_MOCK")),
                                 "mock": bool(os.environ.get("QA_MOCK")), "model": model_name(),
                                 "chunks": len(load_chunks_cached())})
            elif url.path == "/api/chunk":
                label = normalize(parse_qs(url.query).get("label", [""])[0])
                for c in load_chunks_cached():
                    if c["nhan"] == label:
                        return self._send(200, {"ok": True, "chunk": c})
                self._send(404, {"ok": False, "error": {"message": "Nhãn này không tồn tại trong dữ liệu."}})
            else:
                self._send(404, {"ok": False, "error": {"message": "Không tìm thấy trang."}})
        except Exception as e:  # không để lỗi làm sập tiến trình
            self._send(500, {"ok": False, "error": {"message": f"Lỗi hệ thống: {e}"}})

    def do_POST(self):
        if urlparse(self.path).path != "/api/ask":
            return self._send(404, {"ok": False, "error": {"message": "Không tìm thấy."}})
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length).decode("utf-8"))
            question = str(req.get("question", "")).strip()
            mode = req.get("mode")
            if not question:
                return self._send(400, {"ok": False, "error": {"message": "Hãy nhập câu hỏi."}})
            if len(question) > MAX_QUESTION:
                return self._send(400, {"ok": False, "error": {"message": f"Câu hỏi quá dài (tối đa {MAX_QUESTION} ký tự)."}})
            if mode not in MODES:
                return self._send(400, {"ok": False, "error": {"message": "Cách trả lời không hợp lệ."}})
            self._send(200, {"ok": True, "result": MODES[mode](question)})
        except LLMError as e:
            self._send(200, {"ok": False, "error": {"code": e.code, "message": e.message}})
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"ok": False, "error": {"message": "Yêu cầu không đọc được."}})
        except FileNotFoundError:
            self._send(500, {"ok": False, "error": {"message": "Thiếu data/chunks.json. Xem README."}})
        except Exception as e:
            self._send(500, {"ok": False, "error": {"message": f"Lỗi hệ thống: {e}"}})

    def log_message(self, fmt, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Mở http://127.0.0.1:{port}  (Ctrl+C để dừng)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
