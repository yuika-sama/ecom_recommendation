"""
Route: Gửi đánh giá sản phẩm → phân tích cảm xúc → gợi ý sản phẩm.
"""

import logging

from fastapi import APIRouter, HTTPException

from src.api.schemas import ReviewRequest
from src.api.helpers import preprocess, df_to_records
from src.api.services.model_loader import get_models

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Đánh giá"])


@router.post("/api/review")
async def submit_review(request: ReviewRequest):
    """
    Submit đánh giá: phân tích comment + rating → gợi ý sản phẩm phù hợp.
    """
    models = get_models()
    if "nb" not in models or "tfidf" not in models:
        raise HTTPException(503, "Model chưa sẵn sàng.")

    # 1. Phân tích sentiment từ comment
    processed = preprocess(request.comment)
    X = models["tfidf"].transform([processed])
    pred = int(models["nb"].predict(X)[0])
    prob = models["nb"].predict_proba(X)[0]
    sentiment_label = "Tích cực" if pred == 1 else "Tiêu cực"
    confidence = {
        "tieu_cu": round(float(prob[0]), 4),
        "tich_cu": round(float(prob[1]), 4),
    }

    # 2. Phân tích rating
    rating = max(1, min(5, request.rating))
    if rating >= 4:
        rating_label = "Tích cực"
    elif rating == 3:
        rating_label = "Trung bình"
    else:
        rating_label = "Tiêu cực"

    # 3. Kết hợp comment + rating để quyết định hướng gợi ý
    if rating <= 2:
        combined = "Tiêu cực"
    elif rating >= 4 and pred == 1:
        combined = "Tích cực"
    else:
        combined = "Trung bình"

    # 4. Phân cụm (nếu có model)
    cluster_info = None
    if "gmm" in models and "svd" in models:
        try:
            X_svd = models["svd"].transform(X)
            cid = int(models["gmm"].predict(X_svd)[0])
            labels = models.get("topic_labels", {})
            cluster_info = {
                "cluster_id": cid,
                "cluster_name": labels.get(str(cid), f"Cụm {cid}"),
            }
        except Exception:
            pass

    # 5. Gợi ý sản phẩm dựa trên kết quả phân tích
    recommendations = []
    rec_type = "similar"
    if "recommender" in models:
        try:
            catalog = models.get("catalog")
            current_product = {}
            if catalog is not None:
                row = catalog[catalog["product_id"].astype(str) == str(request.product_id)]
                if len(row) > 0:
                    current_product = row.iloc[0].to_dict()

            query = current_product.get("category", "") + " " + current_product.get("name", "")

            if combined == "Tích cực":
                rec_type = "similar"
                recs_df = models["recommender"].recommend_similar(
                    str(request.product_id), top_k=6
                )
                if recs_df.empty:
                    recs_df = models["recommender"].recommend_by_query(
                        query, top_k=6, exclude_ids=[str(request.product_id)]
                    )
            else:
                rec_type = "alternative"
                recs_df = models["recommender"].recommend_by_query(
                    query, top_k=6, exclude_ids=[str(request.product_id)]
                )

            recommendations = df_to_records(recs_df)
        except Exception as e:
            logger.warning("Recommend error: %s", e)

    return {
        "product_id": request.product_id,
        "comment": request.comment,
        "rating": rating,
        "sentiment": {
            "label": sentiment_label,
            "label_num": pred,
            "confidence": confidence,
        },
        "rating_label": rating_label,
        "combined_label": combined,
        "cluster": cluster_info,
        "rec_type": rec_type,
        "recommendations": recommendations,
    }
