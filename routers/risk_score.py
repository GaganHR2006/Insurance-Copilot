"""
Risk Score Router — PDF-aware policy risk scoring using Groq LLM.
Accepts optional policy_text from an uploaded PDF for LLM-based analysis.
Falls back to database fuzzy-matching when no PDF is given.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from services.risk_engine import extract_policy_values_from_pdf, extract_risk_factors, calculate_risk_score

router = APIRouter()


class RiskScoreRequest(BaseModel):
    policy_text: Optional[str] = ""   # Raw text from uploaded PDF
    policy_context: Optional[dict] = None
    pdf_policy: Optional[dict] = None


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
    coverage_score: int
    coverage_label: str
    claim_likelihood: str
    policy_grade_letter: str
    policy_grade_label: str


@router.post("")
async def calculate_risk_score_api(request: RiskScoreRequest):
    """
    Calculate a policy risk score from uploaded PDF text.
    """
    policy_text = request.policy_text or ""
    
    if not policy_text or len(policy_text.strip()) < 50:
        print("[RISK] ERROR: No PDF text in session or text too short.")
        return JSONResponse(
            status_code=400,
            content={"error": "Could not extract data from PDF. Please ensure the PDF contains readable text and re-upload."}
        )

    # Step 1: Extract structured data from PDF text using LLM
    policy_data = await extract_policy_values_from_pdf(policy_text)
    
    if not policy_data:
        return JSONResponse(
            status_code=400,
            content={"error": "Our AI could not extract the necessary risk factors from this PDF. Please try a clearer document."}
        )

    # Step 2: Calculate risk score using corrected formula
    score_result = calculate_risk_score(policy_data)
    
    if "error" in score_result:
        return JSONResponse(status_code=400, content={"error": score_result["error"]})

    # Step 3: Extract dynamic risk factors from PDF text using LLM
    raw_factors = await extract_risk_factors(policy_text, policy_data)
    
    # Return directly, skipping strict response_model if we want flexibility
    return {
        "total_score": score_result.get("total_score", 0),
        "max_score": score_result.get("max_score", 100),
        "grade": score_result.get("grade", "N/A"),
        "color": score_result.get("color", "gray"),
        "recommendation": score_result.get("recommendation", ""),
        "breakdown": score_result.get("breakdown", {}),
        "policy_inputs": score_result.get("policy_inputs", {}),
        "risk_factors": raw_factors,
        "coverage_score": score_result.get("coverage_score", 0),
        "claim_likelihood": score_result.get("claim_likelihood", ""),
        "policy_grade_letter": score_result.get("policy_grade_letter", ""),
        "policy_grade_label": score_result.get("policy_grade_label", ""),
        "raw_text_length": len(policy_text)
    }
