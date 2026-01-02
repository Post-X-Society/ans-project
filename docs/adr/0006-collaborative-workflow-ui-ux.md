# ADR 0006: Collaborative Workflow UI/UX Architecture

**Status:** Accepted
**Date:** 2026-01-02
**Deciders:** System Architect, Frontend Developer
**Related ADRs:** [ADR 0005: EFCSN Compliance Architecture](./0005-efcsn-compliance-architecture.md)

## Context

While implementing the EFCSN compliance workflow system (ADR 0005), we discovered that the existing submission management infrastructure (issues #27-32, #121) provides the database models, API endpoints, and basic UI components, but lacks the collaborative workflow UI/UX layer needed for transparent, team-based fact-checking operations.

**User Requirements:**
- All reviewers and admins must see all submissions (shared visibility)
- Reviewers should be able to voluntarily pick up submissions (self-assignment)
- Admins retain the privilege to manually assign submissions to specific reviewers
- Multiple reviewers can be assigned to a single submission simultaneously
- Personal dashboards should provide role-filtered views of relevant work
- Admin approval dashboards are needed for the multi-tier workflow

**Existing Implementation (80% Complete):**
- ✅ Many-to-many `submission_reviewers` table (#28)
- ✅ Backend API endpoints for reviewer assignment (#29)
- ✅ `GET /submissions` with `assigned_to_me` filter parameter (#30)
- ✅ Frontend submissions overview page at `/submissions` (#31)
- ✅ Reviewer assignment modal with multi-select (#32)
- ✅ Submission detail page with workflow timeline, ratings (#121)
- ✅ Peer review system (database, backend, dashboard) (#63-67)

**Missing Capabilities:**
- ❌ Self-assignment mechanism (no "Pick Up" button)
- ❌ Filter tabs for "All", "My Assignments", "Unassigned", "Pending Review"
- ❌ Personal dashboards for reviewers showing their assignments
- ❌ Admin approval dashboard filtering by workflow state
- ❌ Visual indicators for assignment status on submission cards
- ❌ Sources tab integration into submission detail page

## Decision

We will implement a **transparent, collaborative workflow UI/UX layer** that builds upon the existing infrastructure with the following architectural decisions:

### 1. Self-Assignment Pattern

**Backend API:**
```http
POST /api/v1/submissions/{submission_id}/reviewers/me
Authorization: Bearer {token}
```

**Behavior:**
- Validates user has `REVIEWER`, `ADMIN`, or `SUPER_ADMIN` role
- Checks if user is already assigned (idempotent operation)
- Auto-assigns current authenticated user to the submission
- Returns 201 Created or 200 OK (if already assigned)

**Frontend UI:**
- "Assign to Me" button on `SubmissionCard` component
- Button visible only if:
  - User has reviewer+ role
  - User is NOT already assigned to this submission
- Disabled state shows "Assigned to you" badge when user is already assigned
- Unassigned submissions show visual indicator (orange "Unassigned" badge)

### 2. Shared Visibility with Smart Filters

**Submissions Overview Page (`/submissions`):**

All users with `REVIEWER`, `ADMIN`, or `SUPER_ADMIN` roles see **all submissions** by default (shared transparency), with filter tabs for navigation:

**Filter Tabs:**
1. **"All Submissions"** (default)
   - Shows all submissions without filtering
   - No API filter parameter

2. **"My Assignments"**
   - Uses existing `assigned_to_me=true` API parameter
   - Server-side filter for optimal performance

3. **"Unassigned"**
   - Client-side filter: `submissions.filter(s => s.reviewers.length === 0)`
   - Shows submissions available for self-assignment

4. **"Pending Review"**
   - Client-side filter: assigned to me AND workflow state in reviewable states
   - States: `ASSIGNED`, `IN_RESEARCH`, `DRAFT_READY`, `ADMIN_REVIEW`, `PEER_REVIEW`

**URL State Management:**
- Selected tab persisted in query parameter: `/submissions?tab=my-assignments`
- Enables deep linking and browser back/forward navigation

### 3. Personal Dashboards (Role-Specific Views)

**Reviewer Dashboard (`/dashboard/reviewer`):**

Role: `REVIEWER`, `ADMIN`, `SUPER_ADMIN`

**Sections:**
1. **"My Active Assignments"**
   - Uses `GET /submissions?assigned_to_me=true&status=processing`
   - Shows submissions assigned to current user, not yet published
   - Quick action: "Start Review" → navigate to `/submissions/{id}`

2. **"Pending Peer Reviews"**
   - Uses existing peer review API: `GET /api/v1/peer-reviews/pending`
   - Shows fact-checks awaiting peer review from current user
   - Quick action: "Review Now" → navigate to peer review page

3. **"Recently Completed"**
   - Uses `GET /submissions?assigned_to_me=true&status=completed&limit=10`
   - Shows last 10 submissions completed by current user
   - Read-only, informational

**Admin Approval Dashboard (`/dashboard/admin`):**

Role: `ADMIN`, `SUPER_ADMIN`

**Sections:**
1. **"Pending Admin Review"**
   - Client-side filter: `workflow_state === 'ADMIN_REVIEW'`
   - Shows submissions awaiting admin approval
   - Quick actions: "Approve", "Request Changes", "Reject"

2. **"Pending Final Approval"** (SUPER_ADMIN only)
   - Client-side filter: `workflow_state === 'FINAL_APPROVAL'`
   - Shows submissions awaiting super admin final approval after peer review
   - Quick actions: "Publish", "Send Back to Peer Review"

3. **"Reviewer Workload"**
   - Aggregates submissions by assigned reviewer: `reviewers.reduce((acc, r) => ...)`
   - Shows count of pending submissions per reviewer
   - Enables load balancing decisions
   - Visual: Bar chart or table with reviewer names and counts

### 4. Submission Detail Page Tabs

**Current State:** Single-page view with sections
**Enhancement:** Tab-based navigation for better organization

**Tab Structure (`/submissions/[id]`):**

1. **"Overview"** (default)
   - Submission content, metadata, submitter info
   - Workflow timeline component
   - Current rating display
   - Assigned reviewers list

2. **"Rating & Review"**
   - Rating assignment form (if user has permission)
   - Rating history with versions
   - Workflow state transition controls

3. **"Sources"** (blocked by #73)
   - Source management interface component
   - List of sources with credibility scores
   - Add/edit/archive sources
   - Link sources to specific claims
   - Show archival status (Wayback Machine)

4. **"Peer Reviews"** (when peer review triggered)
   - Peer review timeline (issue #68)
   - List of peer reviewers and their decisions
   - Deliberation comments
   - Consensus status indicator

### 5. Multi-Reviewer Visual Indicators

**SubmissionCard Component Enhancement:**

**Badge System:**
- **Unassigned:** Gray badge "Unassigned" when `reviewers.length === 0`
- **Assigned:** Blue badge showing count: "3 reviewers" when `reviewers.length > 0`
- **In Progress:** Yellow badge when workflow state is `IN_RESEARCH` or `DRAFT_READY`
- **Completed:** Green badge when workflow state is `PUBLISHED`

**Reviewer Avatars:**
- Show first 3 assigned reviewers as circular avatars with initials
- If more than 3: show "+N" indicator (e.g., "+2 more")
- Tooltip on hover: full list of reviewer names

**Color Coding:**
```css
/* Status colors */
--status-unassigned: #6B7280;    /* Gray */
--status-assigned: #3B82F6;      /* Blue */
--status-in-progress: #F59E0B;   /* Yellow */
--status-completed: #10B981;     /* Green */
--status-peer-review: #8B5CF6;   /* Purple */
--status-rejected: #EF4444;      /* Red */
```

### 6. Architecture Principles

**Separation of Concerns:**
- **Shared Visibility:** API returns all submissions to privileged roles
- **Personal Context:** UI adds client-side indicators (`is_assigned_to_me` flag)
- **Smart Filtering:** Server-side for performance, client-side for UX flexibility

**Progressive Disclosure:**
- Overview page: High-level cards with status indicators
- Detail page: Full information with tab-based organization
- Dashboards: Role-specific filtered views for focused work

**Collaborative Transparency:**
- No isolated "My Queue" that hides work from other team members
- All reviewers can see who's working on what
- Self-assignment enables voluntary workload distribution
- Admin assignment enables directed tasking when needed

## Consequences

### Positive

1. **Collaborative Culture:** Shared visibility fosters teamwork and knowledge sharing
2. **Flexible Workload Distribution:** Self-assignment empowers reviewers, admin assignment enables load balancing
3. **Clear Status Indicators:** Visual badges reduce cognitive load, improve workflow awareness
4. **Role-Appropriate Dashboards:** Focused views reduce noise, improve productivity
5. **Scalability:** Multiple reviewers per submission enables parallel work on complex claims
6. **Existing Infrastructure Reuse:** 80% of backend/database work already complete

### Negative

1. **Increased UI Complexity:** Tab navigation and multiple dashboards require more frontend code
2. **Client-Side Filtering:** Some filters require fetching all submissions, may not scale beyond 1000s
3. **Coordination Overhead:** Multiple reviewers on one submission requires communication

### Mitigation Strategies

**Scalability:**
- Implement pagination for submissions list (already exists: `page_size=50`)
- Add server-side filtering for workflow states if client-side filtering becomes slow
- Consider virtual scrolling for very long lists

**Coordination:**
- Add internal comments/notes system for reviewers to communicate (future enhancement)
- Show "currently viewing" indicators for real-time collaboration awareness (future)

## Implementation Plan

### Phase 1: Self-Assignment (Priority 1)
**Issues:** #96 (Backend), #97 (Frontend)
**Effort:** 4-6 hours
**Agents:** Backend Developer (2-3h), Frontend Developer (2-3h)

### Phase 2: Filter Tabs (Priority 1)
**Issue:** #98
**Effort:** 3-4 hours
**Agent:** Frontend Developer

### Phase 3: Personal Dashboards (Priority 2)
**Issues:** #99 (Reviewer Dashboard), #100 (Admin Dashboard)
**Effort:** 14-18 hours
**Agent:** Frontend Developer

### Phase 4: Sources Integration (Priority 1, Blocked)
**Issue:** #101 (blocked by #73)
**Effort:** 4-5 hours
**Agent:** Frontend Developer

### Phase 5: Visual Enhancements (Priority 2)
**Issue:** #102
**Effort:** 3-4 hours
**Agent:** Frontend Developer

### Phase 6: Peer Review Timeline (Priority 3)
**Issue:** #68 (already exists, OPEN)
**Effort:** 3-4 hours
**Agent:** Frontend Developer

**Total Estimated Effort:** 31-41 hours
**Wall-Clock Time:** 2-3 weeks (with parallel work)

## Related Issues

**Existing Infrastructure:**
- #27: [EPIC] Build submissions overview page (OPEN)
- #28: Backend submission-reviewer assignment models (CLOSED)
- #29: Backend reviewer assignment API endpoints (CLOSED)
- #30: Backend submissions list with role-based filtering (CLOSED)
- #31: Frontend submissions overview page UI (CLOSED)
- #32: Frontend reviewer assignment interface (CLOSED)
- #121: Frontend submission detail page (CLOSED)

**Peer Review System:**
- #48: [EPIC] Multi-Tier Approval & Peer Review System (OPEN)
- #63-66: Peer review backend (CLOSED)
- #67: Peer review dashboard (CLOSED)
- #68: Peer review timeline section (OPEN)

**Workflow System:**
- #47: [EPIC] Workflow State Machine & Versioning (OPEN)
- #57: Workflow transitions audit log (CLOSED)
- #59: Workflow state machine implementation (CLOSED)

**New Issues (This ADR):**
- #96: Self-assignment backend endpoint
- #97: Self-assignment frontend UI
- #98: Filter tabs for submissions overview
- #99: Reviewer personal dashboard
- #100: Admin approval dashboard
- #101: Sources tab integration
- #102: Multi-reviewer visual indicators

## References

- [ADR 0005: EFCSN Compliance Architecture](./0005-efcsn-compliance-architecture.md)
- [ADR 0002: Multi-Agent Test-Driven Development Workflow](./0002-multi-agent-tdd-workflow.md)
- [EFCSN Code of Principles](https://efcsn.com/code-of-principles/)
- GitHub Project: [Ans Fact-Checking Platform](https://github.com/Post-X-Society/ans-project)
