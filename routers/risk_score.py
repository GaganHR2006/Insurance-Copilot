"""
Risk Score Router — PDF-aware policy risk scoring using Groq LLM.
Accepts optional policy_text from an uploaded PDF for LLM-based analysis.
Falls back to database fuzzy-matching when no PDF is given.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from services.risk_engine import extract_policy_data, extract_risk_factors, calculate

router = APIRouter()


class RiskScoreRequest(BaseModel):
    policy_text: Optional[str] = ""   # Raw text from uploaded PDF


class RiskFactor(BaseModel):
    factor: str
    detail: str
    severity: str  # "high" | "medium" | "low"


class RiskScoreResponse(BaseModel):
    total_score: int
    max_score: int
    grade: str
    color: str
    recommendation: str
    breakdown: Dict[str, int]
    policy_inputs: Dict[str, Any]
    risk_factors: List[RiskFactor]


@router.post("", response_model=RiskScoreResponse)
async def calculate_risk_score(request: RiskScoreRequest):
    """
    Calculate a policy risk score from uploaded PDF text.
    1. LLM extracts structured policy data (waiting period, network size, etc.)
    2. Formula calculates risk score (0=safe, 100=risky)
    3. LLM extracts dynamic risk factors list
    """
    policy_text = request.policy_text or ""

    # Step 1: Extract structured data from PDF text using LLM
    policy_data = await extract_policy_data(policy_text)

    # Step 2: Calculate risk score using corrected formula
    score_result = calculate(policy_data)

    # Step 3: Extract dynamic risk factors from PDF text using LLM
    raw_factors = await extract_risk_factors(policy_text)
    risk_factors = [RiskFactor(**f) for f in raw_factors]

    return RiskScoreResponse(
        total_score=score_result["total_score"],
        max_score=score_result["max_score"],
        grade=score_result["grade"],
        color=score_result["color"],
        recommendation=score_result["recommendation"],
        breakdown=score_result["breakdown"],
        policy_inputs=score_result["policy_inputs"],
        risk_factors=risk_factors,
    )
