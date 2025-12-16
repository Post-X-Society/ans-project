"""
Ans Backend API - Main Application

FastAPI application for the Ans fact-checking service
"""
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
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

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(auth_router, tags=["authentication"])


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "Ans API - Fact-checking service for Amsterdam youth",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
