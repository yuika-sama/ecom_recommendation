"""
Route: Phân tích cảm xúc bình luận (Naive Bayes).
"""

from fastapi import APIRouter, HTTPException

from src.api.schemas import SentimentRequest
from src.api.helpers import preprocess
from src.api.services.model_loader import get_models

router = APIRouter(tags=["Phân tích cảm xúc"])


@router.post("/api/sentiment")
async def analyze_sentiment(request: SentimentRequest):
    """Phân loại bình luận: Tích cực / Tiêu cực bằng Naive Bayes."""
    models = get_models()
    if "nb" not in models or "tfidf" not in models:
        raise HTTPException(503, "Model chưa sẵn sàng. Hãy chạy notebooks 01-03 trước.")

    processed = preprocess(request.text)
    X = models["tfidf"].transform([processed])
    pred = int(models["nb"].predict(X)[0])
    prob = models["nb"].predict_proba(X)[0].tolist()

    return {
        "text": request.text,
        "processed_text": processed,
        "label": pred,
        "sentiment": "Tích cực" if pred == 1 else "Tiêu cực",
        "confidence": {
            "tieu_cu": round(prob[0], 4),
            "tich_cu": round(prob[1], 4),
        },
    }
