"""
Chat Router - Handles AI-powered Q&A for insurance queries.
Returns a structured response with both raw answer and a parsed bullet list.
"""

from datetime import datetime
from typing import List, Optional
import os

from fastapi import APIRouter
from pydantic import BaseModel

from services.ai_engine import ask_ai

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    policy_context: Optional[str] = ""


class ChatResponse(BaseModel):
    answer: str
    bullets: List[str]
    model: str
    timestamp: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    AI insurance assistant. Returns precise bullet-point answers only.
    Answers are formatted with <b> HTML tags for the critical bullet.
    """
    raw_answer = await ask_ai(request.question, context=request.policy_context or "")

    # Split bullets into a list for frontend rendering
    bullet_list = [
        line.strip() for line in raw_answer.split("\n")
        if line.strip().startswith(("•", "<b>•"))
    ]

    return ChatResponse(
        answer=raw_answer,
        bullets=bullet_list,
        model=os.getenv("AI_MODEL", "llama-3.3-70b-versatile"),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )
