# PHÂN TÍCH CẢM XÚC BÌNH LUẬN SẢN PHẨM & HỆ THỐNG GỢI Ý

## 1. Giới thiệu

Trong lĩnh vực thương mại điện tử, đánh giá của khách hàng đóng vai trò quan trọng trong việc cải thiện chất lượng sản phẩm và trải nghiệm người dùng.
Dự án này tập trung vào việc phân tích cảm xúc của các bình luận sản phẩm nhằm:

* Hiểu được cảm nhận của khách hàng
* Xác định các vấn đề thường gặp
* Hỗ trợ hệ thống gợi ý sản phẩm hiệu quả

---

## 2. Mục tiêu

* Phân loại bình luận thành tích cực / tiêu cực
* Phân cụm các bình luận theo các chủ đề (VD: giao hàng, chất lượng sản phẩm, giá cả,...) 
* Khai phá các luật kết hợp từ các bình luận tiêu cực
* Xây dựng hệ thống gợi ý sản phẩm dựa trên phản hồi tích cực

---

## 3. Bộ dữ liệu
* Train & test đánh giá comment: từ các dataset trong folder: datas/sentiment_dataset
* Train & test recommend sản phẩm: từ các dataset trong folder: datas/recommend_dataset
* Dataset về đánh giá comment: có thể xem xét chạy script trong samples/shopee_reviews_crawler để crawl data.
* Dataset về danh sách các sản phẩm nhằm mở rộng cho recommendation: 

## 4. Phương pháp

### 4.1 Tiền xử lý dữ liệu

* Làm sạch văn bản (loại bỏ ký tự đặc biệt, HTML, emoji không cần thiết)
* Chuẩn hóa từ viết tắt (ví dụ: "sp" → "sản phẩm", "ko" → "không")
* Tách từ tiếng Việt (tokenization)
* Loại bỏ stopwords
* Gán nhãn từ loại (POS tagging)
* Xử lý chuẩn hoá riêng từng bộ dataset & gộp lại làm duy nhất 1 bộ 

---

### 4.2 Trích xuất đặc trưng

* TF-IDF vectorization
* N-gram (1–3)

---

### 4.3 Phân loại cảm xúc

* **Baseline:** Naive Bayes
* **Nâng cao:** Fine-tune PhoBERT

---

### 4.4 Phân cụm bình luận

* **Baseline:** EM (Gaussian Mixture Model)
* **Nâng cao:** BERTopic

Mục tiêu:

* Nhóm các bình luận theo chủ đề như:
  * Giao hàng
  * Chất lượng sản phẩm
  * Đóng gói
  * ...

---

### 4.5 Luật kết hợp

* Áp dụng thuật toán Apriori hoặc FP-Growth
* Tìm các cặp từ thường xuất hiện trong bình luận tiêu cực

Ví dụ:

* "giao hàng chậm" → tiêu cực
* "đóng gói kém" → tiêu cực
* ...
---

### 4.6 Hệ thống gợi ý sản phẩm dựa trên bình luận tích cực

#### Cách tiếp cận cơ bản:

* Content-based filtering
* Dựa trên TF-IDF similarity

#### Cách tiếp cận nâng cao:

* Embedding (PhoBERT)
* Cosine similarity

### 4.7 Phương pháp xử lý tham khảo
* Crawl data sentiment review: /samples/shopee_reviews_crawler
* Reviews sentiment: /samples/shopee_reviews_sentiment_analysis_master

---

## 5. Kiến trúc hệ thống

### 5.1 Tổng quan

* Data Layer: dữ liệu thô và dữ liệu đã xử lý
* Processing Layer: pipeline xử lý văn bản
* Model Layer:
  * Phân loại
  * Phân cụm
  * Luật kết hợp
* Serving Layer: API (FastAPI)
* UI Layer: Dashboard (HTML + CSS + Js)

---

### 5.2 Luồng xử lý

```
Bình luận → Tiền xử lý → Vector hóa
          → Phân loại cảm xúc
          → Phân cụm chủ đề
          → Luật kết hợp
          → Gợi ý sản phẩm
          → API (FastAPI)
          → Giao diện (HTML + CSS + Js)
```

---

## 6. Đánh giá mô hình

### 6.1 Phân loại

* Accuracy
* Precision
* Recall
* F1-score


### 6.2 Phân cụm

* Topic Coherence

### 6.3 Luật kết hợp

* Support
* Confidence
* Lift

---

## 7. Công cụ AI hỗ trợ

* **Gemini AI**: Được sử dụng để hỗ trợ phát triển dự án, tăng năng suất và cải thiện chất lượng công việc.

---
  
## 8. Kết quả & Insight

* Xác định các nguyên nhân chính gây đánh giá tiêu cực
* Phân tích các yếu tố được khách hàng đánh giá cao
* Cải thiện hệ thống gợi ý sản phẩm dựa trên phản hồi thực tế

---

## 9. Hướng phát triển

* Phân tích cảm xúc theo khía cạnh (Aspect-based sentiment analysis)
* Xử lý dữ liệu thời gian thực
* Hệ thống gợi ý đa phương tiện (text + image)
* Mô hình deep learning nâng cao

---

## 10. Kết luận

Dự án cho thấy cách áp dụng các kỹ thuật Data Mining và NLP để khai thác thông tin giá trị từ dữ liệu bình luận, từ đó hỗ trợ cải thiện sản phẩm và trải nghiệm người dùng trong thương mại điện tử.

---
