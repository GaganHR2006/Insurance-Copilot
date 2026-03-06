from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services.pdf_extractor import extract_policy_info, extract_freebies
from services.data_loader import store_pdf_policy, get_pdf_policy
from utils.debug_logger import log
import io

router = APIRouter()


# Try pdfplumber first, fall back to pypdf
def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""

    # Method 1: pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        log("PDF_EXTRACT_pdfplumber", {
            "chars_extracted": len(text),
            "preview": text[:300]
        })
        if len(text.strip()) > 50:
            return text
    except Exception as e:
        log("PDF_EXTRACT_pdfplumber_ERROR", str(e))

    # Method 2: pypdf fallback
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        log("PDF_EXTRACT_pypdf", {
            "chars_extracted": len(text),
            "preview": text[:300]
        })
        if len(text.strip()) > 50:
            return text
    except Exception as e:
        log("PDF_EXTRACT_pypdf_ERROR", str(e))

    # Method 3: PyPDF2 fallback
    try:
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        log("PDF_EXTRACT_PyPDF2", {
            "chars_extracted": len(text),
            "preview": text[:300]
        })
    except Exception as e:
        log("PDF_EXTRACT_PyPDF2_ERROR", str(e))

    return text


@router.post("")
async def upload_policy(file: UploadFile = File(...)):
    log("UPLOAD_START", {"filename": file.filename,
                          "content_type": file.content_type})

    # Validate file type
    if not (file.filename.endswith(".pdf") or
            file.content_type == "application/pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files accepted."
        )

    # Read bytes
    try:
        contents = await file.read()
        log("UPLOAD_READ", {"bytes": len(contents)})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )

    # Extract text
    pdf_text = extract_text_from_pdf(contents)
    log("PDF_TEXT_LENGTH", {"chars": len(pdf_text)})

    if len(pdf_text.strip()) < 20:
        # Return partial success — store what we can
        log("PDF_TEXT_EMPTY", "Could not extract meaningful text")
        empty_policy = {
            "insurer": None,
            "policy_name": file.filename.replace(".pdf", ""),
            "covered_treatments": [],
            "exclusions": [],
            "freebies": [],
            "freebies_count": 0,
            "full_text": "",
            "extraction_failed": True
        }
        store_pdf_policy(empty_policy)
        return JSONResponse(status_code=200, content={
            "status": "partial",
            "warning": "Could not extract text from PDF. "
                       "It may be a scanned image PDF.",
            "filename": file.filename,
            "extracted": empty_policy
        })

    # Extract structured policy info
    try:
        policy_info = extract_policy_info(pdf_text)
        log("POLICY_INFO_EXTRACTED", {
            "insurer": policy_info.get("insurer"),
            "policy_name": policy_info.get("policy_name"),
            "covered_treatments": policy_info.get("covered_treatments"),
            "waiting_period_days": policy_info.get("waiting_period_days"),
            "freebies_count": len(policy_info.get("freebies", []))
        })
    except Exception as e:
        log("POLICY_EXTRACT_ERROR", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Policy extraction failed: {str(e)}"
        )

    # Extract freebies separately (with full debug)
    try:
        freebies = extract_freebies(pdf_text)
        log("FREEBIES_EXTRACTED", {
            "count": len(freebies),
            "freebies": [
                {"id": f["id"], "label": f["label"],
                 "total": f.get("total_per_cycle")}
                for f in freebies
            ]
        })
        policy_info["freebies"] = freebies
        policy_info["freebies_count"] = len(freebies)
    except Exception as e:
        log("FREEBIES_EXTRACT_ERROR", str(e))
        policy_info["freebies"] = []
        policy_info["freebies_count"] = 0

    # Store full text for AI context
    policy_info["full_text"] = pdf_text
    policy_info["filename"] = file.filename

    # Store in session
    store_pdf_policy(policy_info)

    # Verify it was stored
    stored = get_pdf_policy()
    log("STORAGE_VERIFY", {
        "stored_ok": bool(stored),
        "insurer": stored.get("insurer"),
        "freebies_count": len(stored.get("freebies", []))
    })

    return {
        "status": "success",
        "filename": file.filename,
        "text_extracted_chars": len(pdf_text),
        "extracted": {
            "insurer": policy_info.get("insurer"),
            "policy_name": policy_info.get("policy_name"),
            "covered_treatments": policy_info.get("covered_treatments", []),
            "sum_insured": policy_info.get("sum_insured"),
            "waiting_period_days": policy_info.get("waiting_period_days"),
            "freebies": freebies,
            "freebies_count": len(freebies),
        }
    }
