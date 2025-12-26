"""
Workflow API Endpoints for EFCSN-compliant state machine transitions.

Issue #60: Backend: Rating & Workflow API Endpoints (TDD)
EPIC #47: EFCSN Rating System & Workflow State Machine
ADR 0005: EFCSN Compliance Architecture

Endpoints:
- POST /workflow/{submission_id}/transition - State transition (role-based)
- GET /workflow/{submission_id}/history - Full timeline (authenticated)
- GET /workflow/{submission_id}/current - Current state (authenticated)
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.workflow_transition import WorkflowState
from app.services.workflow_service import (
    InvalidTransitionError,
    PermissionDeniedError,
    SubmissionNotFoundError,
    WorkflowService,
)

router = APIRouter()


# Request/Response schemas
class TransitionRequest(BaseModel):
    """Request schema for workflow state transition."""

    to_state: str = Field(
        ...,
        description="Target workflow state",
        examples=["queued", "assigned", "in_research"],
    )
    reason: Optional[str] = Field(
        None,
        description="Optional reason for the transition",
        max_length=1000,
    )
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Optional metadata to store with the transition",
    )


class TransitionResponse(BaseModel):
    """Response schema for successful transition."""

    id: UUID
    workflow_state: str
    content: str
    requires_peer_review: bool
    peer_review_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class WorkflowHistoryItem(BaseModel):
    """Schema for a single workflow transition history item."""

    id: UUID
    from_state: Optional[str]
    to_state: str
    actor_id: UUID
    reason: Optional[str]
    transition_metadata: Optional[dict[str, Any]] = None
    created_at: str

    model_config = {"from_attributes": True}


class CurrentStateResponse(BaseModel):
    """Response schema for current workflow state."""

    submission_id: UUID
    current_state: str
    valid_transitions: list[str]


def _parse_workflow_state(state_str: str) -> WorkflowState:
    """Parse a string to WorkflowState enum, raising HTTPException if invalid."""
    try:
        return WorkflowState(state_str.lower())
    except ValueError as e:
        valid_states = [s.value for s in WorkflowState]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid workflow state: '{state_str}'. Valid states: {valid_states}",
        ) from e


@router.post(
    "/workflow/{submission_id}/transition",
    response_model=TransitionResponse,
    tags=["workflow"],
    summary="Perform workflow transition",
    description="Transition a submission to a new workflow state. Role-based permissions apply.",
)
async def perform_transition(
    submission_id: UUID,
    request: TransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransitionResponse:
    """
    Perform a workflow state transition.

    Transitions are validated against:
    - Valid state transitions (per ADR 0005 state machine)
    - Role-based permissions
    - Required guards (e.g., peer review for sensitive claims)

    All transitions are logged to workflow_transitions table for audit trail.
    """
    # Parse the target state
    to_state = _parse_workflow_state(request.to_state)

    # Create workflow service
    workflow_service = WorkflowService(db)

    try:
        submission = await workflow_service.transition(
            submission_id=submission_id,
            to_state=to_state,
            actor_id=current_user.id,
            reason=request.reason,
            metadata=request.metadata,
        )

        return TransitionResponse(
            id=submission.id,
            workflow_state=submission.workflow_state.value,
            content=submission.content,
            requires_peer_review=submission.requires_peer_review,
            peer_review_reason=submission.peer_review_reason,
        )

    except SubmissionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e


@router.get(
    "/workflow/{submission_id}/history",
    response_model=list[WorkflowHistoryItem],
    tags=["workflow"],
    summary="Get workflow transition history",
    description="Retrieve the complete transition history for a submission. Authenticated.",
)
async def get_transition_history(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkflowHistoryItem]:
    """
    Get the complete workflow transition history for a submission.

    Returns all transitions ordered by created_at timestamp.
    Provides full audit trail for EFCSN compliance.
    """
    workflow_service = WorkflowService(db)

    # Check if submission exists first
    try:
        await workflow_service.get_current_state(submission_id)
    except SubmissionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    transitions = await workflow_service.get_transition_history(submission_id)

    return [
        WorkflowHistoryItem(
            id=t.id,
            from_state=t.from_state.value if t.from_state else None,
            to_state=t.to_state.value,
            actor_id=t.actor_id,
            reason=t.reason,
            transition_metadata=t.transition_metadata,
            created_at=t.created_at.isoformat(),
        )
        for t in transitions
    ]


@router.get(
    "/workflow/{submission_id}/current",
    response_model=CurrentStateResponse,
    tags=["workflow"],
    summary="Get current workflow state",
    description="Retrieve the current workflow state and valid transitions. Authenticated.",
)
async def get_current_workflow_state(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurrentStateResponse:
    """
    Get the current workflow state for a submission.

    Also returns the list of valid transitions from the current state.
    Useful for UI to show available actions.
    """
    workflow_service = WorkflowService(db)

    try:
        current_state = await workflow_service.get_current_state(submission_id)
    except SubmissionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    # Get valid transitions from current state
    valid_transitions = workflow_service.get_valid_transitions(current_state)

    return CurrentStateResponse(
        submission_id=submission_id,
        current_state=current_state.value,
        valid_transitions=[t.value for t in valid_transitions],
    )
