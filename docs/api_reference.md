# API Reference - SentimentIQ

This document describes the REST API endpoints available in the SentimentIQ backend. The API is built with FastAPI.

## Base URL
`http://localhost:8000`

## Endpoints

### 1. General
#### `GET /`
Check API status.
- **Response:**
  ```json
  {
    "message": "SentimentIQ API v2.0 đang chạy!",
    "gemini": true
  }
  ```

#### `GET /api/stats`
Get overall dataset and model statistics.
- **Response:** JSON object containing dataset statistics (total reviews, positive/negative ratios) and model availability.

### 2. Sentiment Analysis & Clustering
#### `POST /api/sentiment`
Analyze the sentiment of a given text.
- **Body:**
  ```json
  {
    "text": "Sản phẩm rất tốt, giao hàng nhanh chóng."
  }
  ```
- **Response:**
  ```json
  {
    "text": "Sản phẩm rất tốt, giao hàng nhanh chóng.",
    "clean_text": "san pham rat tot giao hang nhanh chong",
    "sentiment": "Tích cực",
    "probabilities": {
      "Tích cực": 0.95,
      "Tiêu cực": 0.05
    }
  }
  ```

#### `POST /api/cluster`
Assign a text to a topic cluster using GMM.
- **Body:**
  ```json
  {
    "text": "Đóng gói cẩn thận, shipper nhiệt tình."
  }
  ```
- **Response:**
  ```json
  {
    "cluster": 0,
    "probabilities": [0.8, 0.1, 0.1]
  }
  ```

### 3. Recommendations
#### `POST /api/recommend`
Get content-based product recommendations based on a search query.
- **Body:**
  ```json
  {
    "query": "áo thun nam cotton",
    "top_k": 10
  }
  ```
- **Response:** JSON array of recommended products with `similarity_score`.

#### `POST /api/recommend-user`
Get collaborative filtering recommendations for a specific user ID.
- **Body:**
  ```json
  {
    "user_id": "prs_18",
    "top_k": 10
  }
  ```
- **Response:**
  ```json
  {
    "user_id": "prs_18",
    "recommendations": [
      {
        "product_id": "prs_1001",
        "name": "Áo thun",
        "price": 150000,
        "category": "Thời trang nam"
      }
    ]
  }
  ```

### 4. Catalog & Reviews
#### `GET /api/products/search`
Search for products by name or get all products.
- **Parameters:**
  - `q` (optional): Search keyword.
  - `limit` (default 50): Number of items to return.
- **Response:** JSON array of matching products.

#### `GET /api/products/{product_id}`
Get details of a specific product.
- **Response:** JSON object containing product metadata.

#### `GET /api/reviews/{product_id}`
Get reviews for a specific product.
- **Response:** JSON array of reviews.

#### `POST /api/reviews/{product_id}`
Submit a new review for a product.
- **Body:**
  ```json
  {
    "rating": 5,
    "comment": "Sản phẩm tốt"
  }
  ```
- **Response:** Acknowledgment of review submission and auto-calculated sentiment.

### 5. Chatbot
#### `POST /api/chatbot`
Interact with the AI Assistant.
- **Body:**
  ```json
  {
    "message": "Tìm cho tôi một cái áo khoác",
    "history": [],
    "product_id": null
  }
  ```
- **Response:**
  ```json
  {
    "reply": "Chào bạn, đây là một số áo khoác...",
    "products": [...],
    "gesture": "Talking"
  }
  ```
