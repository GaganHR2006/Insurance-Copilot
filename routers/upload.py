from fastapi import APIRouter
from pydantic import BaseModel
from services.pdf_extractor import extract_policy_info

router = APIRouter()


class ExtractRequest(BaseModel):
    text: str
    filename: str = "policy.pdf"


@router.post("")
async def upload_policy(request: ExtractRequest):
    """
    Receives pre-extracted PDF text from frontend.
    Frontend extracts text using PDF.js (no file upload needed).
    This endpoint just parses the text into structured data.
    """
    print(f"[Upload] Received text: {len(request.text)} chars "
          f"from {request.filename}")

    if len(request.text.strip()) < 20:
        return {
            "status": "partial",
            "warning": "Very little text extracted from PDF.",
            "filename": request.filename,
            "full_text": request.text,
            "extracted": {
                "insurer": None,
                "policy_name": request.filename.replace(".pdf", ""),
                "covered_treatments": [],
                "exclusions": [],
                "waiting_period_days": None,
                "sum_insured": None,
                "room_rent_cap": None,
                "min_age": 18,
                "max_age": 65,
                "sub_limits": {},
                "network_hospitals": [],
                "freebies": [],
                "freebies_count": 0,
            }
        }

    try:
        policy_info = extract_policy_info(request.text)
        policy_info["freebies_count"] = len(
            policy_info.get("freebies", [])
        )
        print(f"[Upload] Extracted insurer: "
              f"{policy_info.get('insurer')}, "
              f"treatments: "
              f"{len(policy_info.get('covered_treatments', []))}")
    except Exception as e:
        print(f"[Upload] extract_policy_info error: {e}")
        policy_info = {
            "insurer": None,
            "policy_name": None,
            "covered_treatments": [],
            "exclusions": [],
            "waiting_period_days": None,
            "sum_insured": None,
            "room_rent_cap": None,
            "min_age": 18,
            "max_age": 65,
            "sub_limits": {},
            "network_hospitals": [],
            "freebies": [],
            "freebies_count": 0,
        }

    return {
        "status": "success",
        "filename": request.filename,
        "full_text": request.text[:4000],
        "extracted": policy_info,
    }
