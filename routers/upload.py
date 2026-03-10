from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services.pdf_extractor import extract_policy_info
import io
import asyncio

router = APIRouter()


def fast_extract_text(file_bytes: bytes,
                      max_pages: int = 5,
                      max_chars: int = 3000) -> str:
    """
    Extract text from PDF quickly.
    Only reads first max_pages pages.
    Stops after max_chars characters.
    Uses pypdf (fastest) then pdfplumber as fallback.
    """
    text = ""

    # Method 1: pypdf (fastest, no heavy dependencies)
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_to_read = min(len(reader.pages), max_pages)
        for i in range(pages_to_read):
            page_text = reader.pages[i].extract_text() or ""
            text += page_text + "\n"
            if len(text) >= max_chars:
                break
        text = text[:max_chars]
        if len(text.strip()) > 100:
            print(f"[Upload] pypdf extracted {len(text)} chars")
            return text
    except Exception as e:
        print(f"[Upload] pypdf failed: {e}")

    # Method 2: pdfplumber (fallback)
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_to_read = min(len(pdf.pages), max_pages)
            for i in range(pages_to_read):
                page_text = pdf.pages[i].extract_text() or ""
                text += page_text + "\n"
                if len(text) >= max_chars:
                    break
        text = text[:max_chars]
        print(f"[Upload] pdfplumber extracted {len(text)} chars")
        return text
    except Exception as e:
        print(f"[Upload] pdfplumber failed: {e}")

    return text


@router.post("")
async def upload_policy(file: UploadFile = File(...)):
    print(f"[Upload] Started: {file.filename}")

    # Validate
    if not (file.filename.lower().endswith(".pdf")
            or file.content_type == "application/pdf"):
        raise HTTPException(400, "Only PDF files accepted.")

    # Read file bytes
    try:
        contents = await file.read()
        print(f"[Upload] Read {len(contents)} bytes")
    except Exception as e:
        raise HTTPException(500, f"File read failed: {e}")

    # Check file size (Vercel limit: 4.5MB body)
    if len(contents) > 4 * 1024 * 1024:
        raise HTTPException(
            413,
            "PDF too large. Please upload a PDF under 4MB."
        )

    # Extract text with timeout safety
    try:
        pdf_text = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, fast_extract_text, contents
            ),
            timeout=8.0  # 8s max — Vercel limit is 10s
        )
    except asyncio.TimeoutError:
        print("[Upload] Text extraction timed out")
        pdf_text = ""
    except Exception as e:
        print(f"[Upload] Extraction error: {e}")
        pdf_text = ""

    print(f"[Upload] Extracted {len(pdf_text)} chars")

    # Extract policy info from text
    if len(pdf_text.strip()) < 20:
        # Return minimal response so frontend doesn't hang
        return JSONResponse({
            "status": "partial",
            "warning": "Could not read PDF text. "
                       "It may be a scanned/image PDF.",
            "filename": file.filename,
            "full_text": "",
            "extracted": {
                "insurer": None,
                "policy_name": file.filename.replace(".pdf",""),
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
        })

    # Parse structured data
    try:
        policy_info = extract_policy_info(pdf_text)
    except Exception as e:
        print(f"[Upload] extract_policy_info failed: {e}")
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
        }

    policy_info["freebies_count"] = len(
        policy_info.get("freebies", [])
    )

    print(f"[Upload] Done. Insurer: {policy_info.get('insurer')}")

    return {
        "status": "success",
        "filename": file.filename,
        "full_text": pdf_text,
        "extracted": policy_info,
    }
