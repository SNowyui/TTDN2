# Báo cáo Đánh giá và So sánh Hệ thống Q&A (Nhiệm vụ 7 & 8)

## Hệ thống tra cứu quy định nghĩa vụ quân sự (Tuần 2)

---

## 1. Mục tiêu và Phạm vi Kiểm thử (Nhiệm vụ 7)

Bộ kiểm thử được xây dựng và chuẩn hóa tại [Bo_15_cau_hoi_kiem_thu.json](Bo_15_cau_hoi_kiem_thu.json) gồm **15 câu hỏi** bao quát toàn diện các tình huống nghiệp vụ:
- **12 câu hỏi nghiệp vụ / kiến thức luật (Q01 – Q12):** Bao gồm độ tuổi (18–25, 27), tiêu chuẩn văn hóa lớp 7, thời điểm gọi nhập ngũ (tháng 2/3), các trường hợp tạm hoãn học tập, hoàn cảnh gia đình khó khăn, thân nhân tại ngũ, miễn NVQS cho con liệt sĩ, quyền lợi nguyên lương khi đi khám, tiêu chuẩn sức khỏe loại 1–3, thang điểm 1–6, loại trừ cận thị > 1.5 điốp & BMI, sơ tuyển tại Trạm y tế cấp xã.
- **2 câu hỏi thiếu dữ kiện (Q13, Q14):** Hỏi về lịch khám cá nhân và chỉ tiêu của xã. Yêu cầu hệ thống nhận diện thiếu thông tin và bắt đầu câu trả lời bằng đúng cụm từ quy ước `KHÔNG TÌM THẤY:`, không đưa trích dẫn ảo.
- **1 câu hỏi ngoài phạm vi (Q15):** Hỏi thủ tục làm hộ chiếu du lịch nước ngoài. Yêu cầu hệ thống từ chối mở đầu bằng `KHÔNG TÌM THẤY:` và giải thích rõ văn bản không quy định.

---

## 2. Bảng Tổng hợp So sánh Thực nghiệm (Nhiệm vụ 8)

Thực nghiệm được thực hiện trên toàn bộ 15 câu hỏi cho cả 2 phương pháp (**Long-context** và **Okapi BM25**), tổng cộng **30 lượt chạy**. Toàn bộ nhật ký chi tiết được ghi nhận tại file Excel [Nhiem_vu_7_8_Bo_cau_hoi_va_danh_gia.xlsx](Nhiem_vu_7_8_Bo_cau_hoi_va_danh_gia.xlsx) (sheet `Log_test`).

### Bảng kết quả tổng hợp:

| Chỉ số đánh giá | Long-context (Đưa toàn bộ văn bản) | Okapi BM25 (Trích chọn đoạn liên quan) | Chênh lệch / Ưu thế |
| :--- | :---: | :---: | :--- |
| **Tổng số câu hỏi kiểm thử** | 15 | 15 | Đầy đủ 15 câu |
| **Số câu trả lời đúng** | **15 / 15** | **15 / 15** | Ngang nhau |
| **Độ chính xác (Accuracy)** | **100%** | **100%** | Cả hai đều đạt độ đúng tuyệt đối |
| **Lượt yêu cầu trích dẫn** | 12 câu (Q01–Q12) | 12 câu (Q01–Q12) | 3 câu Q13–Q15 từ chối hợp lệ |
| **Tỷ lệ nhãn trích dẫn tồn tại** | **100%** (12/12) | **100%** (12/12) | Khớp 100% với `chunks.json` |
| **Tỷ lệ trích dẫn đúng căn cứ** | **100%** (12/12) | **100%** (12/12) | Đúng căn cứ Điều/Khoản luật |
| **Hành vi từ chối (Q13–Q15)** | Đúng tiền tố `KHÔNG TÌM THẤY:` | Đúng tiền tố `KHÔNG TÌM THẤY:` | Không sinh trích dẫn ảo |
| **Lượng token trung bình** | **42.520 tokens** | **1.580 tokens** | **BM25 tiết kiệm 96.3% token** |
| **Thời gian phản hồi trung bình** | **4.45 giây** | **1.05 giây** | **BM25 nhanh gấp 4 lần** |

---

## 3. Nhận xét và Phân tích So sánh Chi tiết

### 3.1. Về Độ chính xác và Khả năng Trích dẫn
- Cả hai phương pháp đều trả lời chính xác 100% các câu hỏi tình huống và nghiệp vụ pháp luật.
- **Về tính đầy đủ:** Long-context có xu hướng trả lời chi tiết, bao quát rộng hơn do nắm giữ toàn bộ 3 văn bản luật trong ngữ cảnh. BM25 trả lời gọn gàng, bám sát các đoạn trích dẫn được xếp hạng cao nhất.
- **Về kiểm soát rủi ro ảo giác (Hallucination):** Ở 3 câu hỏi thiếu thông tin và ngoài phạm vi (Q13, Q14, Q15), cả hai phương pháp đều tuân thủ nghiêm ngặt chỉ thị từ chối, mở đầu bằng `KHÔNG TÌM THẤY:` và không tự tạo bất kỳ nhãn trích dẫn giả nào.

### 3.2. Về Chi phí Token và Kinh tế học hệ thống
- **Okapi BM25 thể hiện ưu thế vượt trội về tài nguyên:**
  - Nhờ cơ chế xếp hạng và chỉ đưa các Điều/Khoản liên quan nhất vào prompt, BM25 chỉ tiêu tốn trung bình **1.580 tokens / lượt hỏi**.
  - So với mức **42.520 tokens / lượt** của Long-context, BM25 giúp **tiết kiệm hơn 96% chi phí gọi API**, cho phép triển khai bền vững trên các gói dịch vụ giới hạn hoặc tài khoản miễn phí.

### 3.3. Về Tốc độ phản hồi (Latency)
- BM25 phản hồi gần như tức thì với thời gian trung bình **1.05 giây** (bao gồm cả thời gian chạy chỉ mục BM25 dưới 1ms và thời gian sinh câu trả lời của LLM).
- Long-context ở lượt gọi đầu tiên mất trung bình **4.45 giây** do mô hình phải tải và mã hóa lượng ngữ cảnh lớn. *(Tuy nhiên, khi kết hợp kỹ thuật Prompt Caching ở Nhiệm vụ 3, độ trễ từ lượt thứ 2 của Long-context có thể giảm xuống ~0.9s)*.

---

## 4. Kết luận Đề xuất triển khai
- **Phương pháp BM25:** Là lựa chọn hàng đầu cho các ứng dụng thực tế quy mô lớn, chatbot công cộng hoặc môi trường giới hạn kinh phí nhờ tốc độ vượt trội và chi phí token siêu rẻ.
- **Phương pháp Long-context:** Là giải pháp dự phòng lý tưởng cho các câu hỏi tổng hợp đa văn bản phức tạp, phát huy tối đa sức mạnh khi có hạ tầng Prompt Caching hỗ trợ.
