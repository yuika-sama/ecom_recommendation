"""
Service xử lý logic chatbot: Gemini AI và rule-based fallback.
"""

import logging
import os

from src.api.helpers import preprocess, df_to_records
from src.api.services.model_loader import get_models

logger = logging.getLogger(__name__)

# ── Gemini AI Setup ────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
_gemini_model = None

VALID_GESTURES = {
    "angry": "Angry", "blush": "Blush", "clapping": "Clapping",
    "goodbye": "Goodbye", "idle": "Idle", "jump": "Jump",
    "lookaround": "LookAround", "relax": "Relax", "sad": "Sad",
    "sleepy": "Sleepy", "surprised": "Surprised", "thinking": "Thinking",
}


def init_gemini():
    """Khởi tạo Gemini AI model. Gọi sau khi load_dotenv()."""
    global _gemini_model
    if not GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY chưa được cài đặt — dùng rule-based chatbot.")
        return

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=(
                "Bạn là trợ lý AI mua sắm thông minh tên 'SentimentIQ Bot' cho nền tảng "
                "thương mại điện tử Việt Nam (hiện tại sử dụng dữ liệu Shopee).\n"
                "Nhiệm vụ: tư vấn sản phẩm, phân tích đánh giá, giải đáp thắc mắc mua sắm.\n"
                "Quy tắc:\n"
                "- Luôn trả lời bằng tiếng Việt, thân thiện và ngắn gọn (tối đa 120 từ).\n"
                "- Để gợi ý từ hệ thống, thêm ở cuối: ##RECOMMEND:từ_khóa##\n"
                "- Ngoại trừ hệ thống, bạn có thể tự do suy nghĩ và gợi ý thêm các sản phẩm "
                "từ các trang bên ngoài trực tiếp trong câu trả lời (kèm link Shopee/Tiki nếu cần).\n"
                "- Nếu cần phân tích review, thêm ở cuối: ##SENTIMENT:nội_dung##\n"
                "- BẮT BUỘC kết thúc câu bằng cử chỉ: ##GESTURE:TênCửChỉ## "
                "(chọn 1 trong: Angry, Blush, Clapping, Goodbye, Idle, Jump, LookAround, "
                "Relax, Sad, Sleepy, Surprised, Thinking)."
            ),
        )
        logger.info("Gemini AI đã kết nối thành công (model: %s)", GEMINI_MODEL)
    except Exception as e:
        logger.warning("Không thể khởi tạo Gemini: %s — dùng rule-based fallback", e)
        _gemini_model = None


def is_gemini_available() -> bool:
    """Kiểm tra Gemini AI đã được khởi tạo chưa."""
    return _gemini_model is not None


async def handle_chat(message: str, history: list[dict]) -> dict:
    """Xử lý tin nhắn chatbot: ưu tiên Gemini, fallback sang rule-based."""
    if _gemini_model:
        return await _gemini_chat(message, history)
    return await _rule_based_chat(message)


async def _gemini_chat(message: str, history: list[dict]) -> dict:
    """Gọi Gemini API để sinh phản hồi."""
    try:
        # Chuyển history sang format Gemini
        gemini_history = [
            {"role": m["role"], "parts": [m["content"]]}
            for m in history[-10:]
        ]
        chat = _gemini_model.start_chat(history=gemini_history)
        response = chat.send_message(message)
        raw_text = response.text

        # Phân tích intent từ signal trong response
        intent, query, products = "general", None, None
        gesture = "Idle"

        # Trích xuất gesture
        if "##GESTURE:" in raw_text:
            parts = raw_text.split("##GESTURE:")
            raw_text = parts[0].strip()
            gesture_text = parts[1].replace("##", "").strip().lower()
            gesture = VALID_GESTURES.get(gesture_text, "Idle")

        # Trích xuất recommend intent
        if "##RECOMMEND:" in raw_text:
            parts = raw_text.split("##RECOMMEND:")
            raw_text = parts[0].strip()
            rec_query = parts[1].replace("##", "").strip()
            intent = "recommend"
            query = rec_query
            models = get_models()
            if "recommender" in models:
                recs_df = models["recommender"].recommend_by_query(
                    preprocess(rec_query), top_k=6
                )
                products = df_to_records(recs_df)

        # Trích xuất sentiment intent
        elif "##SENTIMENT:" in raw_text:
            parts = raw_text.split("##SENTIMENT:")
            raw_text = parts[0].strip()
            review_text = parts[1].replace("##", "").strip()
            intent = "sentiment"
            models = get_models()
            if "nb" in models and "tfidf" in models:
                X = models["tfidf"].transform([preprocess(review_text)])
                pred = int(models["nb"].predict(X)[0])
                prob = models["nb"].predict_proba(X)[0].tolist()
                query = f"Phân tích: {review_text[:50]}..."
                products = [{
                    "type": "sentiment_result",
                    "label": "Tích cực" if pred == 1 else "Tiêu cực",
                    "confidence": round(max(prob) * 100, 1),
                }]

        return {
            "reply": raw_text, "intent": intent,
            "query": query, "products": products, "gesture": gesture,
        }

    except Exception as e:
        logger.error("Gemini error: %s", e)
        return await _rule_based_chat(message)


async def _rule_based_chat(message: str) -> dict:
    """Rule-based chatbot fallback — không cần API key."""
    msg_lower = message.lower()
    models = get_models()

    # Intent: tìm / gợi ý sản phẩm
    recommend_kws = [
        "tìm", "gợi ý", "mua", "muốn", "cần", "bán", "có", "shop", "hàng", "sản phẩm",
    ]
    if any(k in msg_lower for k in recommend_kws) and "recommender" in models:
        processed = preprocess(message)
        recs_df = models["recommender"].recommend_by_query(processed, top_k=6)
        products = df_to_records(recs_df)
        if products:
            return {
                "reply": f"Tôi tìm thấy {len(products)} sản phẩm phù hợp với yêu cầu của bạn:",
                "intent": "recommend", "query": message,
                "products": products, "gesture": "Clapping",
            }

    # Intent: phân tích review
    sentiment_kws = ["review", "đánh giá", "bình luận", "cảm nhận", "tốt không", "có tốt"]
    if any(k in msg_lower for k in sentiment_kws) and "nb" in models:
        X = models["tfidf"].transform([preprocess(message)])
        pred = int(models["nb"].predict(X)[0])
        prob = models["nb"].predict_proba(X)[0].tolist()
        label = "tích cực 😊" if pred == 1 else "tiêu cực 😞"
        conf = round(max(prob) * 100, 1)
        return {
            "reply": f"Phân tích cho thấy nội dung này có vẻ **{label}** (độ tin cậy {conf}%).",
            "intent": "sentiment", "query": None,
            "products": None, "gesture": "Thinking",
        }

    # Fallback chung
    greet_kws = ["xin chào", "chào", "hello", "hi", "hey"]
    if any(k in msg_lower for k in greet_kws):
        reply = (
            "Xin chào! Tôi là SentimentIQ Bot 🤖 — trợ lý mua sắm thông minh. "
            "Tôi có thể giúp bạn tìm sản phẩm hoặc phân tích đánh giá. Bạn cần gì?"
        )
        gesture = "Clapping"
    elif "giá" in msg_lower:
        reply = (
            "Bạn có thể tìm sản phẩm theo khoảng giá trong phần 'Gợi ý sản phẩm'. "
            "Thử nhập tên sản phẩm để tôi tìm cho bạn nhé!"
        )
        gesture = "LookAround"
    elif "giúp" in msg_lower or "làm gì" in msg_lower:
        reply = (
            "Tôi có thể:\n• 🔍 Tìm & gợi ý sản phẩm phù hợp\n"
            "• 💬 Phân tích đánh giá sản phẩm\n"
            "• 🎯 Gợi ý thay thế khi bạn không hài lòng\n\n"
            "Hãy thử hỏi tôi: 'tìm áo thun nam cotton'!"
        )
        gesture = "Jump"
    else:
        reply = (
            "Tôi chưa hiểu rõ yêu cầu của bạn. Hãy thử hỏi về sản phẩm cụ thể, "
            "ví dụ: 'tìm điện thoại pin trâu' hoặc 'gợi ý kem dưỡng da'!"
        )
        gesture = "Idle"

    return {
        "reply": reply, "intent": "general",
        "query": None, "products": None, "gesture": gesture,
    }
