# TTDN2

# Hệ thống Q&A quy định nghĩa vụ quân sự (Tuần 2, phần người 2: Nhiệm vụ 3 và 9)

Hỏi đáp tiếng Việt về Luật NVQS 2015, Thông tư 148/2018 và Thông tư 105/2023, có trích dẫn Điều/Khoản.
Chỉ dùng thư viện chuẩn của Python 3.9+, không cần cài gói nào.

## Chạy app

1. Dùng chung file `.env` của repo nhóm (xem `.env.example`): đặt `OPENAI_API_KEY`; đổi mô hình bằng `OPENAI_MODEL` (mặc định `gpt-5.5`, giống `main.py`).
   Muốn dùng Claude: `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=...`, tùy chọn `ANTHROPIC_MODEL`.
2. `python app.py` rồi mở http://127.0.0.1:8000 (đổi cổng: `python app.py 9000`).
3. Chạy thử không cần khóa API: `QA_MOCK=1 python app.py` (dữ liệu giả lập; thử lỗi bằng `QA_MOCK=rate_limit`, `auth`, `timeout`).
4. Kiểm thử: `python -m unittest discover -s tests`.

## Cấu trúc

| Đường dẫn                                       | Việc                                          | Của                                                                                                       |
| ----------------------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `qa/long_context.py`, `qa/core.py`, `qa/llm.py` | NV3: long-context, prompt, gọi API, xử lý lỗi | người 2                                                                                                   |
| `app.py`, `static/index.html`                   | NV9: giao diện                                | người 2                                                                                                   |
| `qa/bm25.py`, `qa/citations.py`                 | NV4, NV5                                      | **bản tạm**, người 3 thay                                                                                 |
| `Luật_NVQS_2015.md`, `36_VBHN...md`, `88_VBHN...md` | NV1: 3 file Markdown giữ cấu trúc Điều/Khoản, bảng biểu, nhãn chuẩn | người 1 |
| `data/chunks.json`, `tools/build_chunks.py`     | NV2: dữ liệu có cấu trúc từ Markdown (329 chunks, UTF-8) | người 1 |
| `docs/bao_cao_nhiem_vu_1_2.md`                  | Báo cáo đối chiếu văn bản gốc, lỗi gặp phải, kiểm tra ngẫu nhiên 3 Điều, 2 bảng | người 1 |

Lưu ý: gọi OpenAI qua Responses API chưa được thử với khóa thật; nếu lỗi, đọc thông báo trên giao diện và báo lại.

Các bản tạm giữ đúng chữ ký hàm, nên thay file là chạy, không cần sửa giao diện:
`bm25.answer(question)`, `citations.check_citations(text, chunks)`, `chunks.json` theo schema đề bài (có thêm trường `dieu_ten`, thiếu cũng không lỗi).
Cả hai cách trả lời trả về cùng một dạng: `answer, refused, citations[{label, exists}], retrieved, usage, seconds`.

## Nhiệm vụ 3: long-context và prompt caching

- Toàn bộ chunks (khoảng 127 nghìn ký tự, ước 42-63 nghìn token) nằm trong khối `system` cùng quy tắc: chỉ dựa vào văn bản, chép nguyên nhãn trong `[...]`, không có thông tin thì mở đầu bằng `KHÔNG TÌM THẤY:`.
- **OpenAI:** caching tự động với tiền tố prompt trùng nhau từ 1024 token, không cần bật. App đặt quy tắc và văn bản ở đầu (phần cố định), câu hỏi ở cuối nên các câu sau trúng cache. Số trúng cache hiện ở "Token đọc từ cache" (lấy từ `cached_tokens`); "Token ghi vào cache" luôn là 0 vì OpenAI không tính riêng.
- **Anthropic:** khối văn bản gắn `cache_control: ephemeral`, cache sống 5 phút, đọc trúng thì làm mới; có cả số ghi và số đọc cache.
- Kỳ vọng: câu 1 không hoặc ít trúng cache; các câu sau trong vài phút có "đọc từ cache" lớn, "đầu vào không cache" nhỏ, thời gian giảm.
- Chạy `python tools/measure_caching.py` để đo 3 câu liên tiếp, kết quả ghi vào `docs/caching_result.md`. **Chưa chạy được ở bản giao này (chưa có khóa API), cần chạy và dán kết quả vào báo cáo.**

## Nhiệm vụ 9: giao diện

Nhập câu hỏi, chọn long-context hoặc BM25, xem câu trả lời với nhãn trích dẫn bấm được (hiện nội dung Điều/Khoản), nhãn không tồn tại bị gạch đỏ kèm cảnh báo, xem token và thời gian. Lỗi API (thiếu khóa, sai khóa, quota/429, hết credit, quá tải, mất mạng, hết thời gian) hiện thông báo tiếng Việt, app không sập. Có dòng "Chỉ mang tính tham khảo".

Ảnh chụp: `docs/screenshot_main.png` (chụp ở chế độ giả lập, **cần chụp lại bằng khóa thật trước khi nộp**).

## Lỗi dữ liệu đã biết (bản chunks tạm)

- Luật 2015 Điều 26 khoản 1 có danh sách con đánh số lại từ 1 (Nhóm A, Nhóm B), nên "Nhóm A" nằm trong Khoản 1 và "Nhóm B" bị tách thành Khoản 2.
- Bỏ qua chú thích cuối trang và các phụ lục (file Thông tư 105 không chứa nội dung phụ lục).
- Chunk được tách theo Khoản; các điểm a), b)... nằm trong nội dung Khoản, nhãn chưa tới cấp điểm.
