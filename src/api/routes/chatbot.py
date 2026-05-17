"""
Route: AI Chatbot tư vấn mua sắm.
"""

from fastapi import APIRouter

from src.api.schemas import ChatRequest
from src.api.services.chatbot_service import handle_chat

router = APIRouter(tags=["Chatbot"])


@router.post("/api/chatbot")
async def chatbot(request: ChatRequest):
    """
    AI Chatbot tư vấn mua sắm.
    Dùng Gemini nếu có API key, fallback sang rule-based.
    """
    message = request.message.strip()
    history = [{"role": m.role, "content": m.content} for m in request.history]
    return await handle_chat(message, history)
