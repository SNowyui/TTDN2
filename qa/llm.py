"""Gọi LLM bằng thư viện chuẩn (không cần cài gói nào). Hỗ trợ OpenAI (mặc định, theo repo nhóm), Groq và Anthropic.

Chọn nhà cung cấp bằng LLM_PROVIDER=openai|groq|anthropic; nếu bỏ trống thì tự chọn theo khóa có trong
môi trường, thứ tự OPENAI_API_KEY, GROQ_API_KEY, ANTHROPIC_API_KEY.

Mọi lỗi được đổi thành LLMError có thông báo tiếng Việt dễ hiểu để giao diện hiển thị.
Đặt QA_MOCK=1 (hoặc rate_limit / auth / timeout / badcite) để chạy thử không cần API key.
"""
import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
OPENAI_URL = "https://api.openai.com/v1/responses"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODELS = {"anthropic": "claude-3-5-sonnet-20241022", "openai": "gpt-4o-mini", "groq": "llama-3.3-70b-versatile"}
KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "groq": "GROQ_API_KEY"}
MODEL_ENV = {"anthropic": "ANTHROPIC_MODEL", "openai": "OPENAI_MODEL", "groq": "GROQ_MODEL"}
TIMEOUT_S = 120


class LLMError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def load_env():
    """Đọc file .env (KEY=VALUE) ở thư mục gốc dự án nếu có."""
    path = Path(__file__).resolve().parents[1] / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()


def provider():
    p = os.environ.get("LLM_PROVIDER", "").lower()
    if p in DEFAULT_MODELS:
        return p
    for name in ("openai", "groq", "anthropic"):
        if os.environ.get(KEY_ENV[name]):
            return name
    return "openai"


def key_name():
    return KEY_ENV[provider()]


def model_name():
    return os.environ.get(MODEL_ENV[provider()], DEFAULT_MODELS[provider()])


def _http_error(e):
    try:
        err = json.loads(e.read().decode("utf-8")).get("error", {})
        detail, code = err.get("message") or "", str(err.get("code") or "")
    except Exception:
        detail, code = "", ""
    if "credit balance" in detail.lower() or code == "insufficient_quota":
        return LLMError("quota", "Tài khoản API đã hết credit hoặc hết hạn mức. Hãy nạp thêm rồi thử lại.")
    if "model" in detail.lower() and ("access" in detail.lower() or "not exist" in detail.lower() or "found" in detail.lower()):
        return LLMError("model", f"Không có quyền truy cập mô hình '{model_name()}'. Hãy kiểm tra {MODEL_ENV[provider()]} trong .env (gợi ý: gpt-4o-mini).")
    low = detail.lower()
    if e.code in (413, 429) and ("tokens per minute" in low or "request too large" in low or "tpm" in low):
        return LLMError("too_long", "Yêu cầu vượt giới hạn token mỗi phút của gói API hiện tại (long-context gửi cả bộ văn bản, "
                                    "rất nhiều token). Hãy dùng chế độ BM25, đổi mô hình có hạn mức lớn hơn hoặc nâng gói.")
    if e.code in (401, 403):
        return LLMError("auth", f"Khóa API không hợp lệ hoặc không có quyền. Kiểm tra {key_name()}.")
    if e.code == 429:
        wait = e.headers.get("retry-after")
        extra = f" Thử lại sau khoảng {wait} giây." if wait else " Vui lòng đợi một lúc rồi thử lại."
        return LLMError("rate_limit", "Đã vượt giới hạn quota hoặc tốc độ gọi API." + extra)
    if e.code == 413 or (e.code == 400 and ("too long" in detail.lower() or "context_length" in code)):
        return LLMError("too_long", "Nội dung gửi lên quá dài so với giới hạn của mô hình.")
    if e.code == 404:
        return LLMError("model", f"Không tìm thấy mô hình '{model_name()}'. Kiểm tra biến {MODEL_ENV[provider()]}.")
    if e.code >= 500:
        return LLMError("server", "Dịch vụ AI đang tạm quá tải hoặc gặp sự cố. Hãy thử lại sau ít phút.")
    return LLMError("bad_request", f"API từ chối yêu cầu (mã {e.code}). {detail}".strip())


def _mock(system_blocks, question):
    mode = os.environ["QA_MOCK"]
    time.sleep(0.4)
    if mode == "rate_limit":
        raise LLMError("rate_limit", "Đã vượt giới hạn quota hoặc tốc độ gọi API. Vui lòng đợi một lúc rồi thử lại.")
    if mode == "auth":
        raise LLMError("auth", "Khóa API không hợp lệ hoặc không có quyền. Kiểm tra ANTHROPIC_API_KEY.")
    if mode == "timeout":
        raise LLMError("network", "Hết thời gian chờ phản hồi từ API. Hãy thử lại.")
    if "ngoài phạm vi" in question.lower() or "thủ đô" in question.lower():
        text = "KHÔNG TÌM THẤY: các văn bản được cung cấp không có thông tin để trả lời câu hỏi này."
    else:
        text = ("Công dân được gọi nhập ngũ từ đủ 18 tuổi đến hết 25 tuổi "
                "[TT148/2018 | Điều 4 | Khoản 1]; người đang học cao đẳng, đại học đã được tạm hoãn "
                "thì đến hết 27 tuổi [LUAT_NVQS/2015 | Điều 30]. "
                "(Dòng này là dữ liệu giả lập kèm một nhãn không tồn tại để thử giao diện "
                "[TT148/2018 | Điều 99 | Khoản 1].)")
    chars = sum(len(b["text"]) for b in system_blocks) + len(question)
    cached = any("cache_control" in b for b in system_blocks)
    return text, {
        "input_tokens": 30, "output_tokens": 90,
        "cache_creation_input_tokens": chars // 3 if cached else 0,
        "cache_read_input_tokens": 0,
    }


def _post(url, headers, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"content-type": "application/json", "user-agent": "nvqs-qa/1.0", **headers})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise _http_error(e) from None
    except (socket.timeout, TimeoutError):
        raise LLMError("network", "Hết thời gian chờ phản hồi từ API. Hãy thử lại.") from None
    except urllib.error.URLError as e:
        if isinstance(e.reason, (socket.timeout, TimeoutError)):
            raise LLMError("network", "Hết thời gian chờ phản hồi từ API. Hãy thử lại.") from None
        raise LLMError("network", "Không kết nối được tới API. Kiểm tra mạng của bạn.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise LLMError("server", "API trả về dữ liệu không đọc được. Hãy thử lại.") from None


def _anthropic(key, system_blocks, question, max_tokens):
    data = _post(API_URL, {"x-api-key": key, "anthropic-version": API_VERSION}, {
        "model": model_name(), "max_tokens": max_tokens, "temperature": 0,
        "system": system_blocks, "messages": [{"role": "user", "content": question}]})
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return text, data.get("usage", {})


def _openai(key, system_blocks, question, max_tokens):
    # Phần cố định (quy tắc + văn bản) đặt ở đầu prompt; OpenAI tự cache tiền tố trùng (từ 1024 token).
    data = _post(OPENAI_URL, {"authorization": f"Bearer {key}"}, {
        "model": model_name(),
        "instructions": "\n".join(b["text"] for b in system_blocks),
        "input": question,
        "max_output_tokens": max(max_tokens, 4000),  # mô hình suy luận tính cả token suy luận
    })
    if data.get("status") == "incomplete":
        raise LLMError("empty", "Mô hình chưa kịp trả lời xong. Hãy thử lại hoặc hỏi ngắn hơn.")
    text = "".join(c.get("text", "") for item in data.get("output", []) if item.get("type") == "message"
                   for c in item.get("content", []) if c.get("type") == "output_text")
    u = data.get("usage", {})
    cached = (u.get("input_tokens_details") or {}).get("cached_tokens", 0)
    # Quy về cùng dạng với Anthropic để giao diện dùng chung.
    return text, {"input_tokens": u.get("input_tokens", 0) - cached, "output_tokens": u.get("output_tokens", 0),
                  "cache_creation_input_tokens": 0, "cache_read_input_tokens": cached}


def _groq(key, system_blocks, question, max_tokens):
    payload = {
        "model": model_name(), "temperature": 0, "max_completion_tokens": max_tokens,
        "messages": [{"role": "system", "content": "\n".join(b["text"] for b in system_blocks)},
                     {"role": "user", "content": question}]}
    if "gpt-oss" in model_name():  # mô hình suy luận: giảm suy luận, chừa chỗ cho câu trả lời
        payload["reasoning_effort"] = "low"
        payload["max_completion_tokens"] = max(max_tokens, 2048)
    data = _post(GROQ_URL, {"authorization": f"Bearer {key}"}, payload)
    text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    u = data.get("usage", {})
    cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    return text, {"input_tokens": u.get("prompt_tokens", 0) - cached, "output_tokens": u.get("completion_tokens", 0),
                  "cache_creation_input_tokens": 0, "cache_read_input_tokens": cached}


def call_llm(system_blocks, question, max_tokens=1024):
    """Trả về {"text", "usage", "seconds"}; lỗi thì ném LLMError."""
    t0 = time.perf_counter()
    if os.environ.get("QA_MOCK"):
        text, usage = _mock(system_blocks, question)
        return {"text": text, "usage": usage, "seconds": time.perf_counter() - t0}

    key = os.environ.get(key_name())
    if not key:
        raise LLMError("no_key", f"Chưa cấu hình {key_name()}. Xem hướng dẫn trong README.")
    text, usage = {"openai": _openai, "groq": _groq, "anthropic": _anthropic}[provider()](
        key, system_blocks, question, max_tokens)
    if not text.strip():
        raise LLMError("empty", "Mô hình không trả về nội dung. Hãy thử lại hoặc diễn đạt lại câu hỏi.")
    return {"text": text.strip(), "usage": usage, "seconds": time.perf_counter() - t0}
