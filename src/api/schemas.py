"""
Pydantic schemas cho SentimentIQ API.
Định nghĩa cấu trúc request/response cho tất cả endpoints.
"""

from typing import Optional

from pydantic import BaseModel


# ── Sentiment ──────────────────────────────────────────────
class SentimentRequest(BaseModel):
    """Request phân tích cảm xúc bình luận."""
    text: str


# ── Cluster ────────────────────────────────────────────────
class ClusterRequest(BaseModel):
    """Request phân cụm chủ đề bình luận."""
    text: str


# ── Recommend ──────────────────────────────────────────────
class RecommendRequest(BaseModel):
    """Request gợi ý sản phẩm theo query text (Content-based)."""
    query: str
    top_k: int = 10
    exclude_ids: list[str] = []


class RecommendUserRequest(BaseModel):
    """Request gợi ý sản phẩm theo user (Collaborative Filtering)."""
    user_id: str
    top_k: int = 10


# ── Review ─────────────────────────────────────────────────
class ReviewRequest(BaseModel):
    """Request gửi đánh giá sản phẩm (rating + comment)."""
    product_id: str
    comment: str
    rating: int  # 1–5


# ── Chatbot ────────────────────────────────────────────────
class ChatMessage(BaseModel):
    """Một tin nhắn trong lịch sử chat."""
    role: str       # "user" | "model"
    content: str


class ChatRequest(BaseModel):
    """Request gửi tin nhắn đến chatbot."""
    message: str
    history: list[ChatMessage] = []
    product_id: Optional[str] = None
