# SentimentIQ — Hệ thống Phân tích Cảm xúc & Gợi ý Sản phẩm (E-commerce)

> **Môn học/Chủ đề:** Khai phá Dữ liệu Đa phương tiện trong Thương mại Điện tử
> **Nguồn dữ liệu:** Shopee & Tiki (Ngôn ngữ: Tiếng Việt)

SentimentIQ là một hệ thống toàn diện ứng dụng Machine Learning và NLP để phân tích bình luận của người dùng trên các sàn thương mại điện tử, từ đó phân lớp cảm xúc, rút trích chủ đề và đưa ra các chiến lược gợi ý sản phẩm phù hợp. Hệ thống bao gồm backend API mạnh mẽ, một dashboard phân tích, một giao diện client mua sắm, và một trợ lý ảo 3D tích hợp AI (Gemini).

---

## 🗂️ Cấu trúc Dự án

```text
ecom_rcm_1/
├── datas/                          # Chứa dữ liệu thô, dữ liệu đã xử lý và models
├── docs/                           # Tài liệu kỹ thuật & API
├── notebooks/                      # Các bước phân tích & huấn luyện (cho báo cáo)
├── src/                            # Source code chính của ứng dụng
│   ├── api/                        # FastAPI server (routes, services, schemas)
│   ├── data/                       # Module load & xử lý danh mục sản phẩm
│   ├── models/                     # Các module Recommender, CF
│   └── utils/                      # Tiện ích tiền xử lý văn bản tiếng Việt
├── web/                            # Frontend (Vanilla JS + HTML/CSS)
│   ├── index.html                  # Dashboard quản trị
│   ├── client.html                 # Giao diện người dùng mua sắm
│   ├── chatbot.html                # Giao diện Chatbot 3D (Three.js/VRM)
│   ├── css/                        # Stylesheets
│   └── js/                         # JavaScript logic (chứa shared.js)
├── .env.example                    # File mẫu cấu hình biến môi trường
├── requirements.txt                # Danh sách thư viện Python
└── README.md                       # Tài liệu tổng quan này
```

---

## ⚙️ Hướng dẫn Cài đặt & Chạy ứng dụng

### 1. Cài đặt Backend (Python)

Yêu cầu: Python 3.10+

```bash
# Tạo và kích hoạt virtual environment
python -m venv .venv
.venv\Scripts\activate     # Trên Windows
# source .venv/bin/activate  # Trên Linux/Mac

# Cài đặt thư viện
pip install -r requirements.txt

# Tạo file .env từ template (cần điền GEMINI_API_KEY nếu muốn dùng chatbot AI)
cp .env.example .env
```

### 2. Khởi chạy Dịch vụ

**Khởi chạy API Server:**
```bash
# Chạy server FastAPI trên cổng 8000
uvicorn src.api.main:app --reload --port 8000
```
API Documentation (Swagger UI) sẽ có sẵn tại: [http://localhost:8000/docs](http://localhost:8000/docs)

**Mở Frontend Web:**
Bạn có thể mở trực tiếp các file HTML trong thư mục `web/` bằng trình duyệt, hoặc chạy một local server để tránh lỗi CORS đối với mô hình 3D:
```bash
python -m http.server 3000 --directory web/
```
Truy cập Dashboard: [http://localhost:3000/](http://localhost:3000/)

---

## 🧩 Các Tính Năng Cốt Lõi

1. **Phân tích Cảm xúc (Sentiment Analysis):**
   - Sử dụng Naive Bayes để phân loại bình luận tiếng Việt (Tích cực / Tiêu cực).
   - Module tiền xử lý hỗ trợ chuẩn hóa Teencode, tách từ (word segmentation) bằng Underthesea.

2. **Hệ thống Gợi ý (Recommender System):**
   - **Content-based Filtering:** Gợi ý sản phẩm dựa trên TF-IDF và Cosine Similarity của tên & mô tả.
   - **Collaborative Filtering:** Gợi ý dựa trên ma trận người dùng - sản phẩm (User-User CF).

3. **Phân cụm Chủ đề (Topic Clustering):**
   - Sử dụng GMM (Gaussian Mixture Model) để nhóm các bình luận thành các chủ đề chính yếu nhằm trích xuất thông tin insight.

4. **Trợ lý ảo 3D (AI Chatbot):**
   - Tích hợp mô hình ngôn ngữ lớn (Google Gemini 2.0 Flash) kết hợp với Retrieval-Augmented Generation (RAG) nội bộ.
   - Hiển thị nhân vật 3D (.vrm) sử dụng `three-vrm`, có khả năng thay đổi cử chỉ tương ứng với phản hồi.

---

## 🔄 Pipeline Xử Lý Dữ Liệu

Quá trình huấn luyện mô hình được chia thành các bước rõ ràng trong thư mục `notebooks/`:
- `01_crawl_and_prepare_data.ipynb`: Thu thập & làm sạch dữ liệu ban đầu.
- `02_nlp_preprocessing.ipynb`: Pipeline xử lý tiếng Việt chuyên sâu.
- `03_clustering_classification.ipynb`: Huấn luyện mô hình Phân lớp (Naive Bayes) và Phân cụm (GMM).
- `04_association_rules_recommendation.ipynb`: Xây dựng ma trận gợi ý và lưu mô hình.

---

## 📊 Chỉ Số Hiệu Suất Kỳ Vọng

| Tác Vụ | Thuật Toán | Metric Đánh Giá | Mục Tiêu |
|--------|------------|-----------------|-----------|
| Phân loại cảm xúc | Naive Bayes | F1-score | ≥ 82% |
| Phân cụm nội dung | GMM | Silhouette Score | ≥ 0.35 |
| Khai phá luật | Apriori | Lift | ≥ 1.2 |
| Gợi ý sản phẩm | TF-IDF / CF | Precision@10 | ≥ 60% |

---

## 🤖 Bản quyền & Công cụ
- Nền tảng: Python, FastAPI, Scikit-Learn.
- Web 3D: Three.js, React Three Fiber, Pixiv VRM.
- AI Integration: Google Generative AI (Gemini).
