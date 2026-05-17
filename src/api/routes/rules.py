"""
Route: Luật kết hợp (Association Rules).
"""

from fastapi import APIRouter, HTTPException

from src.api.services.model_loader import get_models

router = APIRouter(tags=["Luật kết hợp"])


@router.get("/api/association-rules")
async def get_association_rules(
    top_k: int = 20,
    min_lift: float = 1.0,
    min_confidence: float = 0.0,
):
    """Lấy danh sách luật kết hợp với bộ lọc lift/confidence."""
    models = get_models()
    if "rules" not in models:
        raise HTTPException(503, "Association rules chưa sẵn sàng.")

    df = models["rules"]
    filtered = (
        df[(df["lift"] >= min_lift) & (df["confidence"] >= min_confidence)]
        .sort_values("lift", ascending=False)
        .head(top_k)
    )

    return {
        "total_rules": len(df),
        "filtered_rules": len(filtered),
        "rules": filtered.to_dict(orient="records"),
    }
