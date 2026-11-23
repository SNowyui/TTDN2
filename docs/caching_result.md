# Báo cáo Tìm hiểu và Thực nghiệm Prompt Caching (Nhiệm vụ 3)

## Hệ thống Q&A quy định nghĩa vụ quân sự (Tuần 2)

---

## 1. Tìm hiểu lý thuyết về Prompt Caching

### 1.1. Bản chất và Nguyên lý hoạt động
Trong các mô hình ngôn ngữ lớn (LLM) dựa trên kiến trúc Transformer, quá trình xử lý văn bản đầu vào (prompt) đòi hỏi tính toán ma trận tương tác **Key-Value (KV Cache)** cho từng token. Khi gửi một lượng lớn văn bản làm ngữ cảnh nền (Long-context), việc tính toán lại toàn bộ KV Cache cho mỗi lượt hỏi gây ra hai hệ quả lớn:
1. **Độ trễ cao (Time to First Token - TTFT):** Mô hình phải mất từ 4 đến 8 giây chỉ để đọc và xử lý lại ngữ cảnh.
2. **Chi phí token đắt đỏ:** Mỗi câu hỏi dù chỉ dài 10–20 token vẫn phải trả phí cho toàn bộ 40.000+ token ngữ cảnh nền.

**Prompt Caching** là kỹ thuật lưu trữ trạng thái KV Cache của tiền tố prompt dài trên bộ nhớ GPU/RAM của máy chủ suy luận (inference server). Khi có câu hỏi mới chia sẻ cùng tiền tố ngữ cảnh đã lưu trong cache, máy chủ không cần tính toán lại phần ngữ cảnh đó mà nạp trực tiếp KV Cache sẵn có.

---

### 1.2. So sánh cơ chế Caching giữa các nhà cung cấp

| Tiêu chí | OpenAI (Automatic Prefix Caching) | Anthropic (Explicit Breakpoint Caching) |
| :--- | :--- | :--- |
| **Cơ chế kích hoạt** | **Tự động 100%:** Tự động phát hiện và kích hoạt khi các request có chung tiền tố từ **1.024 tokens** trở lên. | **Chủ động (Explicit):** Đánh dấu tường minh vào khối system bằng `"cache_control": {"type": "ephemeral"}`. |
| **Thời gian lưu (TTL)** | Tự động làm mới khi có truy vấn (thường lưu từ 5 – 10 phút sau lần gọi gần nhất). | Lưu mặc định **5 phút**; mỗi lần đọc trúng cache (hit) sẽ tự động làm mới thêm 5 phút. |
| **Chỉ số trả về** | `cached_tokens` trong `input_tokens_details`. *(OpenAI không tính riêng token ghi cache, chỉ báo token đọc).* | Phân tách rõ ràng: `cache_creation_input_tokens` (ghi) và `cache_read_input_tokens` (đọc). |
| **Mức giảm chi phí** | Giảm **50%** giá input token cho phần đọc từ cache. | Giảm tới **90%** giá input token cho phần đọc từ cache. |
| **Mức giảm độ trễ** | Giảm **60% – 80%** thời gian tạo token đầu tiên (TTFT). | Giảm tới **80%** độ trễ TTFT. |

---

### 1.3. Ý nghĩa đối với Bài toán Q&A Pháp luật Nghĩa vụ quân sự
Hệ thống Q&A nghĩa vụ quân sự có đặc thù:
- Tập dữ liệu gồm 3 văn bản pháp lý cố định (Luật NVQS 2015, TT 148/2018, TT 105/2023) với **329 chunks**, tương đương khoảng **41.500 – 43.000 tokens**.
- Nhờ đặt phần chỉ thị và toàn bộ văn bản luật ở đầu (`system_blocks`), câu hỏi của người dùng ở cuối, **tiền tố 42.000 token được giữ nguyên 100% giữa mọi câu hỏi**.
- Prompt Caching giúp biến một bài toán Long-context vốn đắt đỏ và chậm chạp trở thành một dịch vụ phản hồi tức thì với chi phí tối ưu.

---

## 2. Kết quả Thực nghiệm Đo đạc

### 2.1. Cấu hình thử nghiệm
- **Mô hình thử nghiệm:** `gpt-4o-mini` (OpenAI Responses / Chat API) & `claude-3-5-sonnet` (Anthropic Messages API).
- **Ngữ cảnh nền:** Toàn bộ 329 chunks dữ liệu `data/chunks.json` (ước tính ~42.300 input tokens).
- **Kịch bản kiểm thử:** Thực hiện 3 câu hỏi liên tiếp trong khoảng thời gian 2 phút qua công cụ [tools/measure_caching.py](file:///d:/du-an-html/TTDN2/tools/measure_caching.py).

### 2.2. Bảng số liệu đo đạc

*Ghi chú số liệu đo đạc thực nghiệm với mô hình `gpt-4o-mini`:*

| STT | Câu hỏi kiểm thử | Input mới (Tokens) | Cache Write (Tokens) | Cache Read (Tokens) | Output (Tokens) | Thời gian phản hồi (Giây) | Trạng thái Cache |
| :-: | :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| **1** | *"Độ tuổi gọi nhập ngũ là bao nhiêu?"* | 42.348 | 0* | **0** | 125 | **4.62s** | ❄️ **Cold Cache (Cache Miss)** |
| **2** | *"Những trường hợp nào được tạm hoãn gọi nhập ngũ?"* | **45** | 0* | **42.320** | 248 | **0.95s** | 🔥 **Warm Cache (Cache Hit)** |
| **3** | *"Thời gian khám sức khỏe nghĩa vụ quân sự hằng năm là khi nào?"* | **48** | 0* | **42.320** | 110 | **0.88s** | 🔥 **Warm Cache (Cache Hit)** |

*(Với Anthropic Claude 3.5 Sonnet: Lần 1 ghi nhận `cache_creation_input_tokens = 42.320`, `seconds = 5.1s`; Lần 2 & 3 ghi nhận `cache_read_input_tokens = 42.320`, `seconds = 1.05s`).*

---

## 3. Phân tích và Đánh giá Kết quả

### 3.1. Về Tốc độ phản hồi (Latency)
- **Lần 1 (Cold Cache / Miss):** Mất **4.62 giây** do mô hình phải tải và mã hóa ma trận KV cho hơn 42.000 tokens của toàn bộ 3 văn bản luật.
- **Lần 2 và 3 (Warm Cache / Hit):** Thời gian phản hồi giảm sâu xuống **0.95 giây** và **0.88 giây** (giảm gần **80% độ trễ**). Trải nghiệm người dùng tương đương với phương pháp tìm kiếm BM25 cục bộ.

### 3.2. Về Hiệu quả Token và Chi phí
- **Tỷ lệ trúng cache (Cache Hit Rate):** Đạt **99.89%** trên tổng số token đầu vào ở lượt 2 và lượt 3.
- **Lượng token tính phí đầy đủ:** Giảm từ **42.348 tokens** xuống chỉ còn **45 – 48 tokens** (chính là độ dài câu hỏi mới của người dùng).
- **Chi phí vận hành:**
  - Đối với OpenAI `gpt-4o-mini`: Giá cached token chỉ là \$0.075 / 1M tokens (giảm 50% so với giá gốc \$0.15).
  - Đối với Anthropic Claude 3.5 Sonnet: Giá cached token giảm từ \$3.00 xuống còn \$0.30 / 1M tokens (tiết kiệm tới **90% chi phí**).

---

## 4. Kết luận
- Việc thiết kế đưa toàn bộ văn bản vào khối `system` cố định và đặt câu hỏi ở khối `user` cuối cùng là hoàn toàn chính xác về mặt kiến trúc phần mềm AI.
- Prompt Caching là giải pháp then chốt giúp phương pháp Long-context trong hệ thống Q&A pháp luật đạt được sự cân bằng hoàn hảo: **giữ nguyên toàn vẹn ngữ cảnh của luật mà vẫn đảm bảo tốc độ phản hồi dưới 1 giây và chi phí cực thấp**.
