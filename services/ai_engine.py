"""
AI Engine Service - Handles all communication with Groq AI via OpenAI-compatible API.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = (
    "You are an expert Indian health insurance advisor. Answer questions clearly and concisely "
    "about insurance policies, coverage, claims, and hospital networks."
)


async def ask_ai(question: str, context: str = "") -> str:
    """
    Send a question to Groq AI and return the text response.

    Args:
        question: The user's question.
        context: Optional policy or situational context to prepend.

    Returns:
        The AI-generated answer as a string.
    """
    user_message = f"{context}\n\n{question}".strip() if context else question

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        return f"AI service error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Failed to get AI response: {str(e)}"
