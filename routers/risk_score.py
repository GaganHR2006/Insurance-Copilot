"""
Risk Score Router - Calculates insurance claim risk for a given treatment, hospital, and policy.
"""

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from services.data_loader import load_hospitals, load_policies, load_treatments

router = APIRouter()


class RiskScoreRequest(BaseModel):
    disease: str
    hospital: str
    policy: str


class RiskScoreResponse(BaseModel):
    risk_score: int
    risk_factors: List[str]
    hospital_found: bool
    policy_found: bool
    recommendation: str


@router.post("", response_model=RiskScoreResponse)
def calculate_risk_score(request: RiskScoreRequest):
    """
    Calculate an insurance claim risk score (0-100) for a given disease/treatment,
    hospital, and policy combination.

    Risk factors are evaluated based on waiting periods, room rent caps,
    exclusions, network coverage, pre-auth requirements, and sub-limits.
    """
    hospitals = load_hospitals()
    policies = load_policies()
    treatments = load_treatments()

    disease_lower = request.disease.lower()
    hospital_lower = request.hospital.lower()
    policy_lower = request.policy.lower()

    # Match hospital
    matched_hospital = next(
        (h for h in hospitals if hospital_lower in h["name"].lower()), None
    )
    # Match policy
    matched_policy = next(
        (p for p in policies if policy_lower in p["name"].lower() or policy_lower in p["provider"].lower()),
        None,
    )
    # Match treatment
    matched_treatment = next(
        (t for t in treatments if disease_lower in t["name"].lower()), None
    )

    score = 20  # Base score
    risk_factors: List[str] = []

    if matched_policy:
        # Waiting period > 180 days
        if matched_policy.get("waiting_period_days", 0) > 180:
            score += 20
            risk_factors.append(
                f"Long waiting period: {matched_policy['waiting_period_days']} days (>180 days adds risk)"
            )

        # Room rent cap exists
        if matched_policy.get("room_rent_cap") is not None:
            score += 15
            risk_factors.append(
                f"Room rent cap of ₹{matched_policy['room_rent_cap']}/day may limit coverage"
            )

        # Treatment in exclusions
        exclusions = [e.lower() for e in matched_policy.get("exclusions", [])]
        if any(disease_lower in excl for excl in exclusions):
            score += 10
            risk_factors.append(f"'{request.disease}' found in policy exclusion list")

        # Check sub-limits for treatment category
        if matched_treatment:
            sub_limits = matched_policy.get("sub_limits", {})
            for sub_key in sub_limits:
                if disease_lower in sub_key.lower() or (matched_treatment["category"].lower() in sub_key.lower()):
                    score += 5
                    risk_factors.append(
                        f"Sub-limit of ₹{sub_limits[sub_key]} applies for '{sub_key}'"
                    )

    # Hospital not in network for this policy
    if matched_hospital and matched_policy:
        provider = matched_policy.get("provider", "")
        network = [n.lower() for n in matched_hospital.get("network_policies", [])]
        if provider.lower() not in network:
            score += 15
            risk_factors.append(
                f"Hospital '{matched_hospital['name']}' is NOT in network for '{matched_policy['provider']}'"
            )

    # Pre-auth required
    if matched_treatment and matched_treatment.get("pre_auth_required"):
        score += 10
        risk_factors.append(
            f"Pre-authorisation is required for '{matched_treatment['name']}'"
        )

    # Clamp score to 100
    score = min(score, 100)

    if score < 40:
        recommendation = "Low Risk"
    elif score <= 70:
        recommendation = "Moderate Risk"
    else:
        recommendation = "High Risk"

    return RiskScoreResponse(
        risk_score=score,
        risk_factors=risk_factors,
        hospital_found=matched_hospital is not None,
        policy_found=matched_policy is not None,
        recommendation=recommendation,
    )
