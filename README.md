# Phân tích Cảm xúc Bình luận Sản phẩm & Hệ thống Gợi ý

> **Chủ đề:** Khai phá Dữ liệu Đa phương tiện trong Thương mại Điện tử  
> **Nguồn dữ liệu:** Shopee & Tiki (Vietnamese)

---

## 🗂️ Cấu trúc dự án

```
ecom_rcm_1/
├── datas/
│   ├── sentiment_dataset/          # Dataset bình luận (raw)
│   └── recommend_dataset/          # Dataset sản phẩm
├── docs/                           # Tài liệu mô tả & yêu cầu
├── notebooks/
│   ├── 01_crawl_and_prepare_data.ipynb     # Phase 1: Thu thập & chuẩn bị dữ liệu
│   ├── 02_nlp_preprocessing.ipynb          # Phase 2: Tiền xử lý NLP
│   ├── 03_clustering_classification.ipynb  # Phase 3: Phân cụm & Phân lớp
│   └── 04_association_rules_recommendation.ipynb  # Phase 4: Luật kết hợp & Gợi ý
├── samples/                        # Scripts crawl & phân tích mẫu
├── src/
│   ├── data/                       # Module xử lý dữ liệu
│   ├── models/                     # Module mô hình ML
│   ├── api/                        # FastAPI backend
│   └── utils/                      # Tiện ích dùng chung
├── web/
│   ├── index.html                  # Dashboard chính
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt
└── README.md
```

---

## ⚙️ Cài đặt

```bash
# 1. Kích hoạt virtual environment
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/Mac

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Chạy notebook (chọn 1 trong 4 file)
jupyter notebook notebooks/

# 4. Chạy API server
uvicorn src.api.main:app --reload --port 8000

# 5. Mở Dashboard
# Mở web/index.html trong trình duyệt, hoặc:
python -m http.server 3000 --directory web/
```

---

## 🔄 Pipeline tổng quan

```
Thu thập dữ liệu (Shopee/Tiki)
  └─► Tiền xử lý NLP (làm sạch, tokenize, POS, TF-IDF)
        ├─► Phân lớp cảm xúc (Naive Bayes)
        ├─► Phân cụm chủ đề (EM / GMM)
        ├─► Luật kết hợp (Apriori/FP-Growth) ← bình luận tiêu cực
        └─► Hệ thống Gợi ý (Content-based + Cosine Similarity)
              └─► FastAPI Backend ─► Web Dashboard
```

---

## 📊 Kết quả mục tiêu

| Mô hình | Metric | Mục tiêu |
|---------|--------|-----------|
| Naive Bayes | F1-score | ≥ 82% |
| GMM | Silhouette Score | ≥ 0.35 |
| Apriori | Lift | ≥ 1.2 |
| Recommender | Precision@10 | ≥ 60% |

---

## 🤖 AI hỗ trợ

Dự án sử dụng **Google Gemini AI** để hỗ trợ:
- Sinh code boilerplate và module
- Review code theo chuẩn PEP 8
- Phân tích kết quả và đề xuất cải thiện
- Sinh tài liệu và comment tiếng Việt
