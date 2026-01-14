"""
API v1 router - aggregates all v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    auth,
    claims,
    corrections,
    drafts,
    email_templates,
    health,
    peer_review,
    ratings,
    reviewer_assignments,
    rtbf,
    sources,
    submissions,
    transparency,
    transparency_reports,
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
api_router.include_router(drafts.router, tags=["drafts"])
api_router.include_router(sources.router, tags=["sources"])
api_router.include_router(peer_review.router, tags=["peer-review"])
api_router.include_router(corrections.router, tags=["corrections"])
api_router.include_router(
    email_templates.router, prefix="/email-templates", tags=["email-templates"]
)
api_router.include_router(rtbf.router, tags=["rtbf"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(transparency_reports.router, tags=["transparency-reports"])
api_router.include_router(claims.router, tags=["claims"])
