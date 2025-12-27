"""
Draft API Endpoints for Fact-Check Draft Storage.

Issue #123: Backend: Fact-Check Draft Storage API (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- PATCH /fact-checks/{id}/draft - Save/update draft content
- GET /fact-checks/{id}/draft - Retrieve draft data
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.draft import DraftResponse, DraftUpdate
from app.services.draft_service import (
    DraftNotFoundError,
    DraftPermissionError,
    DraftWorkflowLockedError,
    get_draft,
    save_draft,
)

router = APIRouter()


@router.patch(
    "/fact-checks/{fact_check_id}/draft",
    response_model=DraftResponse,
    status_code=status.HTTP_200_OK,
    tags=["drafts"],
    summary="Save/update draft content",
    description="""
Save or update draft content for a fact-check.

**Authorization:**
- Assigned reviewers can save drafts on their assigned fact-checks
- Admins and super admins can save drafts on any fact-check

**Editable States:** assigned, in_research, draft_ready, needs_more_research

**Locked States (403):** published, rejected, archived
""",
)
async def update_draft(
    fact_check_id: UUID,
    draft_data: DraftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftResponse:
    """
    Save or update draft content for a fact-check.

    Supports partial updates - only provided fields are updated.
    Draft version is automatically incremented on each save.
    """
    try:
        return await save_draft(
            db=db,
            fact_check_id=fact_check_id,
            draft_data=draft_data,
            user=current_user,
        )
    except DraftNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except DraftPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except DraftWorkflowLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e


@router.get(
    "/fact-checks/{fact_check_id}/draft",
    response_model=DraftResponse,
    status_code=status.HTTP_200_OK,
    tags=["drafts"],
    summary="Get draft content",
    description="""
Retrieve draft content for a fact-check.

**Authorization:**
- Assigned reviewers can view drafts on their assigned fact-checks
- Admins and super admins can view drafts on any fact-check

Returns `has_draft: false` if no draft exists yet.
""",
)
async def retrieve_draft(
    fact_check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftResponse:
    """
    Retrieve draft content for a fact-check.

    Returns the current draft state including version and last editor.
    Returns `has_draft: false` if no draft has been saved yet.
    """
    try:
        return await get_draft(
            db=db,
            fact_check_id=fact_check_id,
            user=current_user,
        )
    except DraftNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except DraftPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
