"""
Draft Service for Fact-Check Draft Storage.

Issue #123: Backend: Fact-Check Draft Storage API (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

Provides business logic for saving and retrieving reviewer work-in-progress drafts.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fact_check import FactCheck
from app.models.submission_reviewer import SubmissionReviewer
from app.models.user import User, UserRole
from app.models.workflow_transition import WorkflowState
from app.schemas.draft import DraftContent, DraftResponse, DraftUpdate


class DraftError(Exception):
    """Base exception for draft operations."""

    pass


class DraftNotFoundError(DraftError):
    """Raised when fact-check is not found."""

    pass


class DraftPermissionError(DraftError):
    """Raised when user lacks permission to access draft."""

    pass


class DraftWorkflowLockedError(DraftError):
    """Raised when workflow state prevents draft editing."""

    pass


# Editable workflow states - drafts can be saved/modified in these states
EDITABLE_STATES = {
    WorkflowState.ASSIGNED,
    WorkflowState.IN_RESEARCH,
    WorkflowState.DRAFT_READY,
    WorkflowState.NEEDS_MORE_RESEARCH,
}

# Locked workflow states - drafts cannot be modified in these states
LOCKED_STATES = {
    WorkflowState.PUBLISHED,
    WorkflowState.REJECTED,
    WorkflowState.ARCHIVED,
}


async def get_fact_check_with_claim(db: AsyncSession, fact_check_id: UUID) -> Optional[FactCheck]:
    """
    Get fact-check with claim relationship loaded.

    Args:
        db: Database session
        fact_check_id: UUID of the fact-check

    Returns:
        FactCheck with claim loaded, or None if not found
    """
    stmt = (
        select(FactCheck)
        .options(selectinload(FactCheck.claim))
        .where(FactCheck.id == fact_check_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_submission_for_fact_check(db: AsyncSession, fact_check: FactCheck) -> Optional[Any]:
    """
    Get the submission associated with a fact-check via its claim.

    Args:
        db: Database session
        fact_check: FactCheck with claim loaded

    Returns:
        Submission if found, None otherwise
    """
    if not fact_check.claim or not fact_check.claim.submissions:
        return None
    # Get the first submission (a claim can be linked to multiple submissions)
    return fact_check.claim.submissions[0] if fact_check.claim.submissions else None


async def is_user_assigned_reviewer(db: AsyncSession, submission_id: UUID, user_id: UUID) -> bool:
    """
    Check if a user is an assigned reviewer for a submission.

    Args:
        db: Database session
        submission_id: UUID of the submission
        user_id: UUID of the user to check

    Returns:
        True if user is an assigned reviewer, False otherwise
    """
    stmt = select(SubmissionReviewer).where(
        SubmissionReviewer.submission_id == submission_id,
        SubmissionReviewer.reviewer_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def check_draft_access(
    db: AsyncSession, fact_check: FactCheck, user: User, for_write: bool = False
) -> None:
    """
    Check if user has permission to access draft.

    Args:
        db: Database session
        fact_check: FactCheck to check access for
        user: User requesting access
        for_write: Whether this is a write operation (requires editable state)

    Raises:
        DraftPermissionError: If user lacks permission
        DraftWorkflowLockedError: If workflow state is locked (for write operations)
    """
    # Admins and super admins have full access
    if user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        # But still check workflow state for write operations
        if for_write:
            submission = await get_submission_for_fact_check(db, fact_check)
            if submission and submission.workflow_state in LOCKED_STATES:
                raise DraftWorkflowLockedError(
                    f"Cannot modify draft: workflow is in locked state "
                    f"'{submission.workflow_state.value}'"
                )
        return

    # For reviewers, check if they are assigned to the submission
    if user.role == UserRole.REVIEWER:
        submission = await get_submission_for_fact_check(db, fact_check)
        if not submission:
            raise DraftPermissionError(
                "Cannot access draft: fact-check is not linked to a submission"
            )

        # Check workflow state for write operations
        if for_write and submission.workflow_state in LOCKED_STATES:
            raise DraftWorkflowLockedError(
                f"Cannot modify draft: workflow is in locked state "
                f"'{submission.workflow_state.value}'"
            )

        is_assigned = await is_user_assigned_reviewer(db, submission.id, user.id)
        if not is_assigned:
            raise DraftPermissionError("You are not assigned as a reviewer for this submission")
        return

    # Submitters and other roles cannot access drafts
    raise DraftPermissionError("You do not have permission to access drafts")


async def save_draft(
    db: AsyncSession,
    fact_check_id: UUID,
    draft_data: DraftUpdate,
    user: User,
) -> DraftResponse:
    """
    Save or update draft content for a fact-check.

    Args:
        db: Database session
        fact_check_id: UUID of the fact-check
        draft_data: Draft content to save
        user: User saving the draft

    Returns:
        DraftResponse with updated draft

    Raises:
        DraftNotFoundError: If fact-check doesn't exist
        DraftPermissionError: If user lacks permission
        DraftWorkflowLockedError: If workflow state is locked
    """
    # Get fact-check with claim loaded
    fact_check = await get_fact_check_with_claim(db, fact_check_id)
    if not fact_check:
        raise DraftNotFoundError(f"Fact-check {fact_check_id} not found")

    # Check permission
    await check_draft_access(db, fact_check, user, for_write=True)

    # Get existing draft content or create new
    existing_content = fact_check.draft_content or {}
    current_version = existing_content.get("version", 0)

    # Build new draft content by merging with existing
    new_content: dict[str, Any] = {
        "claim_summary": (
            draft_data.claim_summary
            if draft_data.claim_summary is not None
            else existing_content.get("claim_summary")
        ),
        "analysis": (
            draft_data.analysis
            if draft_data.analysis is not None
            else existing_content.get("analysis")
        ),
        "verdict": (
            draft_data.verdict
            if draft_data.verdict is not None
            else existing_content.get("verdict")
        ),
        "justification": (
            draft_data.justification
            if draft_data.justification is not None
            else existing_content.get("justification")
        ),
        "sources_cited": (
            draft_data.sources_cited
            if draft_data.sources_cited is not None
            else existing_content.get("sources_cited", [])
        ),
        "internal_notes": (
            draft_data.internal_notes
            if draft_data.internal_notes is not None
            else existing_content.get("internal_notes")
        ),
        "version": current_version + 1,
        "last_edited_by": str(user.id),
    }

    # Update fact-check
    fact_check.draft_content = new_content
    fact_check.draft_updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(fact_check)

    # Build response
    return DraftResponse(
        fact_check_id=fact_check.id,
        draft_content=DraftContent(
            claim_summary=new_content.get("claim_summary"),
            analysis=new_content.get("analysis"),
            verdict=new_content.get("verdict"),
            justification=new_content.get("justification"),
            sources_cited=new_content.get("sources_cited", []),
            internal_notes=new_content.get("internal_notes"),
            version=new_content.get("version", 1),
            last_edited_by=(
                UUID(new_content["last_edited_by"]) if new_content.get("last_edited_by") else None
            ),
        ),
        draft_updated_at=fact_check.draft_updated_at,
        has_draft=True,
    )


async def get_draft(
    db: AsyncSession,
    fact_check_id: UUID,
    user: User,
) -> DraftResponse:
    """
    Get draft content for a fact-check.

    Args:
        db: Database session
        fact_check_id: UUID of the fact-check
        user: User requesting the draft

    Returns:
        DraftResponse with draft content

    Raises:
        DraftNotFoundError: If fact-check doesn't exist
        DraftPermissionError: If user lacks permission
    """
    # Get fact-check with claim loaded
    fact_check = await get_fact_check_with_claim(db, fact_check_id)
    if not fact_check:
        raise DraftNotFoundError(f"Fact-check {fact_check_id} not found")

    # Check permission (read access)
    await check_draft_access(db, fact_check, user, for_write=False)

    # Build response
    if fact_check.draft_content:
        content = fact_check.draft_content
        draft_content = DraftContent(
            claim_summary=content.get("claim_summary"),
            analysis=content.get("analysis"),
            verdict=content.get("verdict"),
            justification=content.get("justification"),
            sources_cited=content.get("sources_cited", []),
            internal_notes=content.get("internal_notes"),
            version=content.get("version", 1),
            last_edited_by=(
                UUID(content["last_edited_by"]) if content.get("last_edited_by") else None
            ),
        )
        return DraftResponse(
            fact_check_id=fact_check.id,
            draft_content=draft_content,
            draft_updated_at=fact_check.draft_updated_at,
            has_draft=True,
        )

    return DraftResponse(
        fact_check_id=fact_check.id,
        draft_content=None,
        draft_updated_at=None,
        has_draft=False,
    )
