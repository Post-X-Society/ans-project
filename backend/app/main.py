"""
Ans Backend API - Main Application

FastAPI application for the Ans fact-checking service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title="Ans API",
    description="Fact-checking service API for Amsterdam youth via Snapchat",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint"""
    return {
        "message": "Ans API - Fact-checking service for Amsterdam youth",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
