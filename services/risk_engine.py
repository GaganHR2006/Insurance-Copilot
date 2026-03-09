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

async def extract_policy_values_from_pdf(policy_text: str) -> dict:
    """Use Groq LLM to extract structured values from real PDF text."""
    
    if not policy_text or len(policy_text.strip()) < 50:
        print("[RISK] ERROR: policy_text is empty or too short — PDF extraction failed upstream")
        return None  # Return None, not defaults. Caller must handle this.
    
    # Use first 5000 chars for extraction (covers most key clauses)
    text_sample = policy_text[:5000]
    
    prompt = f"""You are an insurance policy analyst. Extract specific values from this policy document.

Read carefully and find:

1. WAITING PERIOD: Look for phrases like "waiting period", "after X days/months/years". 
   Convert to days: 1 month=30, 1 year=365, 2 years=730.
   If multiple waiting periods exist, take the LONGEST one.
   
2. HOSPITAL NETWORK SIZE: Look for number of empanelled/network hospitals.
   "Pan-India" or "across India" = 500. "5000+ hospitals" = 5000.
   If a specific number is stated, use that exact number.
   
3. TREATMENT COVERAGE PERCENT: What percentage of medical treatments are covered?
   Count covered treatments vs exclusions mentioned.
   "Comprehensive" with few exclusions = 80-90.
   Many exclusions listed = 30-50.
   
4. ROOM RENT CAP: Daily room rent limit in Indian Rupees.
   "No limit" or "actual charges" = 99999.
   "1% of sum insured" with sum=500000 = 5000.
   
5. EXCLUSIONS COUNT: Count every distinct treatment/condition explicitly excluded.

POLICY TEXT:
{text_sample}

Respond with ONLY this JSON, no other text:
{{
  "waiting_period_days": <number>,
  "hospital_network_size": <number>,
  "treatment_coverage_percent": <number 1-100>,
  "room_rent_cap": <number in rupees>,
  "exclusions_count": <number>,
  "extraction_notes": "<brief note on what you found for each field>"
}}"""

    try:
        raw = await _call_groq(prompt, max_tokens=300)
        print(f"[RISK] LLM raw extraction response: {raw[:300]}")
        
        # Clean response
        import re, json
        raw = re.sub(r'```json|```', '', raw).strip()
        
        # Find JSON object
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            print("[RISK] ERROR: No JSON found in LLM response")
            return None
            
        data = json.loads(match.group())
        print(f"[RISK] Extraction notes: {data.get('extraction_notes', 'none')}")
        
        result = {
            "waiting_period_days": max(0, int(data.get("waiting_period_days", 30))),
            "hospital_network_size": max(1, int(data.get("hospital_network_size", 50))),
            "treatment_coverage_percent": max(1, min(100, int(data.get("treatment_coverage_percent", 70)))),
            "room_rent_cap": max(0, int(data.get("room_rent_cap", 99999))),
            "exclusions_count": max(0, int(data.get("exclusions_count", 0)))
        }
        print(f"[RISK] Final extracted values: {result}")
        return result
        
    except Exception as e:
        print(f"[RISK] LLM extraction exception: {e}")
        return None


# ─────────────────────────────────────────────
# Risk factors extractor
# ─────────────────────────────────────────────

async def extract_risk_factors(policy_text: str, policy_data: dict = None) -> list:
    """
    Use Groq LLM to extract risk factors from raw policy text.
    Returns a list of dicts: [{factor, detail, severity}, ...].
    """
    llm_factors = []
    if policy_text and policy_text.strip():
        prompt = f"""You are an insurance policy analyst. Read the following policy text and extract all risk factors that could negatively impact the policyholder.
For each risk factor found, return a JSON array where each item has:
- "factor": short name (e.g. "High Waiting Period")
- "detail": one sentence explaining the risk from the actual policy text
- "severity": "high" | "medium" | "low"
Only include factors actually present in the text. Return only a valid JSON array, no extra text, no markdown.

Policy text:
{policy_text[:4000]}"""

        try:
            print("[risk_engine] Calling LLM for risk factors...")
            raw = await _call_groq(prompt, max_tokens=600)
            raw = re.sub(r"```[a-z]*", "", raw).replace("```", "").strip()
            # Find JSON array using regex if necessary
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                raw = match.group()
            factors = json.loads(raw)
            if isinstance(factors, list):
                # Validate each item
                llm_factors = [
                    {
                        "factor": str(f.get("factor", "Unknown Risk")),
                        "detail": str(f.get("detail", "")),
                        "severity": f.get("severity", "medium").lower()
                        if f.get("severity", "").lower() in ("high", "medium", "low") else "medium",
                    }
                    for f in factors
                ]
        except Exception as e:
            print(f"[risk_engine] extract_risk_factors LLM failed: {e}")
            llm_factors = []

    # After LLM extraction, also add rule-based factors from policy_data
    rule_based = []
    if policy_data:
        if policy_data.get("waiting_period_days", 0) > 90:
            rule_based.append({
                "factor": "Extended Waiting Period",
                "detail": f"Waiting period of {policy_data['waiting_period_days']} days before coverage begins.",
                "severity": "high"
            })
        if policy_data.get("hospital_network_size", 999) < 20:
            rule_based.append({
                "factor": "Limited Hospital Network", 
                "detail": "Very few network hospitals listed, limiting your treatment options.",
                "severity": "high"
            })
        if policy_data.get("treatment_coverage_percent", 100) < 50:
            rule_based.append({
                "factor": "Low Treatment Coverage",
                "detail": f"Only {policy_data['treatment_coverage_percent']}% of treatments covered — many procedures may be excluded.",
                "severity": "high"
            })
        if 0 < policy_data.get("room_rent_cap", 99999) < 2000:
            rule_based.append({
                "factor": "Strict Room Rent Cap",
                "detail": f"Room rent capped at ₹{policy_data['room_rent_cap']}/day which may not cover standard hospital rooms.",
                "severity": "medium"
            })
        if policy_data.get("exclusions_count", 0) > 5:
            rule_based.append({
                "factor": "High Exclusion Count",
                "detail": f"{policy_data['exclusions_count']} treatments/conditions are excluded from coverage.",
                "severity": "medium"
            })
    
    # Merge LLM factors + rule-based, deduplicate by factor name
    all_factors = llm_factors + rule_based
    seen = set()
    unique_factors = []
    for f in all_factors:
        f_name = f["factor"].strip().lower()
        if f_name not in seen:
            seen.add(f_name)
            unique_factors.append(f)
            
    print(f"[risk_engine] Found {len(unique_factors)} unique risk factors.")
    return unique_factors if unique_factors else []


# ─────────────────────────────────────────────
# Risk Score Calculator
# ─────────────────────────────────────────────

def calculate_risk_score(policy_data: dict) -> dict:
    """Calculate risk score 0-100. Higher = riskier policy."""
    
    if policy_data is None:
        return {"error": "Could not extract data from PDF. Please ensure the PDF contains readable text."}
    
    print(f"[RISK] Calculating score from: {policy_data}")
    
    score = 0
    breakdown = {}
    
    # 1. Waiting Period (0-25): longer = more risky
    wp = policy_data["waiting_period_days"]
    if wp == 0:       wp_score = 0
    elif wp <= 30:    wp_score = 5
    elif wp <= 90:    wp_score = 12
    elif wp <= 180:   wp_score = 18
    elif wp <= 365:   wp_score = 22
    else:             wp_score = 25
    score += wp_score
    breakdown["waiting_period_risk"] = wp_score
    
    # 2. Hospital Network (0-20): fewer hospitals = more risky
    hn = policy_data["hospital_network_size"]
    if hn >= 500:     hn_score = 0
    elif hn >= 100:   hn_score = 5
    elif hn >= 50:    hn_score = 10
    elif hn >= 20:    hn_score = 15
    else:             hn_score = 20
    score += hn_score
    breakdown["hospital_network_risk"] = hn_score
    
    # 3. Treatment Coverage (0-25): lower coverage = more risky
    tc = policy_data["treatment_coverage_percent"]
    tc_score = round((1 - tc / 100) * 25)
    score += tc_score
    breakdown["coverage_risk"] = tc_score
    
    # 4. Room Rent Cap (0-15): lower cap = more risky
    rr = policy_data["room_rent_cap"]
    if rr >= 10000:   rr_score = 0
    elif rr >= 5000:  rr_score = 3
    elif rr >= 3000:  rr_score = 7
    elif rr >= 1000:  rr_score = 11
    elif rr == 0:     rr_score = 0   # 0 means not mentioned, treat as no cap
    else:             rr_score = 15
    score += rr_score
    breakdown["room_rent_risk"] = rr_score
    
    # 5. Exclusions (0-15): more exclusions = more risky
    ex = policy_data["exclusions_count"]
    if ex == 0:       ex_score = 0
    elif ex <= 2:     ex_score = 3
    elif ex <= 5:     ex_score = 7
    elif ex <= 10:    ex_score = 11
    else:             ex_score = 15
    score += ex_score
    breakdown["exclusions_risk"] = ex_score
    
    # Grade
    if score <= 15:
        grade, color, claim_likelihood, grade_letter, grade_label = "Excellent", "green", "Low", "A", "Excellent protection"
    elif score <= 30:
        grade, color, claim_likelihood, grade_letter, grade_label = "Good", "teal", "Low-Moderate", "B", "Good protection"
    elif score <= 50:
        grade, color, claim_likelihood, grade_letter, grade_label = "Fair", "yellow", "Moderate", "C", "Review recommended"
    elif score <= 70:
        grade, color, claim_likelihood, grade_letter, grade_label = "Poor", "orange", "High", "D", "Consider alternatives"
    else:
        grade, color, claim_likelihood, grade_letter, grade_label = "Critical", "red", "Very High", "F", "Inadequate coverage"
    
    # Recommendation
    recommendations = {
        "Excellent": "This is a comprehensive, low-risk policy. You are well protected.",
        "Good": "Solid policy with minor gaps. Review exclusions before making claims.",
        "Fair": "Moderate risk. Check waiting periods and room rent caps carefully before hospitalisation.",
        "Poor": "High-risk policy with significant gaps. Consider a top-up plan or switching.",
        "Critical": "This policy has critical coverage gaps. Seek alternatives immediately."
    }
    
    result = {
        "total_score": score,
        "max_score": 100,
        "grade": grade,
        "color": color,
        "recommendation": recommendations[grade],
        "breakdown": breakdown,
        "coverage_score": tc,
        "claim_likelihood": claim_likelihood,
        "policy_grade_letter": grade_letter,
        "policy_grade_label": grade_label,
        "policy_inputs": policy_data
    }
    print(f"[RISK] Final result: score={score}, grade={grade}")
    return result
