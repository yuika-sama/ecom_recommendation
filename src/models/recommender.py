"""
Module ProductRecommender — Hệ thống Gợi ý Sản phẩm Content-based.

Được định nghĩa ở đây (không trong notebook) để joblib.load() hoạt động
đúng khi tải model từ API server.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Các cột sẽ trả về khi gợi ý sản phẩm
RECOMMEND_COLS = ["product_id", "name", "category", "price", "rating", "similarity_score", "url", "location"]


class ProductRecommender:
    """
    Hệ thống Gợi ý Sản phẩm dựa trên Content-based Filtering.
    Sử dụng TF-IDF + Cosine Similarity trên văn bản mô tả sản phẩm.
    """

    def __init__(self, ngram_range: tuple = (1, 2), max_features: int = 30_000):
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            min_df=1,
            sublinear_tf=True,
        )
        self.df_catalog: pd.DataFrame | None = None
        self.tfidf_matrix = None

    def fit(self, df_catalog: pd.DataFrame, text_column: str = "combined_text"):
        """
        Huấn luyện vectorizer trên danh mục sản phẩm.
        
        Args:
            df_catalog: DataFrame chứa danh sách sản phẩm.
            text_column: Tên cột chứa văn bản để huấn luyện (đã qua tiền xử lý).
            
        Returns:
            self: Trả về chính đối tượng ProductRecommender sau khi fit.
        """
        self.df_catalog = df_catalog.reset_index(drop=True)
        self.tfidf_matrix = self.vectorizer.fit_transform(
            df_catalog[text_column].fillna("")
        )
        return self

    def recommend_by_query(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.01,
        exclude_ids: list | None = None,
    ) -> pd.DataFrame:
        """
        Gợi ý sản phẩm dựa trên query text của người dùng.

        Args:
            query: Từ khóa / mô tả nhu cầu người dùng.
            top_k: Số lượng sản phẩm muốn trả về.
            min_similarity: Ngưỡng cosine similarity tối thiểu để lọc kết quả.
            exclude_ids: Danh sách product_id cần loại trừ (ví dụ sản phẩm người dùng đang xem).
            
        Returns:
            DataFrame chứa thông tin top_k sản phẩm gợi ý và độ tương đồng (similarity_score).
        """
        if self.tfidf_matrix is None or self.df_catalog is None:
            return pd.DataFrame()

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Loại trừ các sản phẩm được chỉ định
        if exclude_ids:
            for pid in exclude_ids:
                mask = self.df_catalog["product_id"] == str(pid)
                similarities[mask] = 0.0

        top_idx = np.where(similarities >= min_similarity)[0]
        top_idx = top_idx[np.argsort(similarities[top_idx])[::-1]][:top_k]

        if len(top_idx) == 0:
            # Fallback: lấy top_k không cần ngưỡng nếu không có kết quả nào đạt ngưỡng
            top_idx = np.argsort(similarities)[::-1][:top_k]

        result = self.df_catalog.iloc[top_idx].copy()
        result["similarity_score"] = similarities[top_idx].round(4)
        available_cols = [c for c in RECOMMEND_COLS if c in result.columns]
        return result[available_cols]

    def recommend_similar(
        self,
        product_id: str,
        top_k: int = 10,
    ) -> pd.DataFrame:
        """
        Gợi ý sản phẩm tương tự với một sản phẩm đã có trong danh mục.
        
        Args:
            product_id: ID của sản phẩm gốc.
            top_k: Số lượng sản phẩm muốn trả về.
            
        Returns:
            DataFrame chứa thông tin các sản phẩm tương tự.
        """
        if self.tfidf_matrix is None or self.df_catalog is None:
            return pd.DataFrame()

        idx_list = self.df_catalog.index[
            self.df_catalog["product_id"] == str(product_id)
        ].tolist()
        if not idx_list:
            return pd.DataFrame()

        idx = idx_list[0]
        product_vec = self.tfidf_matrix[idx]
        similarities = cosine_similarity(product_vec, self.tfidf_matrix).flatten()
        similarities[idx] = 0.0  # Loại chính sản phẩm đó

        top_idx = np.argsort(similarities)[::-1][:top_k]
        result = self.df_catalog.iloc[top_idx].copy()
        result["similarity_score"] = similarities[top_idx].round(4)
        available_cols = [c for c in RECOMMEND_COLS if c in result.columns]
        return result[available_cols]

    def get_categories(self) -> list:
        """Trả về danh sách tất cả danh mục sản phẩm."""
        if self.df_catalog is None:
            return []
        return sorted(self.df_catalog["category"].dropna().unique().tolist())
