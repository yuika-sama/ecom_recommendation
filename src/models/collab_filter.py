"""
Collaborative Filtering (User-User) cho gợi ý sản phẩm.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


class CollaborativeFilteringRecommender:
    """
    Hệ thống Gợi ý Sản phẩm dựa trên User-User Collaborative Filtering.
    Tính toán độ tương đồng giữa các người dùng dựa trên lịch sử đánh giá (rating).
    """
    
    def __init__(self, min_rating: float = 0.0):
        """
        Khởi tạo mô hình CF.
        
        Args:
            min_rating: Ngưỡng rating tối thiểu để coi là có tương tác tích cực.
                        Các rating thấp hơn ngưỡng này sẽ bị set về 0 (bỏ qua).
        """
        self.min_rating = min_rating
        self.user_ids: list[str] = []
        self.item_ids: list[str] = []
        self.user_item_matrix: np.ndarray | None = None
        self.user_similarity: np.ndarray | None = None
        self.item_popularity: np.ndarray | None = None

    def fit(
        self,
        orders_df: pd.DataFrame,
        user_col: str = "user_id",
        item_col: str = "product_id",
        rating_col: str = "rating",
    ) -> "CollaborativeFilteringRecommender":
        """
        Huấn luyện mô hình từ dữ liệu lịch sử mua hàng / đánh giá.
        
        Args:
            orders_df: DataFrame chứa dữ liệu tương tác user-item.
            user_col: Tên cột chứa ID người dùng.
            item_col: Tên cột chứa ID sản phẩm.
            rating_col: Tên cột chứa điểm đánh giá.
            
        Returns:
            self: Đối tượng mô hình sau khi huấn luyện.
        """
        df = orders_df.copy()
        if rating_col in df.columns:
            df[rating_col] = pd.to_numeric(df[rating_col], errors="coerce").fillna(0)
        else:
            df[rating_col] = 1

        pivot = df.pivot_table(
            index=user_col,
            columns=item_col,
            values=rating_col,
            aggfunc="mean",
        ).fillna(0)

        self.user_ids = pivot.index.astype(str).tolist()
        self.item_ids = pivot.columns.astype(str).tolist()
        self.user_item_matrix = pivot.values.astype(np.float32)

        if self.min_rating > 0:
            self.user_item_matrix[self.user_item_matrix < self.min_rating] = 0

        self.user_similarity = cosine_similarity(self.user_item_matrix)
        self.item_popularity = (self.user_item_matrix > 0).sum(axis=0)
        return self

    def recommend_for_user(self, user_id: str, top_k: int = 10) -> list[str]:
        """
        Gợi ý sản phẩm cho một người dùng cụ thể.
        
        Args:
            user_id: ID của người dùng.
            top_k: Số lượng sản phẩm muốn gợi ý.
            
        Returns:
            Danh sách product_id của các sản phẩm được gợi ý.
        """
        if self.user_item_matrix is None or self.user_similarity is None:
            return []
        user_id = str(user_id)
        
        # Nếu user chưa từng có trong hệ thống (cold start) -> gợi ý sản phẩm phổ biến
        if user_id not in self.user_ids:
            return self._popular_items(top_k)

        user_idx = self.user_ids.index(user_id)
        similarity = self.user_similarity[user_idx].copy()
        similarity[user_idx] = 0

        scores = similarity @ self.user_item_matrix
        denom = similarity.sum()
        if denom > 0:
            scores = scores / denom

        # Không gợi ý lại các sản phẩm user đã tương tác
        scores[self.user_item_matrix[user_idx] > 0] = -1
        top_indices = np.argsort(scores)[::-1]
        top_indices = [i for i in top_indices if scores[i] > 0][:top_k]
        return [self.item_ids[i] for i in top_indices]

    def _popular_items(self, top_k: int) -> list[str]:
        """Trả về top các sản phẩm phổ biến nhất (nhiều lượt tương tác nhất)."""
        if self.item_popularity is None:
            return []
        top_indices = np.argsort(self.item_popularity)[::-1][:top_k]
        return [self.item_ids[i] for i in top_indices]
