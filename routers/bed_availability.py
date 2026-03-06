"""
Bed Availability Router - Simulates real-time hospital bed availability.
"""

import random
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.data_loader import load_hospitals

router = APIRouter()


class BedAvailabilityRequest(BaseModel):
    hospital_id: Optional[str] = None
    hospital_name: Optional[str] = None
    city: Optional[str] = None


class BedInfo(BaseModel):
    total: int
    available: int


class HospitalBedResult(BaseModel):
    hospital_id: str
    hospital_name: str
    city: str
    icu: BedInfo
    general: BedInfo
    occupancy_rate_percent: float
    last_updated: str


class BedAvailabilityResponse(BaseModel):
    results: List[HospitalBedResult]
    count: int


@router.post("", response_model=BedAvailabilityResponse)
def get_bed_availability(request: BedAvailabilityRequest):
    """
    Get simulated real-time bed availability for hospitals.

    Match is performed by hospital_id, hospital_name (partial), or city.
    At least one filter must be provided.
    """
    hospitals = load_hospitals()

    if not request.hospital_id and not request.hospital_name and not request.city:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of: hospital_id, hospital_name, or city.",
        )

    matched = []
    for h in hospitals:
        if request.hospital_id and h["id"].lower() == request.hospital_id.lower():
            matched.append(h)
        elif request.hospital_name and request.hospital_name.lower() in h["name"].lower():
            matched.append(h)
        elif request.city and request.city.lower() in h["city"].lower():
            matched.append(h)

    # Deduplicate while preserving order
    seen_ids = set()
    unique_matched = []
    for h in matched:
        if h["id"] not in seen_ids:
            seen_ids.add(h["id"])
            unique_matched.append(h)

    results = []
    now = datetime.utcnow().isoformat() + "Z"

    for h in unique_matched:
        total_icu = h["icu_beds"]
        total_general = h["general_beds"]
        avail_icu = random.randint(0, total_icu)
        avail_general = random.randint(0, total_general)

        occupancy = round(
            (1 - avail_general / total_general) * 100 if total_general > 0 else 100.0, 1
        )

        results.append(
            HospitalBedResult(
                hospital_id=h["id"],
                hospital_name=h["name"],
                city=h["city"],
                icu=BedInfo(total=total_icu, available=avail_icu),
                general=BedInfo(total=total_general, available=avail_general),
                occupancy_rate_percent=occupancy,
                last_updated=now,
            )
        )

    return BedAvailabilityResponse(results=results, count=len(results))
