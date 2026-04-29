    **Vai trò:** Bạn là một chuyên gia Khoa học Dữ liệu (Data Scientist) và Quản lý Dự án Công nghệ (Technical Project Manager) có nhiều năm kinh nghiệm trong lĩnh vực Thương mại điện tử (E-commerce).

**Nhiệm vụ:** Hãy giúp tôi lập một bản kế hoạch dự án (Project Plan) chi tiết, chuẩn xác và mang tính thực thi cao cho dự án **"Phân tích cảm xúc bình luận sản phẩm"**.

**Thông tin và yêu cầu kỹ thuật của dự án:**

1. **Lĩnh vực:** Thương mại điện tử.
2. **Nguồn dữ liệu:** Từ những nguồn trong folder datas & crawl data từ shopee dựa vào repository trong samples/shopee_reviews_crawler.
3. **Tiền xử lý ngôn ngữ tự nhiên (NLP):** Làm sạch văn bản, loại bỏ stopwords, gán nhãn từ loại (POS tagging), chuẩn hóa từ viết tắt/teencode.
4. **Phân cụm (Clustering):** Sử dụng thuật toán Expectation-Maximization (EM) để nhóm các bình luận theo chủ đề (khen hoặc chê).
5. **Phân lớp (Classification):** Sử dụng thuật toán Naive Bayes để phân loại bình luận tích cực và tiêu cực.
6. **Luật kết hợp (Association Rules):** Ứng dụng thuật toán (ví dụ: Apriori/FP-Growth) để tìm các cặp từ/cụm từ thường xuyên xuất hiện cùng nhau trong các bình luận tiêu cực (nhằm rút ra insight về lỗi sản phẩm/dịch vụ).
7. **Hệ thống gợi ý (Recommendation System):** Xây dựng hệ thống đề xuất sản phẩm dựa trên các bình luận tích cực từ người dùng.

**Yêu cầu đầu ra của bản kế hoạch:** Hãy cấu trúc bản kế hoạch theo các phần sau:

* **Phần 1: Tổng quan kiến trúc hệ thống (Pipeline):** Mô tả luồng đi của dữ liệu từ lúc thu thập, xử lý, đưa vào các mô hình (EM, Naive Bayes, Association Rules) cho đến hệ thống đề xuất cuối cùng.
* **Phần 2: Đề xuất công nghệ (Tech Stack):** Gợi ý các thư viện, ngôn ngữ lập trình (Python) và công cụ phù hợp nhất cho từng giai đoạn. Lưu ý sử dụng các thư viện, framework hiện đại, phù hợp với dự án.
* **Phần 3: Kế hoạch triển khai chi tiết (Timeline / Sprints):** Chia dự án thành các giai đoạn (Phase) cụ thể. Mỗi Phase cần liệt kê rõ: Nhiệm vụ chính, Đầu ra dự kiến (Deliverables).
* **Phần 4: Tiêu chí đánh giá (Evaluation Metrics):** Đề xuất các độ đo cụ thể cho từng mô hình (Ví dụ: Accuracy, F1-score cho Naive Bayes; Silhouette score cho EM; Support/Confidence cho Luật kết hợp).
* **Phần 5: Quản trị rủi ro:** Chỉ ra những khó khăn tiềm ẩn (đặc biệt với dữ liệu tiếng Việt của Shopee nếu có) và đề xuất phương án giải quyết (Plan B).
* **Phần 6: Công cụ AI hỗ trợ:** Sử dụng Google Generative AI để hỗ trợ phát triển dự án. Hãy mô tả chi tiết cách AI đã được áp dụng như thế nào để tăng năng suất và cải thiện chất lượng công việc.

---

### ** Yêu cầu code đầu ra: ** 

* Code cần được viêt chủ yếu bằng Python, sử dụng các thư viện hiện đại và phù hợp với dự án.
* Code cần được tổ chức thành các module, class và function rõ ràng.
* Code cần được viết theo phong cách PEP 8.
* Code cần được viết bằng tiếng Việt và có comment giải thích rõ ràng.
* Cần có những file .ipynb để mô tả các bước xử lý. Các phần cần có đầu ra file .ipynb là: crawl data và chuẩn bị dữ liệu(File 1); tiền xử lý dữ liệu và xử lý ngôn ngữ tự nhiên(File 2); Phân cụm, Phân lớp nhằm huấn luyện mô hình nhận định đánh giá từ người dùng(File 3); Luật kết hợp, Hệ thống gợi ý sản phẩm(File 4).

---
Hãy trình bày bằng tiếng Việt, sử dụng Markdown, bảng biểu rõ ràng, mạch lạc và giữ phong cách chuyên nghiệp.
