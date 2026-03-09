from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

router = APIRouter()


class FreebiesRequest(BaseModel):
    pdf_policy: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MarkUsedRequest(BaseModel):
    freebie_id: str
    used_count: int = 1
    pdf_policy: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ResetRequest(BaseModel):
    freebie_id: str
    pdf_policy: Optional[Dict[str, Any]] = Field(default_factory=dict)


@router.post("/notifications/freebies")
async def get_freebies(request: FreebiesRequest):
    from utils.debug_logger import log

    pdf = request.pdf_policy or {}
    log("NOTIFICATIONS_POST", {
        "has_pdf": bool(pdf),
        "insurer": pdf.get("insurer") if pdf else None,
        "freebies_in_store": len(pdf.get("freebies", [])) if pdf else 0
    })

    if not pdf or (not pdf.get("insurer") and not pdf.get("full_text")):
        return {
            "pdf_uploaded": False,
            "message": "Upload your policy PDF to see free benefits.",
            "freebies": [],
            "summary": {
                "total_benefits": 0,
                "available": 0,
                "used": 0,
                "total_value_inr": 0
            }
        }

    freebies = pdf.get("freebies", [])

    # If freebies empty but PDF was uploaded — try re-extracting
    if not freebies and pdf.get("full_text"):
        log("FREEBIES_REEXTRACT", "Freebies empty, re-extracting...")
        try:
            from services.pdf_extractor import extract_freebies
            freebies = extract_freebies(pdf["full_text"])
            pdf["freebies"] = freebies
            log("FREEBIES_REEXTRACT_RESULT",
                {"count": len(freebies)})
        except Exception as e:
            log("FREEBIES_REEXTRACT_ERROR", str(e))

    # Group by category
    grouped = {}
    for f in freebies:
        cat = f.get("category", "other")
        grouped.setdefault(cat, []).append(f)

    available = sum(
        1 for f in freebies
        if f.get("status") != "fully_used" and
           (f.get("remaining") is None or f.get("remaining", 0) > 0)
    )
    total_value = sum(f.get("value_inr") or 0 for f in freebies)

    return {
        "pdf_uploaded": True,
        "policy_name": pdf.get("policy_name"),
        "insurer": pdf.get("insurer"),
        "freebies": freebies,
        "grouped": grouped,
        "summary": {
            "total_benefits": len(freebies),
            "available": available,
            "used": sum(f.get("used", 0) for f in freebies),
            "total_value_inr": total_value,
        },
        "updated_pdf_policy": pdf, # Pass back in case re-extraction happened
    }


@router.post("/notifications/freebies/mark-used")
async def mark_freebie_used(request: MarkUsedRequest):
    """
    Mark a freebie as used (called when user avails a benefit).
    Returns updated pdf_policy to persist in frontend.
    """
    pdf = request.pdf_policy or {}
    if not pdf:
        raise HTTPException(status_code=404,
                            detail="No policy uploaded.")

    freebies = pdf.get("freebies", [])
    updated = False

    for f in freebies:
        if f["id"] == request.freebie_id:
            total = f.get("total_per_cycle")
            new_used = f.get("used", 0) + request.used_count
            f["used"] = new_used
            if total is not None:
                f["remaining"] = max(0, total - new_used)
                f["status"] = (
                    "fully_used" if f["remaining"] == 0
                    else "partially_used"
                )
            f["last_used"] = datetime.utcnow().isoformat() + "Z"
            updated = True
            break

    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Freebie '{request.freebie_id}' not found."
        )

    pdf["freebies"] = freebies

    return {
        "success": True,
        "freebie_id": request.freebie_id,
        "updated_freebie": next(
            f for f in freebies
            if f["id"] == request.freebie_id
        ),
        "updated_pdf_policy": pdf
    }


@router.post("/notifications/freebies/reset")
async def reset_freebie(request: ResetRequest):
    """Reset a freebie's used count (e.g. on policy renewal)."""
    pdf = request.pdf_policy or {}
    if not pdf:
        raise HTTPException(status_code=404,
                            detail="No policy uploaded.")
    freebies = pdf.get("freebies", [])
    for f in freebies:
        if f["id"] == request.freebie_id:
            total = f.get("total_per_cycle")
            f["used"] = 0
            f["remaining"] = total
            f["status"] = "available"
            break
            
    pdf["freebies"] = freebies
    return {
        "success": True, 
        "message": f"{request.freebie_id} reset.",
        "updated_pdf_policy": pdf
    }
