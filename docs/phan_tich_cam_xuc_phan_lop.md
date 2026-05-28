# CHƯƠNG: PHÂN TÍCH CẢM XÚC VÀ PHÂN LỚP DỮ LIỆU

## 1. Tiền xử lý văn bản
Dữ liệu bình luận được tổng hợp từ các nguồn trong `datas/sentiment_dataset` (Tiki, Shopee, tập tổng hợp). Sau khi gộp dữ liệu vào `datas/processed/merged_sentiment.csv`, pipeline tiền xử lý được áp dụng để chuẩn hóa tiếng Việt và giảm nhiễu:

1. **Làm sạch**: loại bỏ HTML, URL, email, emoji, ký tự đặc biệt.
2. **Chuẩn hóa teencode/viết tắt**: ví dụ “sp” → “sản phẩm”, “ko” → “không”.
3. **Tách từ tiếng Việt**: dùng `underthesea` khi khả dụng để giữ cụm từ có nghĩa.
4. **Loại stopwords**: bỏ các từ ít mang ý nghĩa phân loại.

Kết quả được lưu tại `datas/processed/processed_reviews.csv` với các cột chính:

- `review_text`: bình luận gốc.
- `processed_text`: văn bản đã làm sạch.
- `label`: nhãn cảm xúc (1 = tích cực, 0 = tiêu cực).
- `source`: nguồn dữ liệu.

## 2. Trích xuất đặc trưng
Dữ liệu văn bản được chuyển sang vector số bằng TF-IDF với cấu hình từ Notebook 02:

- N-gram: 1–3
- `max_features`: 50,000
- `min_df`: 3
- `max_df`: 0.95
- `sublinear_tf`: True

Sau khi vector hóa, dữ liệu được chia train/test theo tỷ lệ 80/20 (stratified) để giữ phân bố nhãn ổn định giữa các tập. Các file đầu ra gồm:

- `datas/processed/tfidf_vectorizer.pkl`
- `datas/processed/X_train.npz`, `X_test.npz`
- `datas/processed/y_train.npy`, `y_test.npy`

## 3. Huấn luyện mô hình
Mô hình phân lớp cảm xúc sử dụng Naive Bayes, với cấu hình chính:

- `ComplementNB(alpha=0.1)` cho dữ liệu văn bản mất cân bằng nhẹ.
- Thử nghiệm thêm các biến thể `MultinomialNB` và `ComplementNB` với alpha khác nhau để so sánh.

Mô hình được lưu tại `datas/models/naive_bayes.pkl` để phục vụ API hoặc các bước phân tích tiếp theo.

## 4. Đánh giá mô hình
Mô hình được đánh giá bằng các thước đo tiêu chuẩn cho bài toán phân lớp văn bản:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion Matrix
- Cross-validation 5-fold (F1-score)

Biểu đồ nhầm lẫn được lưu tại `datas/processed/confusion_matrix.png` để quan sát trực quan lỗi phân loại.

> Ghi chú: Các chỉ số cụ thể phụ thuộc vào lần chạy và cấu hình môi trường. Có thể chạy lại Notebook 03 để cập nhật số liệu mới nhất.

## 5. Kết quả phân tích
Thống kê từ `datas/processed/processed_reviews.csv`:

### 5.1. Phân bố nhãn cảm xúc

| Nhãn | Ý nghĩa | Số lượng | Tỷ lệ (%) |
| --- | --- | ---: | ---: |
| 1 | Tích cực | 19,353 | 61.5 |
| 0 | Tiêu cực | 12,116 | 38.5 |
| **Tổng** |  | **31,469** | **100** |

### 5.2. Độ dài bình luận (token)

| Nhãn | Độ dài trung bình | Min | Max |
| --- | ---: | ---: | ---: |
| Tích cực | 4.95 | 1 | 43 |
| Tiêu cực | 3.22 | 1 | 46 |

**Nhận xét chính:**

- Dữ liệu đủ lớn và đa nguồn để huấn luyện mô hình baseline.
- Nhãn tích cực chiếm ưu thế (61.5%), nhưng chưa gây mất cân bằng nghiêm trọng.
- Bình luận tích cực thường dài hơn và giàu mô tả; bình luận tiêu cực ngắn, trực diện.
- Pipeline tiền xử lý giúp giảm nhiễu tiếng Việt và nâng chất lượng đặc trưng TF-IDF.
