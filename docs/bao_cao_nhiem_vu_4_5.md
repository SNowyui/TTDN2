# Báo cáo kết quả Nhiệm vụ 4 và Nhiệm vụ 5 (Người 3)

## Hệ thống Q&A quy định nghĩa vụ quân sự (Tuần 2)

---

## 1. Nhiệm vụ 4: Hỏi đáp bằng BM25 (`qa/bm25.py`)

### 1.1. Mục tiêu và Yêu cầu
- Triển khai phương pháp truy hồi thông tin bằng thuật toán **Okapi BM25** trên tập dữ liệu gồm 329 chunks pháp luật NVQS (`data/chunks.json`).
- Tìm kiếm các Điều/Khoản liên quan nhất dựa theo từ khóa trong câu hỏi của người dùng.
- Đưa các đoạn trích liên quan vào prompt của LLM theo cùng định dạng với phương pháp Long-context (Nhiệm vụ 3) và trả về kết quả đồng nhất: `answer, refused, citations, retrieved, usage, seconds`.

### 1.2. Thiết kế Thuật toán và Kiến trúc
1. **Biểu diễn văn bản mở rộng (Searchable Document Representation):**
   - Thay vì chỉ tìm kiếm trên nội dung thô (`noi_dung`), mỗi chunk được kết hợp đầy đủ:
     $$\text{SearchText} = \text{Bí\_danh\_Văn\_bản} + \text{Số\_Điều} + \text{Tên\_Điều} + \text{Số\_Khoản} + \text{Nhãn} + \text{Nội\_dung}$$
   - Điều này đảm bảo khi người dùng hỏi đích danh: *"Theo Điều 41 Luật NVQS..."* hoặc *"Theo Thông tư 105..."*, hệ thống vẫn bắt chính xác các từ khóa văn bản và số Điều.
2. **Tokenizer và Tiền xử lý tiếng Việt:**
   - Hỗ trợ tách từ unigram kết hợp **bigram âm tiết tiếng Việt** (ví dụ: `độ_tuổi`, `tạm_hoãn`, `cận_thị`, `sức_khỏe`) để nắm bắt ngữ nghĩa cụm từ pháp lý.
   - Giữ nguyên các giá trị số thực có dấu phẩy/chấm (như `1.5` diop, `18.0` BMI, `29.9` BMI).
   - Bộ lọc **Stopwords tiếng Việt**: loại bỏ các hư từ gây nhiễu điểm số (*là, và, của, các, những, được, trong, có, thì, khi, cho, ở, theo, nào, gì, sao, thế nào, ra sao...*).
3. **Chỉ mục Inverted Index và Caching:**
   - Xây dựng lớp `BM25Index` với bảng chỉ mục ngược (`inverted_index[term] -> [(doc_id, tf)]`), tính trước toàn bộ độ dài tài liệu $dl$ và tần số văn bản $df$.
   - Sử dụng cơ chế Singleton Cache trong bộ nhớ, chỉ khởi tạo chỉ mục 1 lần duy nhất lúc khởi động hệ thống. Thời gian truy vấn trung bình giảm xuống **dưới 1ms**.
4. **Mở rộng ngữ cảnh cấp Điều (Context Expansion):**
   - Đề bài yêu cầu: *"Tìm các Điều liên quan theo từ khóa rồi đưa vào prompt"*.
   - Trong dữ liệu, mỗi chunk là một Khoản. Để tránh việc câu trả lời bị đứt đoạn do chỉ lấy được 1 Khoản lẻ tẻ, hệ thống tự động nhận diện các Điều có độ khớp cao nhất và mở rộng đưa thêm các Khoản liên đới cùng Điều vào prompt (giới hạn tối đa $k + 4$ chunks).
5. **Hiệu chỉnh Siêu tham số:**
   - $k_1 = 1.5$: Độ bão hòa tần số từ khóa.
   - $b = 0.35$: Hệ số phạt độ dài tài liệu. Với văn bản pháp lý, các điều khoản liệt kê điều kiện quan trọng (như Điều 41 tạm hoãn gồm 7 điểm a-g) thường rất dài; mức $b = 0.35$ giúp tránh việc phạt oan các điều khoản dài so với mức mặc định $b = 0.75$.

---

## 2. Nhiệm vụ 5: Kiểm tra trích dẫn (`qa/citations.py`)

### 2.1. Mục tiêu và Yêu cầu
- Viết hàm `check_citations(text, chunks)` để xác định mọi nhãn trích dẫn có trong văn bản trả lời của LLM có thực sự tồn tại trong `chunks.json` hay không.
- Loại bỏ các nhãn trùng lặp và giữ nguyên thứ tự xuất hiện đầu tiên.
- Trả về danh sách: `[{"label": str, "exists": bool}, ...]`.

### 2.2. Điểm cải tiến và Tính linh hoạt (Robustness)
1. **Biểu thức chính quy linh hoạt:**
   - Nhận diện các nhãn trích dẫn dạng `[VĂN_BẢN | Điều X | Khoản Y]` hoặc `[VĂN_BẢN | Điều X]`.
   - Hỗ trợ nhận diện cả khi có khoảng trắng dư thừa ở đầu/cuối ngoặc vuông.
2. **Chuẩn hóa nhãn (Normalization):**
   - Hàm `normalize(label)` chuẩn hóa khoảng trắng quanh dấu gạch `|`.
   - Chuẩn hóa chữ hoa/chữ thường cho các cụm từ: `Điều <số>`, `Khoản <số>`, `Bảng <số>`.
   - Bảng ánh xạ bí danh `DOC_CANONICAL` giúp tự động chuyển đổi các biến thể (ví dụ `luật nvqs 2015` -> `LUAT_NVQS/2015`, `tt 148/2018` -> `TT148/2018`).
3. **So khớp hai tầng (Two-tier matching):**
   - Tầng 1: So khớp chính xác 100% với tập hợp `known_labels`.
   - Tầng 2: So khớp không phân biệt chữ hoa/thường (`known_lower_map`) để tránh việc LLM viết hoa/thường khác biệt mà bị đánh dấu nhầm thành trích dẫn ảo.
4. **Hàm tiện ích bổ sung:**
   - `is_valid_citation(label, chunks)`: Kiểm tra nhanh tính hợp lệ của một nhãn.
   - `get_chunk_by_label(label, chunks)`: Truy xuất trực tiếp đối tượng chunk để phục vụ API xem nội dung Điều/Khoản trong Nhiệm vụ 9.

---

## 3. Kết quả Thử nghiệm và Đánh giá

### 3.1. Kết quả kiểm thử Unit Tests (`tests/test_task4_task5.py`)
Đã xây dựng bộ 11 bài kiểm thử tự động, toàn bộ **11/11 tests đều PASS (100%)**:
- `test_exact_citation_exists`: Kiểm tra trích dẫn chính xác tồn tại.
- `test_nonexistent_citation_flagged`: Nhận diện chính xác trích dẫn ảo (Điều 99, Điều 88).
- `test_case_insensitive_and_whitespace_normalization`: Chuẩn hóa hoa/thường và khoảng trắng thừa.
- `test_deduplication_and_order_preservation`: Khử trùng lặp và giữ nguyên thứ tự.
- `test_helper_functions`: Kiểm tra các hàm `is_valid_citation` và `get_chunk_by_label`.
- `test_tokenizer_numbers_and_bigrams`: Tách số thực `1.5`, `29.9` và cụm từ ghép `cận_thị`.
- `test_retrieval_age_query`: Bắt chính xác Điều 30 Luật NVQS và Điều 4 Khoản 1 TT 148.
- `test_retrieval_article_specific_query`: Bắt chính xác Điều 41 Khoản 1 khi người dùng nhắc tên Điều.
- `test_retrieval_eye_and_bmi`: Bắt chính xác Điều 4 Khoản 3 TT 148 về cận thị và BMI.
- `test_retrieval_off_topic_returns_empty_or_low_score`: Xử lý câu hỏi ngoài phạm vi.
- `test_bm25_answer_mock`: Đảm bảo schema trả về tương thích hoàn toàn với hệ thống và giao diện app.

### 3.2. Đánh giá truy hồi trên Bộ 15 câu kiểm thử (Nhiệm vụ 7)
- **Tỷ lệ truy hồi đúng các Điều/Khoản căn cứ pháp lý:** Đạt **85.7% (12/14 câu có căn cứ)** khớp đầy đủ 100% các nhãn trích dẫn yêu cầu vào Top Retrieved.
- **Tốc độ truy hồi:** Thời gian tìm kiếm BM25 trung bình đạt **0.8ms / câu**, đáp ứng hoàn hảo yêu cầu thời gian thực của ứng dụng web.
