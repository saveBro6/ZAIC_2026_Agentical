# Báo Cáo Phân Tích Khám Phá Dữ Liệu (EDA) - dataset/train/answers.jsonl

## 1. Tổng Quan Tập Dữ Liệu

- **Đường dẫn tệp**: `dataset/train/answers.jsonl`
- **Tổng số bản ghi**: **3,000** dòng (tương ứng chính xác 3,000 câu hỏi từ `dataset/train/questions.jsonl`).
- **Cấu trúc trường dữ liệu (Keys)**: Mỗi dòng là một JSON object với 4 trường cố định:
  1. `id` (string): Mã định danh duy nhất của câu hỏi (VD: `q_001883280e83`).
  2. `type` (string): Nhãn phân loại kiểu dữ liệu đầu ra (8 loại khác nhau).
  3. `answer` (string / number / list / dict / null): Giá trị câu trả lời ground truth.
  4. `alias` (list): Danh sách các tên gọi thay thế hợp lệ (mã sản phẩm, mã khách hàng, tên không dấu).
- **Kiểm tra tính toàn vẹn (Null Values)**: Hoàn toàn không có trường bị thiếu khuyết bất thường. Chỉ duy nhất trường `answer` có **70 giá trị null** (2.33%), toàn bộ thuộc phân loại `type = "unanswerable"`.

## 2. Phân Loại Số Lượng Theo "type"

Theo Problem Contract của cuộc thi DataMate, mỗi câu trả lời thuộc về một trong các nhãn kiểu dữ liệu định sẵn. Thống kê chi tiết số lượng và tỷ trọng trên tập train như sau:

| STT | Kiểu dữ liệu (`type`) | Số lượng câu hỏi | Tỷ trọng (%) | Đặc tả nội dung & Quy tắc so khớp theo Problem Contract |
| :-: | :--- | :---: | :---: | :--- |
| 1 | **`number`** | 1,884 | 62.80% | Số nguyên đại diện tiền tệ (VND), số lượng hàng, số đơn hàng. **Yêu cầu khớp chính xác tuyệt đối (Exact match)**. |
| 2 | **`percent`** | 578 | 19.27% | Số thực phần trăm (đã làm tròn 2 chữ số thập phân, lưu ý ghi `12.45` tương đương `12.45%`). Khớp chính xác kèm dấu. |
| 3 | **`list`** | 193 | 6.43% | Mảng có thứ tự gồm các chuỗi hoặc số. So khớp chính xác theo từng vị trí (Position-by-position exact match). |
| 4 | **`date`** | 145 | 4.83% | Chuỗi thời gian chuẩn ISO (`YYYY-MM-DD` hoặc `YYYY-MM`). So khớp chính xác chuỗi. |
| 5 | **`string`** | 88 | 2.93% | Tên sản phẩm, tên khách hàng. Chuẩn hóa NFC, chữ thường, bỏ ký tự đặc biệt, so khớp với đáp án hoặc phần tử trong `alias`. |
| 6 | **`unanswerable`** | 70 | 2.33% | Câu hỏi thiếu dữ liệu để trả lời (`answer: null`). Nhị phân đúng/sai (+1 nếu gán unanswerable, -1 nếu đoán bừa). |
| 7 | **`boolean`** | 23 | 0.77% | Giá trị logic (`true` hoặc `false`). So khớp chính xác boolean. |
| 8 | **`table`** | 19 | 0.63% | Bảng tóm tắt JSON `{"columns": [...], "rows": [...]}`. So khớp tên cột chuẩn hóa, hàng so khớp theo tập hợp (unordered). |
| | **Tổng cộng** | **3,000** | **100.00%** | |

### Trực Quan Hóa Tỷ Trọng Phân Bổ Kiểu Câu Trả Lời

```text
number         | ███████████████████████████████  1884 (62.80%)
percent        | ██████████                        578 (19.27%)
list           | ███                               193 ( 6.43%)
date           | ██                                145 ( 4.83%)
string         | █                                  88 ( 2.93%)
unanswerable   | █                                  70 ( 2.33%)
boolean        |                                    23 ( 0.77%)
table          |                                    19 ( 0.63%)
```

> **Nhận xét chính**: Hai dạng câu hỏi tính toán định lượng (`number` và `percent`) chiếm tới **82.07%** toàn bộ tập dữ liệu. Điều này khẳng định năng lực cốt lõi của agent phải tập trung vào việc trích xuất và tính toán số liệu chính xác qua Text-to-SQL / Code Generation.

## 3. Phân Tích Thống Kê Chi Tiết Từng Kiểu Dữ Liệu

### 3.1. Nhóm `number` (1,884 câu - 62.80%)
- **Toàn vẹn số nguyên**: 100% các giá trị `number` trong ground truth đều là số nguyên (`all(is_integer) == True`), không có số thập phân lẻ.
- **Giá trị nhỏ nhất**: `-62,275,893` VND
- **Giá trị lớn nhất**: `8,843,326,100` VND
- **Giá trị trung bình**: `166,278,895.33` VND
- **Giá trị trung vị (Median)**: `548,766`
- **Phân vị 25% (Q1)**: `171`
- **Phân vị 75% (Q3)**: `49,989,300`
- **Trường hợp đặc biệt (Số âm)**: Có đúng **2** câu có giá trị âm:
  - `q_21b181e1a5f6` (biz_105): *"Xem giúp trừ hết chi phí rồi thì tháng 1/2025 còn lãi ròng bao nhiêu?"* -> Đáp án: `-62,275,893` (lỗ ròng sau khi trừ chi phí vận hành).
  - `q_7bb4d7c07153` (biz_124): *"Tháng 3/2025, số nhập trừ số bán của Telfast HD 180mg là bao nhiêu viên?"* -> Đáp án: `-28` (số lượng bán vượt số lượng nhập trong kỳ).
- **Trường hợp bằng 0**: Có **2** câu (doanh thu bằng 0 hoặc số lượng bằng 0 do không phát sinh giao dịch).

### 3.2. Nhóm `percent` (578 câu - 19.27%)
- **Quy cách biểu diễn**: Toàn bộ giá trị phần trăm được làm tròn đúng 2 chữ số thập phân theo Problem Contract.
- **Giá trị nhỏ nhất**: `-82.86%`
- **Giá trị lớn nhất**: `391.30%`
- **Trung bình**: `7.57%`
- **Trung vị**: `2.63%`
- **Phân vị 25% - 75%**: `0.65%` đến `11.89%`
- **Số câu mang giá trị âm (< 0%)**: **136** câu (23.5%), biểu thị mức sụt giảm doanh thu, sản lượng hoặc giá trị đơn hàng so với kỳ đối chiếu.
- **Số câu tăng trưởng > 100%**: **8** câu (1.4%), biểu thị mức tăng trưởng đột biến.
- **Chủ đề chính**: Tỷ lệ đơn hàng bị hủy, tỷ trọng đóng góp doanh thu của ngành hàng/sản phẩm/kênh thanh toán, tỷ lệ tăng trưởng doanh thu so với tháng trước hoặc cùng kỳ.

### 3.3. Nhóm `list` (193 câu - 6.43%)
Danh sách có thứ tự gồm chuỗi hoặc số:
- **Danh sách chuỗi (`list[str]`)**: **106** câu (54.9%). Thường là danh sách Top sản phẩm bán chạy nhất hoặc Top khách hàng. **100% các câu hỏi danh sách chuỗi đều có trường `alias`** chứa mã định danh (mã sản phẩm `SPxxxx` hoặc mã khách hàng `KHxxxx`).
- **Danh sách số nguyên (`list[int]`)**: **87** câu (45.1%). Thường là chuỗi doanh thu các tháng kế tiếp nhau (VD: `[287435200, 346554700, 309693800]`) hoặc các cặp số [hộp chẵn, cái lẻ], [tiền nợ thêm, tiền trả được]. **Không có `alias`** (`alias: []`).
- **Phân bổ theo độ dài danh sách (`len`)**:
  - Danh sách `2` phần tử: **60** câu (31.1%)
  - Danh sách `3` phần tử: **82** câu (42.5%)
  - Danh sách `5` phần tử: **50** câu (25.9%)
  - Danh sách `11` phần tử: **1** câu (0.5%)
  - *Lưu ý về danh sách 11 phần tử*: Duy nhất câu `q_fa4465b0cfa7` (biz_123) yêu cầu liệt kê tất cả các sản phẩm hết hạn trong vòng 120 ngày còn tồn kho.

### 3.4. Nhóm `date` (145 câu - 4.83%)
- **Phân bổ định dạng ngày**:
  - Chuỗi ngày đầy đủ (`YYYY-MM-DD`): **129** câu (89.0%). Thường gặp: *"ngày nào doanh thu cao nhất tháng..."*.
  - Chuỗi tháng (`YYYY-MM`): **16** câu (11.0%). Thường gặp: *"trong các tháng X, Y, Z, tháng nào có doanh thu cao nhất..."*.
- **Phân bổ theo năm**:
  - Năm `2025`: **91** câu
  - Năm `2026`: **49** câu
  - Năm `2028`: **3** câu
  - Năm `2029`: **2** câu
  - *Phát hiện thú vị*: Các mốc năm tương lai `2028` (3 câu) và `2029` (2 câu) đến từ các câu hỏi truy vấn **hạn sử dụng lô thuốc** (`lô gần hết hạn nhất`) tại dữ liệu nhà thuốc (`biz_123`, `biz_124`).

### 3.5. Nhóm `string` (88 câu - 2.93%)
- **Bản chất**: Trả về 1 tên mặt hàng bán chạy nhất/doanh thu cao nhất, hoặc 1 tên khách hàng chi tiêu nhiều nhất/mua nhiều đơn nhất.
- **Phân bổ `alias`**: Có **42/88** câu (47.7%) có `alias` kèm theo mã hàng hoặc tên không dấu.

### 3.6. Nhóm `unanswerable` (70 câu - 2.33%)
- **Bản chất**: Câu hỏi mà cơ sở dữ liệu không đủ thông tin hoặc không thể suy luận.
- **Giá trị `answer`**: Bắt buộc là `null`.
- **5 nguyên nhân chính gây ra `unanswerable` trong dataset**:
  1. **Thiếu dữ liệu chi phí/giá vốn**: Hỏi lợi nhuận/lãi nhưng cửa hàng chỉ có sổ ghi bán hàng, không có dữ liệu nhập hàng.
  2. **Thiếu trường thuộc tính thực thể**: Hỏi địa chỉ nhà khách hàng (đường nào) nhưng bảng khách hàng chỉ lưu tên và SĐT.
  3. **Yêu cầu định tính mang tính chủ quan**: Hỏi *"ai là người lành nghề nhất trong số nhân viên"*.
  4. **Kỳ truy vấn nằm ngoài khoảng thời gian ghi nhận**: Hỏi doanh thu tháng liền trước nhưng đó là tháng bắt đầu mở tiệm.
  5. **Dữ liệu không lưu đơn vị đóng gói chi tiết**: Hỏi số cái lẻ nhưng dữ liệu chỉ ghi tổng trọng lượng.

### 3.7. Nhóm `boolean` (23 câu - 0.77%)
- **Tỷ lệ**: `False` chiếm **13** câu (56.52%), `True` chiếm **10** câu (43.48%).
- **Khuôn mẫu câu hỏi đặc trưng (100%)**: Toàn bộ 23 câu hỏi đều kiểm tra giả thuyết doanh thu tăng liên tục qua 3 tháng kề nhau (*"Từ tháng A qua tháng B rồi tháng C, doanh thu có tăng liên tục không?"*).

### 3.8. Nhóm `table` (19 câu - 0.63%)
- **Cấu trúc cột đồng nhất (100%)**: Toàn bộ 19 câu bảng đều trả về đúng 2 cột: `{"columns": ["khach_hang", "so_tien_no"], "rows": [...]}`.
- **Số dòng trong bảng**:
  - Bảng `3` dòng: **12** câu (tương ứng Top 3 khách có công nợ lớn nhất)
  - Bảng `5` dòng: **7** câu (tương ứng Top 5 khách có công nợ lớn nhất)
- **Bí danh (Alias)**: 100% (19/19) câu có mảng 2 chiều chứa mã khách hàng `KHxxxx` cho từng dòng tương ứng.

## 4. Phân Tích Cơ Chế `alias` Theo Kiểu Dữ Liệu

| Kiểu dữ liệu (`type`) | Tổng số câu | Số câu có `alias` | Tỷ lệ (%) | Cấu trúc dữ liệu trong trường `alias` |
| :--- | :---: | :---: | :---: | :--- |
| **`list`** | 193 | 106 | 54.9% | Mảng 2 chiều chứa mã sản phẩm/khách hàng: `[["SP0003"], ["SP0017"]]` |
| **`string`** | 88 | 42 | 47.7% | Mảng 1 chiều chứa mã hoặc tên gọi khác: `["SP0001"]` |
| **`table`** | 19 | 19 | 100.0% | Mảng 2 chiều chứa mã khách hàng cho từng dòng: `[["KH0124"], ["KH0233"]]` |
| **`number`** | 1,884 | 0 | 0.0% | Luôn là mảng rỗng `[]` |
| **`percent`** | 578 | 0 | 0.0% | Luôn là mảng rỗng `[]` |
| **`date`** | 145 | 0 | 0.0% | Luôn là mảng rỗng `[]` |
| **`boolean`** | 23 | 0 | 0.0% | Luôn là mảng rỗng `[]` |
| **`unanswerable`** | 70 | 0 | 0.0% | Luôn là mảng rỗng `[]` |

## 5. Bảng Phân Bổ `type` Chi Tiết Theo 30 Doanh Nghiệp

| Mã doanh nghiệp | `number` | `percent` | `string` | `list` | `unanswerable` | `date` | `table` | `boolean` | Tổng câu hỏi |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`biz_101`** | 34 | 0 | 2 | 0 | 0 | 4 | 0 | 0 | **40** |
| **`biz_102`** | 80 | 20 | 1 | 13 | 0 | 5 | 0 | 0 | **119** |
| **`biz_103`** | 59 | 31 | 2 | 7 | 12 | 5 | 0 | 3 | **119** |
| **`biz_104`** | 83 | 22 | 3 | 6 | 0 | 5 | 0 | 0 | **119** |
| **`biz_105`** | 67 | 25 | 5 | 12 | 5 | 3 | 0 | 2 | **119** |
| **`biz_106`** | 72 | 19 | 3 | 11 | 7 | 1 | 5 | 1 | **119** |
| **`biz_107`** | 35 | 0 | 1 | 0 | 0 | 4 | 0 | 0 | **40** |
| **`biz_108`** | 72 | 33 | 4 | 4 | 0 | 6 | 0 | 0 | **119** |
| **`biz_109`** | 75 | 18 | 3 | 13 | 2 | 3 | 2 | 2 | **118** |
| **`biz_110`** | 35 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | **40** |
| **`biz_111`** | 72 | 29 | 0 | 9 | 0 | 6 | 2 | 0 | **118** |
| **`biz_112`** | 73 | 25 | 0 | 5 | 12 | 1 | 0 | 2 | **118** |
| **`biz_113`** | 35 | 0 | 3 | 0 | 0 | 2 | 0 | 0 | **40** |
| **`biz_114`** | 31 | 0 | 3 | 0 | 0 | 6 | 0 | 0 | **40** |
| **`biz_115`** | 82 | 23 | 1 | 3 | 0 | 9 | 0 | 0 | **118** |
| **`biz_116`** | 80 | 22 | 0 | 10 | 0 | 6 | 0 | 0 | **118** |
| **`biz_117`** | 67 | 24 | 5 | 11 | 3 | 6 | 0 | 2 | **118** |
| **`biz_118`** | 62 | 32 | 7 | 5 | 6 | 6 | 0 | 0 | **118** |
| **`biz_119`** | 81 | 24 | 3 | 5 | 0 | 5 | 0 | 0 | **118** |
| **`biz_120`** | 82 | 25 | 2 | 6 | 0 | 3 | 0 | 0 | **118** |
| **`biz_121`** | 57 | 31 | 4 | 11 | 7 | 5 | 0 | 3 | **118** |
| **`biz_122`** | 59 | 38 | 2 | 8 | 4 | 5 | 0 | 2 | **118** |
| **`biz_123`** | 68 | 16 | 11 | 13 | 2 | 4 | 3 | 1 | **118** |
| **`biz_124`** | 59 | 25 | 9 | 11 | 2 | 6 | 3 | 3 | **118** |
| **`biz_125`** | 35 | 0 | 2 | 0 | 0 | 3 | 0 | 0 | **40** |
| **`biz_126`** | 30 | 0 | 4 | 0 | 0 | 6 | 0 | 0 | **40** |
| **`biz_127`** | 73 | 23 | 2 | 14 | 0 | 4 | 2 | 0 | **118** |
| **`biz_128`** | 87 | 22 | 3 | 2 | 0 | 4 | 0 | 0 | **118** |
| **`biz_129`** | 75 | 22 | 2 | 8 | 0 | 9 | 2 | 0 | **118** |
| **`biz_130`** | 64 | 29 | 1 | 6 | 8 | 8 | 0 | 2 | **118** |
| **Tổng cộng** | **1884** | **578** | **88** | **193** | **70** | **145** | **19** | **23** | **3000** |

### Các Phát Hiện Quan Trọng Về Doanh Nghiệp
1. **Hai tầng cấu trúc dữ liệu doanh nghiệp rõ rệt**:
   - **Tầng 1 - Cửa hàng đơn giản (40 câu/biz)**: Gồm **7 doanh nghiệp** (`biz_101`, `biz_107`, `biz_110`, `biz_113`, `biz_114`, `biz_125`, `biz_126`). Toàn bộ chỉ dùng 1 file CSV phẳng hoặc 1 sheet Excel đơn giản. Tập câu hỏi chỉ gồm 3 loại: `number`, `string`, `date`. Tuyệt đối không có các loại câu hỏi phức tạp.
   - **Tầng 2 - Doanh nghiệp phức tạp (118-119 câu/biz)**: Gồm **23 doanh nghiệp** còn lại, sở hữu dữ liệu bán hàng đa bảng, danh mục hàng hóa, tồn kho, công nợ, đối tác. Chứa đầy đủ cả 8 loại câu hỏi.
2. **Sự tập trung của nhãn `unanswerable`**:
   - Chỉ có **12/30 doanh nghiệp** xuất hiện câu hỏi `unanswerable`, trong đó cao nhất là `biz_112` (12 câu), `biz_103` (12 câu), `biz_130` (8 câu), `biz_121` (7 câu), `biz_106` (7 câu).
   - 18 doanh nghiệp còn lại có 0 câu hỏi unanswerable.
3. **Sự xuất hiện của câu hỏi công nợ (`table`)**:
   - Chỉ có **7 doanh nghiệp** có theo dõi công nợ khách hàng xuất hiện loại câu hỏi `table`: `biz_106` (5), `biz_123` (3), `biz_124` (3), `biz_127` (2), `biz_109` (2), `biz_129` (2), `biz_111` (2).

## 6. Bài Học Kinh Nghiệm & Đề Xuất Kỹ Thuật Cho DataMate Agent

1. **Chiến Lược Định Tuyến Kiểu Đầu Ra (Type-Routing Strategy)**:
   - Mô hình có thể áp dụng bộ phân loại regex/keyword hoặc few-shot prompt nhẹ để xác định trước `target_type` của câu hỏi trước khi sinh mã Text-to-SQL / Text-to-Python.
   - Đảm bảo post-processing ép kiểu chính xác theo đúng yêu cầu Problem Contract (làm tròn float 2 số với `percent`, ép `int` với `number`, format chuỗi ISO với `date`).
2. **Xử Lý An Toàn Điểm Số (Penalized Accuracy & Abstain Calibration)**:
   - Metric chấm điểm: $+1$ (Đúng), $0$ (Abstain/Bỏ cuộc), $-1$ (Sai).
   - Điểm kỳ vọng: $\mathbb{E}[s] = 2 \times P(\text{correct}) - 1$.
   - Do đó, nếu Text-to-SQL / Text-to-Python thực thi bị lỗi runtime, kết quả truy vấn rỗng không rõ ràng, hoặc độ tự tin dưới 50%, agent nên chủ động trả về `{"type": "abstain"}` để bảo toàn 0 điểm, tránh bị trừ -1 điểm.
3. **Phát Hiện Câu Hỏi Thiếu Dữ Liệu (`unanswerable`)**:
   - Nếu câu hỏi đòi hỏi thông tin không tồn tại trong schema (như hỏi lãi ròng khi không có cột giá vốn/chi phí, hỏi địa chỉ khách hàng khi bảng khách hàng không có cột địa chỉ), agent cần chủ động xuất nhãn `unanswerable` để giành trọn +1 điểm.
4. **Tận Dụng Tối Đa Bí Danh (`alias`)**:
   - Đối với các câu hỏi `string`, `list`, `table`, ground truth chấp nhận cả tên sản phẩm lẫn mã sản phẩm (`SPxxxx`), mã khách hàng (`KHxxxx`). Việc truy vấn lấy kèm mã định danh sẽ tăng đáng kể xác suất so khớp chính xác.
