"""
Hospitals Router - Filter and retrieve hospital network information.
"""

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.data_loader import load_hospitals

router = APIRouter()


class FiltersApplied(BaseModel):
    city: Optional[str] = None
    treatment: Optional[str] = None


class HospitalsResponse(BaseModel):
    hospitals: List[dict]
    count: int
    filters_applied: FiltersApplied


@router.get("", response_model=HospitalsResponse)
def get_hospitals(city: Optional[str] = None, treatment: Optional[str] = None):
    """
    Retrieve hospitals optionally filtered by city and/or treatment.

    Query params:
    - city: Filter hospitals by city (case-insensitive).
    - treatment: Filter hospitals that offer this treatment (case-insensitive).
    """
    hospitals = load_hospitals()

    if city:
        hospitals = [h for h in hospitals if city.lower() in h["city"].lower()]

    if treatment:
        hospitals = [
            h for h in hospitals
            if any(treatment.lower() in t.lower() for t in h["treatments"])
        ]

    return HospitalsResponse(
        hospitals=hospitals,
        count=len(hospitals),
        filters_applied=FiltersApplied(
            city=city if city else None,
            treatment=treatment if treatment else None,
        ),
    )
