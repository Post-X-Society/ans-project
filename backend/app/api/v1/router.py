"""
API v1 router - aggregates all v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, submissions, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
