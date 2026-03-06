"""
Risk Engine Service - Calculates policy risk scores and extracts risk factors.
Uses Groq LLM to analyse uploaded policy PDFs for structured data extraction.
"""

import json
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()
_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
_AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")


# ─────────────────────────────────────────────
# LLM helper
# ─────────────────────────────────────────────

async def _call_groq(prompt: str, max_tokens: int = 600) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {_GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": _AI_MODEL,
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


# ─────────────────────────────────────────────
# Policy data extractor
# ─────────────────────────────────────────────

async def extract_policy_data(policy_text: str) -> dict:
    """
    Use Groq LLM to extract structured numeric values from raw policy text.
    Returns a dict with: waiting_period_days, hospital_network_size,
    treatment_coverage_percent, room_rent_cap, exclusions_count.
    Falls back to conservative defaults if extraction fails.
    """
    if not policy_text or not policy_text.strip():
        return _default_policy_data()

    prompt = f"""From the insurance policy text below, extract these values as JSON only:
{{
  "waiting_period_days": <integer: the longest waiting period in days mentioned>,
  "hospital_network_size": <integer: number of network hospitals. If 'pan-India' use 200, if 'limited' use 30, if explicitly stated use that number>,
  "treatment_coverage_percent": <integer 0-100: overall breadth of treatment coverage>,
  "room_rent_cap": <integer: daily room rent cap in rupees. Use 0 if no cap mentioned>,
  "exclusions_count": <integer: count of distinct exclusions listed in the policy>
}}
Return ONLY the JSON object, no explanation, no markdown.

Policy text:
{policy_text[:4000]}"""

    try:
        raw = await _call_groq(prompt, max_tokens=200)
        # strip any markdown code fences
        raw = re.sub(r"```[a-z]*", "", raw).replace("```", "").strip()
        data = json.loads(raw)
        # Validate types
        return {
            "waiting_period_days": int(data.get("waiting_period_days", 30)),
            "hospital_network_size": int(data.get("hospital_network_size", 50)),
            "treatment_coverage_percent": int(data.get("treatment_coverage_percent", 70)),
            "room_rent_cap": int(data.get("room_rent_cap", 3000)),
            "exclusions_count": int(data.get("exclusions_count", 3)),
        }
    except Exception as e:
        print(f"[risk_engine] extract_policy_data failed: {e}")
        return _default_policy_data()


def _default_policy_data() -> dict:
    return {
        "waiting_period_days": 30,
        "hospital_network_size": 50,
        "treatment_coverage_percent": 70,
        "room_rent_cap": 3000,
        "exclusions_count": 3,
    }


# ─────────────────────────────────────────────
# Risk factors extractor
# ─────────────────────────────────────────────

async def extract_risk_factors(policy_text: str) -> list:
    """
    Use Groq LLM to extract risk factors from raw policy text.
    Returns a list of dicts: [{factor, detail, severity}, ...].
    """
    if not policy_text or not policy_text.strip():
        return []

    prompt = f"""You are an insurance policy analyst. Read the following policy text and extract all risk factors that could negatively impact the policyholder.
For each risk factor found, return a JSON array where each item has:
- "factor": short name (e.g. "High Waiting Period")
- "detail": one sentence explaining the risk from the actual policy text
- "severity": "high" | "medium" | "low"
Only include factors actually present in the text. Return only a valid JSON array, no extra text, no markdown.

Policy text:
{policy_text[:4000]}"""

    try:
        raw = await _call_groq(prompt, max_tokens=600)
        raw = re.sub(r"```[a-z]*", "", raw).replace("```", "").strip()
        factors = json.loads(raw)
        if not isinstance(factors, list):
            return []
        # Validate each item
        return [
            {
                "factor": str(f.get("factor", "Unknown Risk")),
                "detail": str(f.get("detail", "")),
                "severity": f.get("severity", "medium").lower()
                if f.get("severity", "").lower() in ("high", "medium", "low") else "medium",
            }
            for f in factors
        ]
    except Exception as e:
        print(f"[risk_engine] extract_risk_factors failed: {e}")
        return []


# ─────────────────────────────────────────────
# Risk Score Calculator
# ─────────────────────────────────────────────

def calculate(policy_data: dict) -> dict:
    """
    Corrected risk scoring formula.
    RISK SCORE = measure of HOW RISKY the policy is (0 = safest, 100 = riskiest).
    Lower score = safer policy.

    policy_data keys:
      - waiting_period_days: int (lower is better)
      - hospital_network_size: int (higher is better)
      - treatment_coverage_percent: int 0-100 (higher is better)
      - room_rent_cap: int Rs/day (higher is better; 0 = no cap = best)
      - exclusions_count: int (lower is better)
    """

    # ── Waiting Period Risk (0-25 pts) ──
    wp = policy_data.get("waiting_period_days", 30)
    if wp <= 30:
        wp_risk = 5
    elif wp <= 60:
        wp_risk = 12
    elif wp <= 90:
        wp_risk = 18
    else:
        wp_risk = 25

    # ── Hospital Network Risk (0-20 pts) ──
    hn = policy_data.get("hospital_network_size", 50)
    if hn >= 100:
        hn_risk = 0
    elif hn >= 50:
        hn_risk = 8
    elif hn >= 20:
        hn_risk = 14
    else:
        hn_risk = 20

    # ── Treatment Coverage Risk (0-25 pts) ──
    tc = policy_data.get("treatment_coverage_percent", 80)
    tc_risk = round((1 - tc / 100) * 25)

    # ── Room Rent Cap Risk (0-15 pts) ──
    rr = policy_data.get("room_rent_cap", 3000)
    if rr == 0 or rr >= 5000:
        rr_risk = 0
    elif rr >= 3000:
        rr_risk = 5
    elif rr >= 1500:
        rr_risk = 10
    else:
        rr_risk = 15

    # ── Exclusions Risk (0-15 pts) ──
    ex = policy_data.get("exclusions_count", 2)
    if ex == 0:
        ex_risk = 0
    elif ex <= 2:
        ex_risk = 5
    elif ex <= 5:
        ex_risk = 10
    else:
        ex_risk = 15

    score = min(wp_risk + hn_risk + tc_risk + rr_risk + ex_risk, 100)

    # ── Grade ──
    if score <= 20:
        grade = "Excellent"
        color = "green"
        recommendation = "This is a low-risk, comprehensive policy. You are well covered."
    elif score <= 40:
        grade = "Good"
        color = "teal"
        recommendation = "This policy is fairly solid. Minor gaps exist — review exclusions."
    elif score <= 60:
        grade = "Fair"
        color = "yellow"
        recommendation = "Moderate risk. Check waiting periods and room rent caps carefully."
    elif score <= 80:
        grade = "Poor"
        color = "orange"
        recommendation = "High risk policy. Consider switching or adding a top-up plan."
    else:
        grade = "Critical"
        color = "red"
        recommendation = "Very high risk. This policy has significant coverage gaps."

    return {
        "total_score": score,
        "max_score": 100,
        "grade": grade,
        "color": color,
        "breakdown": {
            "waiting_period_risk": wp_risk,
            "hospital_network_risk": hn_risk,
            "coverage_risk": tc_risk,
            "room_rent_risk": rr_risk,
            "exclusions_risk": ex_risk,
        },
        "recommendation": recommendation,
        "policy_inputs": policy_data,
    }
