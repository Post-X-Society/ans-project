"""
API v1 router - aggregates all v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    health,
    ratings,
    reviewer_assignments,
    submissions,
    transparency,
    users,
    workflow,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(
    reviewer_assignments.router, prefix="/submissions", tags=["reviewer-assignments"]
)
api_router.include_router(transparency.router, prefix="/transparency", tags=["transparency"])
api_router.include_router(ratings.router, tags=["ratings"])
api_router.include_router(workflow.router, tags=["workflow"])
