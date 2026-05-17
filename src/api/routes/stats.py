"""
Route: Thống kê tổng quan hệ thống.
"""

from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from src.api.services.model_loader import get_models, PROCESSED_DIR
from src.api.services.chatbot_service import is_gemini_available

router = APIRouter(tags=["Thống kê"])


@router.get("/api/stats")
async def get_stats():
    """Lấy thống kê tổng quan: dataset, models, Gemini status."""
    stats: dict = {}

    # Thống kê dataset
    try:
        df = pd.read_csv(PROCESSED_DIR / "processed_reviews.csv")
        total = len(df)
        positive = int((df["label"] == 1).sum())
        negative = int((df["label"] == 0).sum())
        stats["dataset"] = {
            "total_reviews": total,
            "positive": positive,
            "negative": negative,
            "positive_ratio": round(positive / total, 4),
            "negative_ratio": round(negative / total, 4),
            "sources": df["source"].value_counts().to_dict() if "source" in df.columns else {},
        }
    except Exception:
        stats["dataset"] = {"error": "Dataset chưa được xử lý"}

    # Trạng thái models
    models = get_models()
    stats["models"] = {
        "naive_bayes": "nb" in models,
        "gmm_clustering": "gmm" in models,
        "recommender": "recommender" in models,
        "collaborative_filtering": "cf_recommender" in models,
        "association_rules": "rules" in models,
    }
    stats["gemini_enabled"] = is_gemini_available()
    return stats
