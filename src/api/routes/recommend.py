"""
Route: Gợi ý sản phẩm (Content-based + Collaborative Filtering).
"""

from fastapi import APIRouter, HTTPException

from src.api.schemas import RecommendRequest, RecommendUserRequest
from src.api.helpers import preprocess, df_to_records
from src.api.services.model_loader import get_models

router = APIRouter(tags=["Gợi ý sản phẩm"])


@router.post("/api/recommend")
async def recommend_products(request: RecommendRequest):
    """Gợi ý sản phẩm dựa trên query text (Content-based Filtering)."""
    models = get_models()
    if "recommender" not in models:
        raise HTTPException(503, "Recommender chưa sẵn sàng.")

    processed = preprocess(request.query)
    recs = models["recommender"].recommend_by_query(
        processed, top_k=request.top_k, exclude_ids=request.exclude_ids
    )
    return {
        "query": request.query,
        "total_found": len(recs),
        "recommendations": df_to_records(recs),
    }


@router.post("/api/recommend-user")
async def recommend_for_user(request: RecommendUserRequest):
    """Gợi ý sản phẩm theo người dùng (Collaborative Filtering)."""
    models = get_models()
    if "cf_recommender" not in models:
        raise HTTPException(503, "CF model chưa sẵn sàng.")

    product_ids = models["cf_recommender"].recommend_for_user(
        request.user_id, top_k=request.top_k
    )

    if not product_ids:
        return {
            "user_id": request.user_id,
            "total_found": 0,
            "recommendations": [],
        }

    catalog = models.get("catalog")
    if catalog is None:
        return {
            "user_id": request.user_id,
            "total_found": len(product_ids),
            "recommendations": [{"product_id": pid} for pid in product_ids],
        }

    df = catalog[catalog["product_id"].astype(str).isin(product_ids)].copy()
    df["__rank"] = df["product_id"].astype(str).apply(
        lambda pid: product_ids.index(pid)
    )
    df = df.sort_values("__rank").drop(columns=["__rank"])

    return {
        "user_id": request.user_id,
        "total_found": len(df),
        "recommendations": df_to_records(df),
    }
