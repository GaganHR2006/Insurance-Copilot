"""
Chat Router - Handles AI-powered Q&A for insurance queries.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.ai_engine import ask_ai, AI_MODEL

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    policy_context: Optional[str] = ""


class ChatResponse(BaseModel):
    answer: str
    model: str
    timestamp: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Ask an insurance-related question. Optionally provide policy context
    to get more tailored answers from the AI advisor.
    """
    answer = await ask_ai(request.question, context=request.policy_context or "")
    return ChatResponse(
        answer=answer,
        model=AI_MODEL,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )
