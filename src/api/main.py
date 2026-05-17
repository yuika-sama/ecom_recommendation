"""
FastAPI Backend — SentimentIQ
Phân tích Cảm xúc, Phân cụm, Luật kết hợp, Gợi ý Sản phẩm & AI Chatbot.

Chạy: uvicorn src.api.main:app --reload --port 8000
"""

import logging
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.services.chatbot_service import init_gemini, is_gemini_available
from src.api.routes import sentiment, cluster, recommend, review, products, rules, stats, chatbot

# ── Cấu hình ──────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Khởi tạo Gemini AI (sau load_dotenv)
init_gemini()

# ── FastAPI App ────────────────────────────────────────────
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

# ── Đăng ký routes ─────────────────────────────────────────
app.include_router(sentiment.router)
app.include_router(cluster.router)
app.include_router(recommend.router)
app.include_router(review.router)
app.include_router(products.router)
app.include_router(rules.router)
app.include_router(stats.router)
app.include_router(chatbot.router)


@app.get("/", tags=["Root"])
async def root():
    """Health check endpoint."""
    return {
        "message": "SentimentIQ API v2.0 đang chạy!",
        "gemini": is_gemini_available(),
    }


# ── Chạy trực tiếp ────────────────────────────────────────
if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("src.api.main:app", host=host, port=port, reload=True)
