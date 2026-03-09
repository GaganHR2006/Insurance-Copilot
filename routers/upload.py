from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services.pdf_extractor import extract_policy_info, extract_freebies
from utils.debug_logger import log
import io

router = APIRouter()


# Try pdfplumber first, fall back to pyPDF2
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from uploaded PDF file. Try pdfplumber first, fallback to PyPDF2."""
    text = ""
    file = io.BytesIO(file_bytes)
    
    # Method 1: pdfplumber (better for complex layouts)
    try:
        import pdfplumber
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if len(text.strip()) > 100:
            print(f"[PDF] pdfplumber extracted {len(text)} characters")
            print(f"[PDF] First 500 chars: {text[:500]}")
            return text
    except Exception as e:
        print(f"[PDF] pdfplumber failed: {e}")
    
    # Method 2: PyPDF2 fallback
    try:
        import PyPDF2
        if hasattr(file, 'seek'):
            file.seek(0)
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        print(f"[PDF] PyPDF2 extracted {len(text)} characters")
        print(f"[PDF] First 500 chars: {text[:500]}")
        return text
    except Exception as e:
        print(f"[PDF] PyPDF2 failed: {e}")
    
    print("[PDF] ERROR: Could not extract text from PDF")
    return ""


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
        
        # ── LLM Fallback for basic info ──
        if not policy_info.get("insurer") or not policy_info.get("policy_name"):
            log("UPLOAD_LLM_FALLBACK", "Regex missed insurer. Using Groq LLM...")
            try:
                from services.risk_engine import _call_groq
                import re, json
                prompt = f"""Read this insurance policy text and extract the Insurance Company (Insurer) and the Policy Name/Plan Name.
Return ONLY a valid JSON object with keys "insurer" and "policy_name".
Text:
{pdf_text[:3500]}"""
                raw_llm = await _call_groq(prompt, max_tokens=150)
                match = re.search(r'\{.*\}', raw_llm, re.DOTALL)
                if match:
                    llm_data = json.loads(match.group())
                    if llm_data.get("insurer") and not policy_info.get("insurer"):
                        policy_info["insurer"] = llm_data["insurer"].strip()
                    if llm_data.get("policy_name") and not policy_info.get("policy_name"):
                        policy_info["policy_name"] = llm_data["policy_name"].strip()
            except Exception as llm_e:
                log("UPLOAD_LLM_ERROR", str(llm_e))

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

    return {
        "status": "success",
        "filename": file.filename,
        "text_extracted_chars": len(pdf_text),
        "extracted_text": pdf_text,
        "extracted": policy_info
    }
