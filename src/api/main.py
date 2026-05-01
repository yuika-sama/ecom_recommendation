"""
FastAPI Backend — SentimentIQ
Phân tích Cảm xúc, Phân cụm, Luật kết hợp, Gợi ý Sản phẩm & AI Chatbot.
Chạy: uvicorn src.api.main:app --reload --port 8000
"""

import os
import re
import json
import logging
import joblib
import numpy as np
import pandas as pd
import uvicorn
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Import class ProductRecommender (FIX: phải import trước joblib.load) ──
from src.models.recommender import ProductRecommender  # noqa: F401

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Gemini AI Setup
# ──────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
_gemini_model  = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=(
                "Bạn là trợ lý AI mua sắm thông minh tên 'SentimentIQ Bot' cho nền tảng "
                "thương mại điện tử Việt Nam (Shopee/Tiki).\n"
                "Nhiệm vụ: tư vấn sản phẩm, phân tích đánh giá, giải đáp thắc mắc mua sắm.\n"
                "Quy tắc:\n"
                "- Luôn trả lời bằng tiếng Việt, thân thiện và ngắn gọn (tối đa 120 từ).\n"
                "- Để gợi ý từ hệ thống, thêm ở cuối: ##RECOMMEND:từ_khóa##\n"
                "- Ngoại trừ hệ thống, bạn có thể tự do suy nghĩ và gợi ý thêm các sản phẩm từ các trang bên ngoài trực tiếp trong câu trả lời (kèm link Shopee/Tiki nếu cần).\n"
                "- Nếu cần phân tích review, thêm ở cuối: ##SENTIMENT:nội_dung##\n"
                "- BẮT BUỘC kết thúc câu bằng cử chỉ: ##GESTURE:TênCửChỉ## (chọn 1 trong: Angry, Blush, Clapping, Goodbye, Idle, Jump, LookAround, Relax, Sad, Sleepy, Surprised, Thinking)."
            ),
        )
        logger.info("Gemini AI da ket noi thanh cong (model: %s)", GEMINI_MODEL)
    except Exception as e:
        logger.warning("Khong the khoi tao Gemini: %s — dung rule-based fallback", e)
        _gemini_model = None
else:
    logger.info("GEMINI_API_KEY chua duoc cai dat — dung rule-based chatbot.")

# ──────────────────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────────────────
app = FastAPI(
    title="SentimentIQ API",
    description="Khai phá dữ liệu đa phương tiện — E-commerce Việt Nam",
    version="2.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────
# Đường dẫn
# ──────────────────────────────────────────────────────────
ROOT_DIR      = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = ROOT_DIR / "datas" / "processed"
MODELS_DIR    = ROOT_DIR / "datas" / "models"

# ──────────────────────────────────────────────────────────
# Model Loading — FIX: per-model error handling
# ──────────────────────────────────────────────────────────
_models: dict = {}
_load_attempted = False


def get_models() -> dict:
    """Tải và cache tất cả models. Load từng model độc lập để tránh lỗi cascade."""
    global _load_attempted
    if _load_attempted:
        return _models
    _load_attempted = True

    _load_one("tfidf",      PROCESSED_DIR / "tfidf_vectorizer.pkl")
    _load_one("nb",         MODELS_DIR    / "naive_bayes.pkl")
    _load_one("gmm",        MODELS_DIR    / "gmm_model.pkl")
    _load_one("svd",        MODELS_DIR    / "svd_transformer.pkl")
    _load_one("recommender",MODELS_DIR    / "recommender.pkl")

    try:
        _models["rules"] = pd.read_csv(MODELS_DIR / "association_rules.csv")
        logger.info("  [OK] rules (%d rows)", len(_models["rules"]))
    except Exception as e:
        logger.warning("  [SKIP] rules: %s", e)

    try:
        with open(MODELS_DIR / "topic_labels.json", "r", encoding="utf-8") as f:
            _models["topic_labels"] = json.load(f)
        logger.info("  [OK] topic_labels")
    except Exception as e:
        logger.warning("  [SKIP] topic_labels: %s", e)

    try:
        _models["catalog"] = pd.read_csv(MODELS_DIR / "product_catalog.csv")
        logger.info("  [OK] catalog (%d products)", len(_models["catalog"]))
    except Exception as e:
        logger.warning("  [SKIP] catalog: %s", e)

    loaded = [k for k in ("tfidf","nb","gmm","svd","recommender","rules") if k in _models]
    logger.info("Models da tai: %s", loaded)
    return _models


def _load_one(key: str, path: Path):
    try:
        _models[key] = joblib.load(path)
        logger.info("  [OK] %s", key)
    except Exception as e:
        logger.warning("  [FAIL] %s: %s", key, e)


# ──────────────────────────────────────────────────────────
# NLP Preprocessing
# ──────────────────────────────────────────────────────────
RE_HTML    = re.compile(r"<[^>]+>")
RE_URL     = re.compile(r"https?://\S+|www\.\S+")
RE_EMOJI   = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]+", flags=re.UNICODE)
RE_SPECIAL = re.compile(r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]")
TEENCODE   = {
    "sp":"sản phẩm","ko":"không","k":"không","ok":"được",
    "gh":"giao hàng","ship":"giao hàng","vs":"với","dc":"được",
    "bt":"bình thường","cx":"cũng","nx":"nữa","mn":"mọi người",
    "ae":"anh em","mk":"tôi","ms":"mới","ad":"admin",
}

def preprocess(text: str) -> str:
    text = RE_HTML.sub(" ", text)
    text = RE_URL.sub(" ", text)
    text = RE_EMOJI.sub(" ", text)
    text = text.lower()
    text = RE_SPECIAL.sub(" ", text)
    words = [TEENCODE.get(w, w) for w in text.split()]
    return " ".join(words).strip()

# ──────────────────────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────────────────────
class SentimentRequest(BaseModel):
    text: str

class ClusterRequest(BaseModel):
    text: str

class RecommendRequest(BaseModel):
    query: str
    top_k: int = 10
    exclude_ids: list[str] = []

class ReviewRequest(BaseModel):
    product_id: str
    comment: str
    rating: int          # 1–5

class ChatMessage(BaseModel):
    role: str            # "user" | "model"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    product_id: Optional[str] = None

# ──────────────────────────────────────────────────────────
# Endpoints — Root
# ──────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {"message": "SentimentIQ API v2.0 dang chay!", "gemini": bool(_gemini_model)}


# ──────────────────────────────────────────────────────────
# Sentiment
# ──────────────────────────────────────────────────────────
@app.post("/api/sentiment", tags=["Phan tich cam xuc"])
async def analyze_sentiment(request: SentimentRequest):
    models = get_models()
    if "nb" not in models or "tfidf" not in models:
        raise HTTPException(503, "Model chua san sang. Hay chay notebooks 01-03 truoc.")
    processed = preprocess(request.text)
    X   = models["tfidf"].transform([processed])
    pred = int(models["nb"].predict(X)[0])
    prob = models["nb"].predict_proba(X)[0].tolist()
    return {
        "text": request.text,
        "processed_text": processed,
        "label": pred,
        "sentiment": "Tích cực" if pred == 1 else "Tiêu cực",
        "confidence": {"tieu_cu": round(prob[0], 4), "tich_cu": round(prob[1], 4)},
    }


# ──────────────────────────────────────────────────────────
# Cluster
# ──────────────────────────────────────────────────────────
@app.post("/api/cluster", tags=["Phan cum"])
async def cluster_text(request: ClusterRequest):
    models = get_models()
    if "gmm" not in models:
        raise HTTPException(503, "GMM model chua san sang.")
    processed = preprocess(request.text)
    X_tfidf   = models["tfidf"].transform([processed])
    X_svd     = models["svd"].transform(X_tfidf)
    cid       = int(models["gmm"].predict(X_svd)[0])
    probs     = models["gmm"].predict_proba(X_svd)[0].tolist()
    labels    = models.get("topic_labels", {})
    return {
        "text": request.text,
        "cluster_id": cid,
        "cluster_name": labels.get(str(cid), f"Cụm {cid}"),
        "probabilities": [round(p, 4) for p in probs],
    }


# ──────────────────────────────────────────────────────────
# Association Rules
# ──────────────────────────────────────────────────────────
@app.get("/api/association-rules", tags=["Luat ket hop"])
async def get_association_rules(
    top_k: int = 20,
    min_lift: float = 1.0,
    min_confidence: float = 0.0,
):
    models = get_models()
    if "rules" not in models:
        raise HTTPException(503, "Association rules chua san sang.")
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


# ──────────────────────────────────────────────────────────
# Recommend
# ──────────────────────────────────────────────────────────
@app.post("/api/recommend", tags=["Goi y san pham"])
async def recommend_products(request: RecommendRequest):
    models = get_models()
    if "recommender" not in models:
        raise HTTPException(503, "Recommender chua san sang.")
    processed = preprocess(request.query)
    recs = models["recommender"].recommend_by_query(
        processed, top_k=request.top_k, exclude_ids=request.exclude_ids
    )
    return {
        "query": request.query,
        "total_found": len(recs),
        "recommendations": _df_to_records(recs),
    }


# ──────────────────────────────────────────────────────────
# Products — NEW
# ──────────────────────────────────────────────────────────
@app.get("/api/products", tags=["San pham"])
async def get_products(
    search: str = "",
    category: str = "",
    page: int = 1,
    limit: int = 20,
):
    """Lấy danh sách sản phẩm với tìm kiếm và phân trang."""
    models = get_models()
    if "catalog" not in models:
        raise HTTPException(503, "Product catalog chua san sang.")

    df = models["catalog"].copy()

    if search.strip():
        q = search.lower()
        cols = df.columns.tolist()
        cond = df["name"].fillna("").astype(str).str.lower().str.contains(q, na=False)
        if "category"    in cols: cond = cond | df["category"].fillna("").astype(str).str.lower().str.contains(q, na=False)
        if "description" in cols: cond = cond | df["description"].fillna("").astype(str).str.lower().str.contains(q, na=False)
        df = df[cond]

    if category.strip():
        df = df[df["category"].str.lower() == category.lower()]

    total = len(df)
    start = (page - 1) * limit
    page_df = df.iloc[start: start + limit]

    catalog_all = models["catalog"]
    if "category" in catalog_all.columns:
        categories = sorted(catalog_all["category"].dropna().unique().tolist())
    else:
        categories = []

    display_cols = [c for c in ["product_id","name","category","price","rating"] if c in page_df.columns]
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "products": page_df[display_cols].where(pd.notnull(page_df[display_cols]), None).to_dict(orient="records"),
        "categories": categories[:50],
    }


# ──────────────────────────────────────────────────────────
# Review — NEW
# ──────────────────────────────────────────────────────────
@app.post("/api/review", tags=["Danh gia"])
async def submit_review(request: ReviewRequest):
    """
    Submit đánh giá: phân tích comment + rating → gợi ý sản phẩm phù hợp.
    """
    models = get_models()
    if "nb" not in models or "tfidf" not in models:
        raise HTTPException(503, "Model chua san sang.")

    # 1. Phân tích sentiment từ comment
    processed = preprocess(request.comment)
    X   = models["tfidf"].transform([processed])
    pred = int(models["nb"].predict(X)[0])
    prob = models["nb"].predict_proba(X)[0]
    sentiment_label = "Tích cực" if pred == 1 else "Tiêu cực"
    confidence = {"tieu_cu": round(float(prob[0]), 4), "tich_cu": round(float(prob[1]), 4)}

    # 2. Phân tích rating
    rating = max(1, min(5, request.rating))
    if rating >= 4:
        rating_label = "Tích cực"
    elif rating == 3:
        rating_label = "Trung bình"
    else:
        rating_label = "Tiêu cực"

    # 3. Kết hợp comment + rating để quyết định hướng gợi ý
    # Rating ưu tiên hơn comment khi mâu thuẫn
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
            cid   = int(models["gmm"].predict(X_svd)[0])
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
            # Lấy thông tin sản phẩm hiện tại
            current_product = {}
            if catalog is not None:
                row = catalog[catalog["product_id"].astype(str) == str(request.product_id)]
                if len(row) > 0:
                    current_product = row.iloc[0].to_dict()

            query = current_product.get("category", "") + " " + current_product.get("name", "")

            if combined == "Tích cực":
                # Gợi ý sản phẩm tương tự
                rec_type = "similar"
                recs_df = models["recommender"].recommend_similar(
                    str(request.product_id), top_k=6
                )
                if recs_df.empty:
                    recs_df = models["recommender"].recommend_by_query(query, top_k=6,
                                                                        exclude_ids=[str(request.product_id)])
            else:
                # Tiêu cực → gợi ý thay thế trong cùng category
                rec_type = "alternative"
                recs_df = models["recommender"].recommend_by_query(
                    query, top_k=6, exclude_ids=[str(request.product_id)]
                )

            recommendations = _df_to_records(recs_df)
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


# ──────────────────────────────────────────────────────────
# Chatbot — NEW
# ──────────────────────────────────────────────────────────
@app.post("/api/chatbot", tags=["Chatbot"])
async def chatbot(request: ChatRequest):
    """
    AI Chatbot tư vấn mua sắm.
    Dùng Gemini nếu có API key, fallback sang rule-based.
    """
    message  = request.message.strip()
    history  = request.history

    if _gemini_model:
        return await _gemini_chat(message, history)
    else:
        return await _rule_based_chat(message)


async def _gemini_chat(message: str, history: list[ChatMessage]) -> dict:
    """Gọi Gemini API để sinh phản hồi."""
    try:
        # Chuyển history sang format Gemini
        gemini_history = [
            {"role": m.role, "parts": [m.content]}
            for m in history[-10:]  # Giới hạn 10 turns gần nhất
        ]
        chat = _gemini_model.start_chat(history=gemini_history)
        response = chat.send_message(message)
        raw_text = response.text

        # Phân tích intent từ signal trong response
        intent, query, products = "general", None, None
        gesture = "Idle"  # Mặc định

        if "##GESTURE:" in raw_text:
            parts = raw_text.split("##GESTURE:")
            raw_text = parts[0].strip()
            gesture_text = parts[1].replace("##", "").strip().lower()
            
            valid_gestures_map = {
                "angry": "Angry", "blush": "Blush", "clapping": "Clapping", 
                "goodbye": "Goodbye", "idle": "Idle", "jump": "Jump", 
                "lookaround": "LookAround", "relax": "Relax", "sad": "Sad", 
                "sleepy": "Sleepy", "surprised": "Surprised", "thinking": "Thinking"
            }
            if gesture_text in valid_gestures_map:
                gesture = valid_gestures_map[gesture_text]
            else:
                gesture = "Idle"

        if "##RECOMMEND:" in raw_text:
            parts = raw_text.split("##RECOMMEND:")
            raw_text = parts[0].strip()
            rec_query = parts[1].replace("##", "").strip()
            intent = "recommend"
            query  = rec_query
            models = get_models()
            if "recommender" in models:
                recs_df  = models["recommender"].recommend_by_query(
                    preprocess(rec_query), top_k=6
                )
                products = _df_to_records(recs_df)

        elif "##SENTIMENT:" in raw_text:
            parts = raw_text.split("##SENTIMENT:")
            raw_text    = parts[0].strip()
            review_text = parts[1].replace("##", "").strip()
            intent = "sentiment"
            models = get_models()
            if "nb" in models and "tfidf" in models:
                X    = models["tfidf"].transform([preprocess(review_text)])
                pred = int(models["nb"].predict(X)[0])
                prob = models["nb"].predict_proba(X)[0].tolist()
                query = f"Phân tích: {review_text[:50]}..."
                products = [{
                    "type": "sentiment_result",
                    "label": "Tích cực" if pred == 1 else "Tiêu cực",
                    "confidence": round(max(prob) * 100, 1),
                }]

        return {"reply": raw_text, "intent": intent, "query": query, "products": products, "gesture": gesture}

    except Exception as e:
        logger.error("Gemini error: %s", e)
        return await _rule_based_chat(message)


async def _rule_based_chat(message: str) -> dict:
    """Rule-based chatbot fallback — không cần API key."""
    msg_lower = message.lower()
    models    = get_models()

    # Intent: tìm / gợi ý sản phẩm
    recommend_kws = ["tìm","gợi ý","mua","muốn","cần","bán","có","shop","hàng","sản phẩm"]
    if any(k in msg_lower for k in recommend_kws) and "recommender" in models:
        # Dùng message như query
        processed = preprocess(message)
        recs_df   = models["recommender"].recommend_by_query(processed, top_k=6)
        products  = _df_to_records(recs_df)
        if products:
            return {
                "reply": f"Tôi tìm thấy {len(products)} sản phẩm phù hợp với yêu cầu của bạn:",
                "intent": "recommend",
                "query": message,
                "products": products,
                "gesture": "Clapping"
            }

    # Intent: phân tích review
    sentiment_kws = ["review","đánh giá","bình luận","cảm nhận","tốt không","có tốt"]
    if any(k in msg_lower for k in sentiment_kws) and "nb" in models:
        X    = models["tfidf"].transform([preprocess(message)])
        pred = int(models["nb"].predict(X)[0])
        prob = models["nb"].predict_proba(X)[0].tolist()
        label = "tích cực 😊" if pred == 1 else "tiêu cực 😞"
        conf  = round(max(prob) * 100, 1)
        return {
            "reply": f"Phân tích cho thấy nội dung này có vẻ **{label}** (độ tin cậy {conf}%).",
            "intent": "sentiment",
            "query": None,
            "products": None,
            "gesture": "Thinking"
        }

    # Fallback chung
    greet_kws = ["xin chào","chào","hello","hi","hey"]
    if any(k in msg_lower for k in greet_kws):
        reply = "Xin chào! Tôi là SentimentIQ Bot 🤖 — trợ lý mua sắm thông minh. Tôi có thể giúp bạn tìm sản phẩm hoặc phân tích đánh giá. Bạn cần gì?"
        gesture = "Clapping"
    elif "giá" in msg_lower:
        reply = "Bạn có thể tìm sản phẩm theo khoảng giá trong phần 'Gợi ý sản phẩm'. Thử nhập tên sản phẩm để tôi tìm cho bạn nhé!"
        gesture = "LookAround"
    elif "giúp" in msg_lower or "làm gì" in msg_lower:
        reply = "Tôi có thể:\n• 🔍 Tìm & gợi ý sản phẩm phù hợp\n• 💬 Phân tích đánh giá sản phẩm\n• 🎯 Gợi ý thay thế khi bạn không hài lòng\n\nHãy thử hỏi tôi: 'tìm áo thun nam cotton'!"
        gesture = "Jump"
    else:
        reply = "Tôi chưa hiểu rõ yêu cầu của bạn. Hãy thử hỏi về sản phẩm cụ thể, ví dụ: 'tìm điện thoại pin trâu' hoặc 'gợi ý kem dưỡng da'!"
        gesture = "Idle"

    return {"reply": reply, "intent": "general", "query": None, "products": None, "gesture": gesture}


# ──────────────────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────────────────
@app.get("/api/stats", tags=["Thong ke"])
async def get_stats():
    stats: dict = {}
    try:
        df = pd.read_csv(PROCESSED_DIR / "processed_reviews.csv")
        total    = len(df)
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
        stats["dataset"] = {"error": "Dataset chua duoc xu ly"}

    models = get_models()
    stats["models"] = {
        "naive_bayes":       "nb"          in models,
        "gmm_clustering":    "gmm"         in models,
        "recommender":       "recommender" in models,
        "association_rules": "rules"       in models,
    }
    stats["gemini_enabled"] = bool(_gemini_model)
    return stats


# ──────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────
def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Chuyển DataFrame thành list[dict], xử lý NaN."""
    if df is None or df.empty:
        return []
    return df.where(pd.notnull(df), None).to_dict(orient="records")


# ──────────────────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("src.api.main:app", host=host, port=port, reload=True)
