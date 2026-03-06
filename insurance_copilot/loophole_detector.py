"""
loophole_detector.py — LoopholeDetector: Identifies hidden loopholes in policy text.
Uses Groq LLM with a structured prompt to extract JSON.
"""

import json
import os
import re

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

_SYSTEM_PROMPT = """You are an expert insurance policy analyst.
Your task is to carefully read the provided policy text and extract potential loopholes,
limitations, and hidden clauses. You MUST respond ONLY with a valid JSON object and nothing
else — no markdown fences, no explanation, just the raw JSON.

The JSON must have exactly these keys:
{
  "waiting_periods": [],
  "room_rent_caps": [],
  "exclusions": [],
  "sub_limits": [],
  "co_payment_clauses": []
}

Each value is a list of short, descriptive strings summarising the relevant clauses found.
If a category has no clauses, return an empty list for that key."""


class LoopholeDetector:
    """
    Analyses insurance policy text and surfaces hidden loopholes.

    Uses a Groq LLM with a structured prompt to produce a machine-readable
    JSON summary of waiting periods, caps, exclusions, sub-limits, and
    co-payment requirements.
    """

    def __init__(self):
        """Initialise the detector with a Groq LLM client."""
        api_key = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=api_key,
            temperature=0.0,
        )

    # ------------------------------------------------------------------
    def detect(self, policy_text: str) -> dict:
        """
        Detect loopholes and limitations in the given policy text.

        Args:
            policy_text: Raw text of an insurance policy document.

        Returns:
            A dict with keys: waiting_periods, room_rent_caps, exclusions,
            sub_limits, co_payment_clauses. On parse failure, returns a
            dict with an 'error' key and 'raw_response'.
        """
        try:
            messages = [
                ("system", _SYSTEM_PROMPT),
                ("human", f"Policy Text:\n\n{policy_text}"),
            ]
            response = self.llm.invoke(messages)
            raw = response.content.strip()

            # Strip accidental markdown code fences if present
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            result = json.loads(raw)

            # Ensure all expected keys exist
            defaults = {
                "waiting_periods": [],
                "room_rent_caps": [],
                "exclusions": [],
                "sub_limits": [],
                "co_payment_clauses": [],
            }
            defaults.update(result)
            return defaults

        except json.JSONDecodeError as exc:
            return {
                "error": f"JSON parse error: {exc}",
                "raw_response": raw if "raw" in dir() else "No response",
            }
        except Exception as exc:
            return {"error": f"LLM call failed: {exc}"}
