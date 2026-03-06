"""
Insurance Copilot API - Main Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat, risk_score, eligibility, hospitals, bed_availability, upload, notifications

app = FastAPI(
    title="Insurance Copilot API",
    description="AI-powered Indian health insurance advisor API",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(risk_score.router, prefix="/risk-score", tags=["Risk Score"])
app.include_router(eligibility.router, prefix="/eligibility", tags=["Eligibility"])
app.include_router(hospitals.router, prefix="/hospitals", tags=["Hospitals"])
app.include_router(bed_availability.router, prefix="/bed-availability", tags=["Bed Availability"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(notifications.router, tags=["Notifications"])


@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Insurance Copilot"}


@app.on_event("startup")
async def startup_event():
    print("Insurance Copilot API started successfully")
