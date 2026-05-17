"""
Route: Phân cụm chủ đề bình luận (GMM / EM).
"""

from fastapi import APIRouter, HTTPException

from src.api.schemas import ClusterRequest
from src.api.helpers import preprocess
from src.api.services.model_loader import get_models

router = APIRouter(tags=["Phân cụm"])


@router.post("/api/cluster")
async def cluster_text(request: ClusterRequest):
    """Phân cụm bình luận theo chủ đề bằng Gaussian Mixture Model."""
    models = get_models()
    if "gmm" not in models:
        raise HTTPException(503, "GMM model chưa sẵn sàng.")

    processed = preprocess(request.text)
    X_tfidf = models["tfidf"].transform([processed])
    X_svd = models["svd"].transform(X_tfidf)
    cid = int(models["gmm"].predict(X_svd)[0])
    probs = models["gmm"].predict_proba(X_svd)[0].tolist()
    labels = models.get("topic_labels", {})

    return {
        "text": request.text,
        "cluster_id": cid,
        "cluster_name": labels.get(str(cid), f"Cụm {cid}"),
        "probabilities": [round(p, 4) for p in probs],
    }
