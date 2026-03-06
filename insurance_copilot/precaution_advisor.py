"""
precaution_advisor.py — PrecautionAdvisor: Advises patients when treatments aren't covered.
Uses Groq LLM to generate empathetic, actionable precautions.
"""

import os
from typing import List

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

_SYSTEM_PROMPT = (
    "You are a helpful medical insurance advisor. When a treatment is not covered "
    "by insurance, provide 5 practical, safe, and actionable precautions the patient "
    "can take. Be empathetic and clear."
)


class PrecautionAdvisor:
    """
    Provides coverage status and actionable precautions for medical treatments.

    When a treatment is covered, it returns a simple confirmation.
    When a treatment is NOT covered, the Groq LLM generates five patient-friendly
    precautionary steps.
    """

    def __init__(self):
        """Initialise the advisor with a Groq LLM client."""
        api_key = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=api_key,
            temperature=0.4,
        )

    # ------------------------------------------------------------------
    def _parse_precautions(self, text: str) -> List[str]:
        """
        Parse LLM output into a clean list of 5 precaution strings.

        Args:
            text: Raw LLM response text containing bullet points.

        Returns:
            A list of precaution strings (stripped of leading markers).
        """
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        precautions = []
        for line in lines:
            # Strip common list markers: 1. 2. • - *
            cleaned = line.lstrip("0123456789.-•*) ").strip()
            if cleaned:
                precautions.append(cleaned)
        return precautions[:5]

    # ------------------------------------------------------------------
    def advise(self, treatment: str, is_covered: bool, policy_context: str = "") -> dict:
        """
        Return coverage status and (if not covered) actionable precautions.

        Args:
            treatment: Name of the medical treatment or procedure.
            is_covered: True if the treatment is covered by the policy.
            policy_context: Optional additional context from the policy.

        Returns:
            A dict with keys:
            - If covered: status, message, precautions (empty list).
            - If not covered: treatment, coverage, precautions (list of 5),
              disclaimer.
        """
        if is_covered:
            return {
                "status": "covered",
                "message": "Treatment is covered under your policy.",
                "precautions": [],
            }

        try:
            user_prompt = (
                f"Treatment: {treatment}\n"
                f"This treatment is NOT covered by the patient's insurance policy.\n"
            )
            if policy_context:
                user_prompt += f"Policy context: {policy_context}\n"
            user_prompt += "Provide 5 bullet-point precautions."

            messages = [
                ("system", _SYSTEM_PROMPT),
                ("human", user_prompt),
            ]
            response = self.llm.invoke(messages)
            precautions = self._parse_precautions(response.content)

        except Exception as exc:
            precautions = [f"[ERROR] Could not generate precautions: {exc}"]

        return {
            "treatment": treatment,
            "coverage": "Not covered",
            "precautions": precautions,
            "disclaimer": "This is general advice. Please consult a medical professional.",
        }
