# Báo cáo kết quả Nhiệm vụ 1 và Nhiệm vụ 2 (Người 1)

## Hệ thống Q&A quy định nghĩa vụ quân sự (Tuần 2)

---

## 1. Nhiệm vụ 1: Chuyển đổi .docx sang Markdown

### 1.1. Các văn bản đã chuyển đổi
Đã thực hiện chuyển đổi 3 văn bản .docx pháp lý thành 3 file Markdown độc lập:
1. `Luật_NVQS_2015.md`: Luật Nghĩa vụ quân sự số 78/2015/QH13 ngày 19/06/2015.
2. `36_VBHN-BQP_670379_tt148___68_.md`: Văn bản hợp nhất số 36/VBHN-BQP ngày 22/08/2025 (Hợp nhất Thông tư 148/2018/TT-BQP và Thông tư 68/2025/TT-BQP).
3. `88_VBHN-BQP_681511__tt_105___106_.md`: Văn bản hợp nhất số 88/VBHN-BQP ngày 17/11/2025 (Hợp nhất Thông tư 105/2023/TT-BQP và Thông tư 106/2025/TT-BQP).

### 1.2. Quy ước cấu trúc và nhãn thống nhất
- Mỗi Điều là một tiêu đề cấp 2 `## Điều <số>. <Tiêu đề>`.
- Mỗi Khoản hoặc Điều (không có khoản) có một dòng nhãn riêng đặt ngay trước nội dung theo định dạng chuẩn:
  - `[LUAT_NVQS/2015 | Điều <dieu> | Khoản <khoan>]` hoặc `[LUAT_NVQS/2015 | Điều <dieu>]`
  - `[TT148/2018 | Điều <dieu> | Khoản <khoan>]` hoặc `[TT148/2018 | Điều <dieu>]`
  - `[TT105/2023 | Điều <dieu> | Khoản <khoan>]` hoặc `[TT105/2023 | Điều <dieu>]`
- Các bảng biểu (tiêu ngữ, cơ quan ban hành, nơi nhận, xác thực) được chuyển thành định dạng Markdown Table chuẩn.

### 1.3. Các lỗi và vấn đề gặp phải khi đối chiếu mắt với văn bản gốc
1. **Lẫn chú thích sửa đổi bổ sung (Footnotes):** Trong hai văn bản hợp nhất 36/VBHN-BQP và 88/VBHN-BQP có rất nhiều ký hiệu chú thích như `[1]`, `[2]`, `[3]` dẫn tới phần giải thích sửa đổi ở cuối trang. Nếu để nguyên sẽ dễ bị nhầm lẫn với nhãn trích dẫn của hệ thống. Đã chuyển các ký hiệu này thành định dạng footnote Markdown `[^1]` hoặc lược bỏ khi đưa vào nội dung tra cứu của chunk.
2. **Lỗi đánh số danh mục con ở Điều 26 Luật NVQS 2015:** Trong Khoản 1 Điều 26 có danh sách hai nhóm tuổi phục vụ lại được đánh số `1. Nhóm A...` và `2. Nhóm B...`. Khi xử lý tự động rất dễ bị hiểu nhầm thành Khoản 2 riêng biệt. Đã xử lý giữ trọn vẹn cả hai nhóm A và B trong nhãn `[LUAT_NVQS/2015 | Điều 26 | Khoản 1]`.
3. **Các Điều không phân chia Khoản:** Các điều như Điều 1, 2 Luật NVQS 2015 hoặc Điều 2, Điều 5 Thông tư 105/2023 không có các khoản 1, 2, 3 mà chỉ có các điểm a, b hoặc một đoạn văn liền. Trường hợp này quy ước để `khoan: null` và nhãn chỉ dừng ở cấp Điều `[VĂN_BẢN | Điều <dieu>]`, không tự ý đánh số Khoản 1.
4. **Phụ lục bảng tiêu chuẩn chi tiết của TT 105/2023:** Trong văn bản .docx được cấp của Thông tư 105/2023, phần phụ lục bảng khám chuyên khoa chi tiết chỉ ghi chú `| FILE ĐƯỢC ĐÍNH KÈM THEO VĂN BẢN |`, nội dung bảng biểu chi tiết không nằm trong phần thân của file văn bản hợp nhất này.

---

## 2. Nhiệm vụ 2: Tạo chunks.json và Kiểm tra dữ liệu

### 2.1. Cấu trúc dữ liệu `data/chunks.json`
Dữ liệu được trích xuất tự động qua công cụ `tools/build_chunks.py` thành file `data/chunks.json` đảm bảo:
- Mã hóa UTF-8 giữ nguyên chữ có dấu tiếng Việt (không dùng `\u...`).
- Mỗi đơn vị chunk là một đối tượng JSON gồm:
  ```json
  {
    "van_ban": "TT148/2018",
    "dieu": "4",
    "dieu_ten": "Tiêu chuẩn tuyển quân",
    "khoan": "1",
    "nhan": "TT148/2018 | Điều 4 | Khoản 1",
    "noi_dung": "1. Tuổi đời:\na) Công dân từ đủ 18 tuổi đến hết 25 tuổi;\nb) Công dân nam được đào tạo trình độ cao đẳng, đại học..."
  }
  ```
- **Tổng số chunks:** 329 đơn vị.
  - `LUAT_NVQS/2015`: 175 chunks.
  - `TT148/2018`: 37 chunks.
  - `TT105/2023`: 117 chunks.
- **Tính toàn vẹn:** 0 nhãn bị trùng lặp, 0 chunk có nội dung rỗng.

---

### 2.2. Kiểm tra ngẫu nhiên 3 Điều

#### Điều 1: Luật Nghĩa vụ quân sự 2015 - Điều 30
- **Nhãn:** `LUAT_NVQS/2015 | Điều 30`
- **Khoản:** `null`
- **Nội dung:**
  > *"Công dân đủ 18 tuổi được gọi nhập ngũ; độ tuổi gọi nhập ngũ từ đủ 18 tuổi đến hết 25 tuổi; công dân được đào tạo trình độ cao đẳng, đại học đã được tạm hoãn gọi nhập ngũ thì độ tuổi gọi nhập ngũ đến hết 27 tuổi."*
- **Đánh giá:** Khớp 100% từng câu chữ so với bản gốc Luật NVQS 2015.

#### Điều 2: Thông tư 148/2018/TT-BQP - Điều 4 (Tiêu chuẩn tuyển quân)
- **Số lượng chunks:** 4 chunks ứng với 4 khoản:
  - `TT148/2018 | Điều 4 | Khoản 1` (Tuổi đời: 18 đến 25, cao đẳng/đại học hoãn thì đến 27)
  - `TT148/2018 | Điều 4 | Khoản 2` (Tiêu chuẩn chính trị)
  - `TT148/2018 | Điều 4 | Khoản 3` (Tiêu chuẩn sức khỏe: loại 1, 2, 3; cận thị > 1.5 điốp, viễn thị, BMI < 18.0 hoặc > 29.9 không gọi)
  - `TT148/2018 | Điều 4 | Khoản 4` (Tiêu chuẩn văn hóa: từ lớp 8 trở lên)
- **Đánh giá:** Đã cập nhật đúng nội dung sửa đổi bổ sung mới nhất theo Thông tư 68/2025/TT-BQP (văn bản hợp nhất 36/VBHN-BQP).

#### Điều 3: Thông tư 105/2023/TT-BQP - Điều 4 (Tiêu chuẩn sức khỏe)
- **Số lượng chunks:** 4 chunks ứng với 4 khoản:
  - `TT105/2023 | Điều 4 | Khoản 1` (Tiêu chuẩn sức khỏe thực hiện NVQS: loại 1, 2, 3; không nghiện ma túy)
  - `TT105/2023 | Điều 4 | Khoản 2` (Tiêu chuẩn sức khỏe tuyển sinh quân sự: loại 1, 2)
  - `TT105/2023 | Điều 4 | Khoản 3` (Tiêu chuẩn tuyển dụng cán bộ, sĩ quan dự bị)
  - `TT105/2023 | Điều 4 | Khoản 4` (Tiêu chuẩn tuyển dụng QNCN, CN&VCQP)
- **Đánh giá:** Khớp chính xác với văn bản hợp nhất 88/VBHN-BQP.

---

### 2.3. Kiểm tra ngẫu nhiên 2 Bảng biểu

#### Bảng 1: Bảng tiêu ngữ và cơ quan ban hành (36/VBHN-BQP)
- **Dạng thể hiện:**
  ```markdown
  | **BỘ QUỐC PHÒNG<br>-------** | **CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM<br>Độc lập - Tự do - Hạnh phúc<br>---------------** |
  | --- | --- |
  | Số: 36/VBHN-BQP | *Hà Nội, ngày 22 tháng 8 năm 2025* |
  ```
- **Đánh giá:** Hiển thị đúng cấu trúc 2 cột của thể thức văn bản hành chính quy phạm pháp luật Việt Nam.

#### Bảng 2: Bảng nơi nhận và ký xác thực văn bản hợp nhất (88/VBHN-BQP)
- **Dạng thể hiện:**
  ```markdown
  | Nơi nhận:<br>- Thủ tướng Chính phủ (để b/c);<br>- Các đ/c Lãnh đạo BQP;... | **XÁC THỰC VĂN BẢN HỢP NHẤT**<br>**KT. BỘ TRƯỞNG<br>THỨ TRƯỞNG<br>Thượng tướng Vũ Hải Sản** |
  | --- | --- |
  ```
- **Đánh giá:** Giữ nguyên vẹn danh sách nơi nhận và chủ thể ký xác thực văn bản.
