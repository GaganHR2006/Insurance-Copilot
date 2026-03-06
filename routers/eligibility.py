"""
Eligibility Router — delegates to eligibility_engine which uses
PDF policy as primary source.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.eligibility_engine import check_eligibility
from services.data_loader import get_pdf_policy, load_policies

router = APIRouter()


class EligibilityRequest(BaseModel):
    treatment:                str = Field(..., min_length=1)
    policy:                   str = ""
    age:                      int = Field(..., ge=1, le=120)
    waiting_period_served_days: int = Field(..., ge=0)


@router.post("")
async def check_eligibility_route(request: EligibilityRequest):
    """
    Check treatment eligibility.
    Uses uploaded PDF as primary source; falls back to policies.json.
    """
    return check_eligibility(
        treatment=request.treatment,
        policy=request.policy,
        age=request.age,
        waiting_period_served_days=request.waiting_period_served_days,
    )


@router.get("/policy-options")
async def get_policy_options():
    """
    Returns the policy to pre-select in the dropdown.
    If a PDF has been uploaded, returns that policy's details.
    Otherwise returns all policies from the dataset.
    """
    pdf      = get_pdf_policy()
    policies = load_policies()

    policy_list = [
        p.get("name") or p.get("policy_name") or ""
        for p in policies
        if p.get("name") or p.get("policy_name")
    ]

    return {
        "pdf_policy": {
            "detected":           bool(
                pdf.get("insurer") or
                pdf.get("covered_treatments") or
                pdf.get("sum_insured") or
                pdf.get("waiting_period_days")
            ),
            "insurer":            pdf.get("insurer"),
            "policy_name":        pdf.get("policy_name"),
            "covered_treatments": pdf.get("covered_treatments", []),
            "waiting_period_days": pdf.get("waiting_period_days"),
            "sum_insured":        pdf.get("sum_insured"),
        },
        "available_policies": policy_list,
    }
