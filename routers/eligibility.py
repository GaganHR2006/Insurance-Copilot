"""
Eligibility Router - Checks insurance claim eligibility for a given treatment and policy.
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.data_loader import load_policies, load_treatments

router = APIRouter()


class EligibilityRequest(BaseModel):
    treatment: str
    policy: str
    age: int
    waiting_period_served_days: int


class EligibilityChecks(BaseModel):
    treatment_covered: bool
    waiting_period_met: bool
    age_eligible: bool
    not_excluded: bool


class EligibilityResponse(BaseModel):
    eligible: bool
    checks: EligibilityChecks
    reason: str
    estimated_coverage_inr: Optional[int] = None


@router.post("", response_model=EligibilityResponse)
def check_eligibility(request: EligibilityRequest):
    """
    Check whether a treatment is eligible for coverage under a given policy,
    factoring in age, waiting period served, and exclusions.

    Returns eligibility status, individual check results, a human-readable reason,
    and estimated coverage amount if eligible.
    """
    policies = load_policies()
    treatments = load_treatments()

    treatment_lower = request.treatment.lower()
    policy_lower = request.policy.lower()

    matched_policy = next(
        (
            p for p in policies
            if policy_lower in p["name"].lower() or policy_lower in p["provider"].lower()
        ),
        None,
    )
    matched_treatment = next(
        (t for t in treatments if treatment_lower in t["name"].lower()), None
    )

    # Default checks
    treatment_covered = False
    waiting_period_met = False
    age_eligible = 18 <= request.age <= 65
    not_excluded = True

    if matched_policy:
        covered = [c.lower() for c in matched_policy.get("covered_treatments", [])]
        treatment_covered = any(treatment_lower in c for c in covered)

        waiting_period_met = (
            request.waiting_period_served_days >= matched_policy.get("waiting_period_days", 0)
        )

        exclusions = [e.lower() for e in matched_policy.get("exclusions", [])]
        not_excluded = not any(treatment_lower in excl for excl in exclusions)

    eligible = treatment_covered and waiting_period_met and age_eligible and not_excluded

    # Build human-readable reason
    reasons = []
    if not treatment_covered:
        policy_name = matched_policy["name"] if matched_policy else request.policy
        reasons.append(f"'{request.treatment}' is not covered under {policy_name}")
    if not waiting_period_met:
        wp = matched_policy.get("waiting_period_days", "N/A") if matched_policy else "N/A"
        reasons.append(
            f"Waiting period not met (required: {wp} days, served: {request.waiting_period_served_days} days)"
        )
    if not age_eligible:
        reasons.append(f"Age {request.age} is outside eligible range (18–65)")
    if not not_excluded:
        reasons.append(f"'{request.treatment}' is explicitly excluded by this policy")

    if eligible:
        reason = "All eligibility checks passed. Claim is likely to be approved."
    else:
        reason = "; ".join(reasons) + "."

    estimated_coverage_inr = None
    if eligible and matched_treatment:
        estimated_coverage_inr = int(matched_treatment["avg_cost_inr"] * 0.85)

    return EligibilityResponse(
        eligible=eligible,
        checks=EligibilityChecks(
            treatment_covered=treatment_covered,
            waiting_period_met=waiting_period_met,
            age_eligible=age_eligible,
            not_excluded=not_excluded,
        ),
        reason=reason,
        estimated_coverage_inr=estimated_coverage_inr,
    )
