# Knowledge Base - SentimentIQ

Tài liệu này cung cấp kiến thức nền tảng về các thuật toán Machine Learning và phương pháp tiếp cận được sử dụng trong dự án SentimentIQ. Thông tin này hữu ích để đưa vào báo cáo môn học.

## 1. Tiền xử lý Ngôn ngữ Tự nhiên (NLP) cho Tiếng Việt
Dữ liệu văn bản thô từ các sàn thương mại điện tử thường chứa nhiều nhiễu (emoji, URL, ký tự đặc biệt, teencode).
- **Làm sạch:** Loại bỏ HTML tags, URLs, Emojis.
- **Chuẩn hóa Teencode:** Chuyển đổi các từ viết tắt phổ biến (vd: `sp` -> `sản phẩm`, `ko` -> `không`) thành từ vựng đầy đủ.
- **Tách từ (Word Segmentation):** Sử dụng thư viện `underthesea` để gom các âm tiết tiếng Việt thành từ có nghĩa (vd: `sản phẩm` thay vì `sản` và `phẩm` riêng biệt).
- **Loại bỏ Stopwords:** Bỏ các từ xuất hiện nhiều nhưng ít mang ý nghĩa phân loại (vd: `và`, `là`, `của`).
- **TF-IDF (Term Frequency-Inverse Document Frequency):** Kỹ thuật chuyển đổi văn bản thành vector số. Nó đánh giá tầm quan trọng của một từ trong một tài liệu so với tập văn bản.

## 2. Phân loại Cảm xúc (Sentiment Classification)
Dự án sử dụng thuật toán **Naive Bayes** để phân loại bình luận thành "Tích cực" hoặc "Tiêu cực".
- **Lý thuyết:** Naive Bayes dựa trên định lý Bayes với giả định "ngây thơ" (naive) rằng các đặc trưng (ở đây là các từ) độc lập với nhau. Mặc dù giả định này hiếm khi đúng trong ngôn ngữ tự nhiên, Naive Bayes vẫn hoạt động cực kỳ hiệu quả và nhanh chóng cho phân loại văn bản.
- **Biến thể:** Thường dùng `MultinomialNB` cho dữ liệu tần suất từ/TF-IDF.

## 3. Phân cụm Chủ đề (Topic Clustering)
Dự án sử dụng **Gaussian Mixture Model (GMM)** để tự động nhóm các bình luận thành các cụm (clusters) mang chủ đề tương tự nhau (ví dụ: giao hàng, chất lượng sản phẩm, giá cả).
- **Lý thuyết:** GMM là một mô hình xác suất giả định rằng tất cả các điểm dữ liệu được sinh ra từ một hỗn hợp của một số hữu hạn các phân phối Gaussian (chuẩn) với các tham số chưa biết. Khác với K-Means (gán cứng - hard clustering), GMM cung cấp "soft clustering", tức là tính toán xác suất một điểm dữ liệu thuộc về từng cụm.
- **Giải thuật:** Sử dụng Expectation-Maximization (EM) để tối ưu hóa các tham số của các phân phối Gaussian.

## 4. Luật Kết Hợp (Association Rules)
Mục tiêu là tìm ra các quy luật mua sắm của khách hàng, ví dụ: "Khách hàng mua A thì thường mua B".
- **Lý thuyết:** Thuật toán **Apriori** (hoặc FP-Growth) tìm kiếm các tập phổ biến (frequent itemsets) trong cơ sở dữ liệu giao dịch.
- **Các độ đo chính:**
  - **Support (Độ hỗ trợ):** Tỷ lệ các giao dịch chứa cả A và B.
  - **Confidence (Độ tin cậy):** Xác suất mua B khi đã mua A.
  - **Lift (Độ nâng):** Tỷ lệ giữa Confidence(A->B) và Expected Confidence (nếu A và B hoàn toàn độc lập). Lift > 1 chứng tỏ luật có ý nghĩa.

## 5. Hệ thống Gợi ý (Recommender System)
Hệ thống kết hợp hai phương pháp:
- **Content-Based Filtering (Lọc dựa trên nội dung):** Gợi ý sản phẩm tương tự bằng cách phân tích nội dung (tên, mô tả, danh mục). Sử dụng TF-IDF để vector hóa và **Cosine Similarity** để đo khoảng cách giữa các vector. Phương pháp này giải quyết được vấn đề "Cold Start" cho sản phẩm mới.
- **Collaborative Filtering (Lọc cộng tác - User-User CF):** Khai thác hành vi người dùng. Xây dựng ma trận User-Item (người dùng - sản phẩm) với giá trị là rating. Tính độ tương đồng (Cosine) giữa các người dùng để dự đoán rating cho các sản phẩm mà người dùng chưa tương tác, từ đó đưa ra gợi ý.

## 6. Generative AI & Chatbot
Dự án sử dụng **Google Gemini AI** để xây dựng chatbot thông minh.
- Chatbot sử dụng prompt engineering để cung cấp ngữ cảnh (vai trò là trợ lý mua sắm SentimentIQ).
- Nó nhận đầu vào là câu hỏi của người dùng và lịch sử chat, đồng thời được "cấy" dữ liệu từ cơ sở dữ liệu (tên sản phẩm, giá) để phản hồi chính xác (kỹ thuật RAG - Retrieval-Augmented Generation ở dạng đơn giản).
- Mô hình trả về kết quả dưới dạng JSON chứa câu trả lời (`reply`), danh sách sản phẩm liên quan (`products`) và cử chỉ (`gesture`) để đồng bộ với mô hình 3D (VRM).
