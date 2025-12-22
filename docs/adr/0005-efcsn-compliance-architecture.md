# ADR 0005: EFCSN Compliance Architecture

## Status
Proposed

## Date
2025-12-21

## Context

AnsCheckt must comply with the European Fact-Checking Standards Network (EFCSN) Code of Standards to achieve and maintain certification. This requires comprehensive organizational transparency, methodological rigor, and robust corrections/complaints handling.

### EFCSN Core Requirements

**Organizational Transparency (>1% or €5,000 funding sources)**
- Legal structure and governance
- Key staff and decision-makers
- Funding sources and amounts
- Editorial independence mechanisms
- Partnership disclosures

**Methodological Transparency**
- Public methodology documentation
- Claim selection criteria
- Rating system definitions
- Evidence standards (minimum 2 sources)
- Source citation requirements

**Operational Standards**
- Minimum 4 original fact-checks published monthly
- Editorial review before publication
- Corrections policy and public log
- Complaints handling with EFCSN escalation
- Multi-editor approval for substantial fact-checks

**Data Protection**
- GDPR compliance
- Minor anonymization
- Source protection
- Right to be forgotten
- 7-year audit log retention

## Decision

We will implement a **multi-tier approval workflow** with comprehensive transparency features and audit trails.

### 1. Rating System Architecture

**Standardized Rating Enum:**
```python
class FactCheckRating(str, Enum):
    TRUE = "true"                      # Completely accurate
    PARTLY_FALSE = "partly_false"      # Mix of true and false
    FALSE = "false"                    # Completely inaccurate
    MISSING_CONTEXT = "missing_context" # True but misleading
    ALTERED = "altered"                # Digitally manipulated
    SATIRE = "satire"                  # Satirical content
    UNVERIFIABLE = "unverifiable"      # Cannot be proven
```

**Rating Metadata:**
- Rating definitions table (multilingual)
- Visual indicator specifications (colors, icons)
- Rating history for versioning
- Required editorial justification for rating changes

### 2. Workflow State Machine

```
┌─────────────┐
│  SUBMITTED  │ (Public submission)
└──────┬──────┘
       │
       ├→ DUPLICATE_DETECTED → ARCHIVED
       │
       ↓
┌─────────────┐
│   QUEUED    │ (Awaiting assignment)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  ASSIGNED   │ (Reviewer assigned)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│IN_RESEARCH  │ (Reviewer collecting evidence)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│DRAFT_READY  │ (Reviewer submits draft)
└──────┬──────┘
       │
       ├→ NEEDS_MORE_RESEARCH (Admin feedback)
       │        ↓
       │   [Returns to IN_RESEARCH]
       │
       ↓
┌─────────────┐
│ADMIN_REVIEW │ (Admin evaluating)
└──────┬──────┘
       │
       ├→ REJECTED → ARCHIVED
       │
       ↓
┌─────────────┐
│PEER_REVIEW  │ (2+ editors review for substantial claims)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│FINAL_APPROVAL│ (Super Admin final check)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  PUBLISHED  │ (Public-facing)
└──────┬──────┘
       │
       └→ CORRECTION_REQUESTED → UNDER_CORRECTION → CORRECTED → PUBLISHED
```

**State Transition Rules:**
- All transitions logged with timestamp, actor, reason
- Certain transitions require minimum evidence count
- Peer review required for: political claims, health/safety claims, claims with >10k views
- Automated notifications on state changes

### 3. Multi-Tier Approval System

**Tier 1: Reviewer (Role: reviewer)**
- Claim assignment
- Evidence collection (minimum 2 sources required)
- Draft rating suggestion
- Internal reasoning documentation
- Cannot self-publish

**Tier 2: Admin (Role: admin)**
- Review drafts
- Request additional research
- Modify evidence/rating
- Approve for publication (standard claims)
- Escalate to peer review (substantial claims)

**Tier 3: Peer Review Panel (Role: admin, 2+ required)**
- Triggered for:
  - Political/controversial claims
  - Health/safety misinformation
  - Claims with potential legal implications
  - Claims exceeding engagement threshold
- Consensus required (all must approve)
- Documented deliberation

**Tier 4: Super Admin (Role: super_admin)**
- Final approval after peer review
- Override authority (with justification)
- Access to full audit trail
- Can unpublish/retract

### 4. Evidence & Source Management

**Source Requirements:**
- Minimum 2 sources per fact-check
- At least 1 primary source preferred
- Each source categorized: supports/contradicts/contextualizes
- Source credibility assessment (1-5 scale)
- Archive snapshots for reproducibility

**Evidence Database Schema:**
```python
class Source:
    id: UUID
    fact_check_id: UUID
    type: Enum[PRIMARY, SECONDARY, EXPERT, MEDIA, GOVERNMENT, ACADEMIC]
    title: str
    url: str
    publication_date: datetime
    access_date: datetime
    credibility_score: int  # 1-5
    relevance: Enum[SUPPORTS, CONTRADICTS, CONTEXTUALIZES]
    archived_url: str  # Wayback Machine or local snapshot
    notes: str
```

**Citation Display:**
- Numbered inline citations [1], [2]
- Footnote-style source list at bottom
- Click to expand full source metadata
- Visual indicators for source quality

### 5. Corrections & Complaints System

**Correction Categories:**

**Minor Corrections** (no public notice required):
- Typos, grammar
- Broken links
- Formatting issues
- Applied immediately, logged internally

**Update Corrections** (appended note):
- New information emerges
- Additional sources found
- Clarifying details added
- Format: "Update (YYYY-MM-DD): [explanation]"

**Substantial Corrections** (prominent notice):
- Rating change
- Major factual error
- Methodology flaw
- Format: Full correction notice at top of fact-check

**Corrections Workflow:**
```
Correction Request → Triage → Investigation → Decision
                                                  ├→ Accepted → Apply Correction → Notify Submitter
                                                  └→ Rejected → Explain Reason → Archive
```

**Public Corrections Log:**
- All substantial corrections public (last 2 years minimum)
- Linked from original fact-check
- RSS feed for transparency
- Monthly corrections summary

**EFCSN Escalation:**
- Prominent link on corrections policy page
- Unresolved complaints can be escalated to EFCSN
- EFCSN complaint form embedded/linked

### 6. Transparency Pages Architecture

**Content Management:**
- Separate `transparency_pages` table
- Versioned content (all changes tracked)
- Multilingual support (EN, NL)
- Annual review prompts (automated notifications)

**Required Pages:**
```
/about/methodology          # Fact-checking process
/about/organization         # Legal structure, governance
/about/team                 # Key staff with backgrounds
/about/funding              # All sources >1% or €5k
/about/partnerships         # Platform and org partnerships
/policies/corrections       # How to request corrections
/policies/privacy           # GDPR, data handling
/corrections-log            # Public corrections archive
```

**Database Schema:**
```python
class TransparencyPage:
    id: UUID
    slug: str  # e.g., "methodology"
    title: dict[str, str]  # {"en": "...", "nl": "..."}
    content: dict[str, str]  # Multilingual markdown
    version: int
    last_reviewed: datetime
    next_review_due: datetime  # Annual reminder
    change_log: list[dict]  # [{date, editor, change_summary}]
```

### 7. Analytics & Compliance Dashboard

**Internal Metrics:**
- Fact-checks published per month (EFCSN requires 4+)
- Average time-to-publication
- Rating distribution
- Source quality scores
- Correction rate
- Workflow bottlenecks

**EFCSN Compliance Checklist:**
- [ ] 4+ fact-checks this month
- [ ] All transparency pages updated (annual)
- [ ] Funding disclosure current
- [ ] Corrections policy accessible
- [ ] Methodology documented
- [ ] Staff information public

**Public Reporting:**
- Monthly transparency reports (auto-generated)
- Annual impact reports
- Corrections statistics
- Engagement metrics

### 8. GDPR & Data Retention

**Personal Data Handling:**
- Submitter information: Optional, encrypted, 90-day retention unless claim published
- Contact info: Hashed for duplicate detection, not displayed publicly
- Minor protection: Automatic anonymization for users <18
- Right to be forgotten: Automated data deletion workflow

**Retention Policies:**
- Fact-checks: Indefinite (public interest)
- Audit logs: 7 years (legal compliance)
- Draft evidence: 2 years after publication
- Rejected claims: 1 year
- Correction requests: 3 years

**SMTP Email System:**
- Environment variable configuration (.env)
- Transactional emails:
  - Claim submission acknowledgment
  - Status update notifications
  - Correction request confirmations
  - Workflow assignment alerts
- Email templates (multilingual)
- Opt-out mechanism

## Database Schema Extensions

### New Tables Required

**1. fact_check_ratings**
```sql
CREATE TABLE fact_check_ratings (
    id UUID PRIMARY KEY,
    fact_check_id UUID REFERENCES fact_checks(id),
    rating VARCHAR(50) NOT NULL,  -- Enum value
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP NOT NULL,
    justification TEXT NOT NULL,
    version INTEGER NOT NULL,
    is_current BOOLEAN DEFAULT TRUE
);
```

**2. sources**
```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY,
    fact_check_id UUID REFERENCES fact_checks(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    url TEXT,
    publication_date DATE,
    access_date DATE NOT NULL,
    credibility_score INTEGER CHECK (credibility_score BETWEEN 1 AND 5),
    relevance VARCHAR(50),  -- supports/contradicts/contextualizes
    archived_url TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**3. corrections**
```sql
CREATE TABLE corrections (
    id UUID PRIMARY KEY,
    fact_check_id UUID REFERENCES fact_checks(id),
    correction_type VARCHAR(50),  -- minor/update/substantial
    requested_by_email VARCHAR(255),
    requested_at TIMESTAMP NOT NULL,
    request_details TEXT NOT NULL,
    status VARCHAR(50),  -- pending/accepted/rejected
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    resolution_notes TEXT,
    applied_at TIMESTAMP
);
```

**4. workflow_transitions**
```sql
CREATE TABLE workflow_transitions (
    id UUID PRIMARY KEY,
    submission_id UUID REFERENCES submissions(id),
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,
    transitioned_by UUID REFERENCES users(id),
    transitioned_at TIMESTAMP DEFAULT NOW(),
    reason TEXT,
    metadata JSONB  -- Additional context
);
```

**5. transparency_pages**
```sql
CREATE TABLE transparency_pages (
    id UUID PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,
    title JSONB NOT NULL,  -- {"en": "...", "nl": "..."}
    content JSONB NOT NULL,  -- {"en": "...", "nl": "..."}
    version INTEGER NOT NULL,
    last_reviewed TIMESTAMP,
    next_review_due TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transparency_page_versions (
    id UUID PRIMARY KEY,
    page_id UUID REFERENCES transparency_pages(id),
    version INTEGER NOT NULL,
    content JSONB NOT NULL,
    changed_by UUID REFERENCES users(id),
    change_summary TEXT,
    changed_at TIMESTAMP DEFAULT NOW()
);
```

**6. peer_reviews**
```sql
CREATE TABLE peer_reviews (
    id UUID PRIMARY KEY,
    fact_check_id UUID REFERENCES fact_checks(id),
    reviewer_id UUID REFERENCES users(id),
    approved BOOLEAN,
    comments TEXT,
    reviewed_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fact_check_id, reviewer_id)
);
```

**7. analytics_events**
```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(50),  -- view, share, correction_request, etc.
    entity_type VARCHAR(50),  -- fact_check, submission, etc.
    entity_id UUID,
    metadata JSONB,
    occurred_at TIMESTAMP DEFAULT NOW()
);
```

**8. email_templates**
```sql
CREATE TABLE email_templates (
    id UUID PRIMARY KEY,
    template_key VARCHAR(100) UNIQUE NOT NULL,
    subject JSONB NOT NULL,  -- {"en": "...", "nl": "..."}
    body_html JSONB NOT NULL,
    body_text JSONB NOT NULL,
    variables JSONB,  -- Available placeholders
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Extended Existing Tables

**submissions table updates:**
```sql
ALTER TABLE submissions
    ADD COLUMN submitter_email VARCHAR(255),
    ADD COLUMN submitter_email_hash VARCHAR(64),  -- For duplicate detection
    ADD COLUMN snapchat_url TEXT,
    ADD COLUMN priority INTEGER DEFAULT 0,
    ADD COLUMN is_duplicate BOOLEAN DEFAULT FALSE,
    ADD COLUMN duplicate_of UUID REFERENCES submissions(id),
    ADD COLUMN engagement_count INTEGER DEFAULT 0,
    ADD COLUMN requires_peer_review BOOLEAN DEFAULT FALSE;
```

**fact_checks table updates:**
```sql
ALTER TABLE fact_checks
    ADD COLUMN current_rating_id UUID REFERENCES fact_check_ratings(id),
    ADD COLUMN sources_count INTEGER DEFAULT 0,
    ADD COLUMN correction_count INTEGER DEFAULT 0,
    ADD COLUMN published_at TIMESTAMP,
    ADD COLUMN retracted BOOLEAN DEFAULT FALSE,
    ADD COLUMN retraction_reason TEXT;
```

## Technical Implementation Requirements

### 1. State Machine Implementation
- Use Python `transitions` library or similar
- Database-backed state storage
- Event-driven state transitions
- Rollback capability for testing

### 2. Email Service
- Integration with SMTP provider (configurable)
- Queue-based sending (Celery + Redis)
- Template rendering engine (Jinja2)
- Multilingual support
- Delivery tracking

### 3. Analytics Service
- Time-series data for compliance metrics
- Real-time dashboard (WebSocket updates)
- Exportable reports (PDF, CSV)
- Automated monthly summaries

### 4. Audit Logging
- Immutable audit trail
- Searchable/filterable logs
- Role-based access to logs
- Compliance report generation

### 5. Document Versioning
- Git-like version control for fact-checks
- Diff visualization
- Revert capability
- Attribution tracking

## API Endpoints Required

```
POST   /api/v1/submissions/public           # Public claim submission
GET    /api/v1/submissions/{id}/timeline     # Audit trail view

POST   /api/v1/fact-checks/{id}/sources     # Add source
GET    /api/v1/fact-checks/{id}/sources     # List sources

POST   /api/v1/fact-checks/{id}/rating      # Assign rating (versioned)
GET    /api/v1/fact-checks/{id}/ratings     # Rating history

POST   /api/v1/corrections                  # Submit correction request
GET    /api/v1/corrections                  # Admin: list requests
PATCH  /api/v1/corrections/{id}             # Process correction

GET    /api/v1/transparency/{slug}          # Get page (multilingual)
PATCH  /api/v1/transparency/{slug}          # Update page (admin)

GET    /api/v1/analytics/compliance         # EFCSN metrics dashboard
GET    /api/v1/analytics/monthly-report     # Auto-generated report

POST   /api/v1/workflow/{submission_id}/transition  # State change
GET    /api/v1/workflow/{submission_id}/history     # Full timeline

POST   /api/v1/peer-review/{fact_check_id}  # Submit peer review
GET    /api/v1/peer-review/{fact_check_id}  # Get review status
```

## Consequences

### Positive
✅ **EFCSN Certification Ready**: Meets all Code of Standards requirements
✅ **Comprehensive Audit Trail**: Every action logged and traceable
✅ **Editorial Quality**: Multi-tier approval ensures accuracy
✅ **Public Accountability**: Transparent corrections and methodology
✅ **Legal Compliance**: GDPR, data retention, minor protection
✅ **Scalability**: Queue-based workflow supports growth
✅ **Multilingual**: Dutch and English throughout

### Negative
⚠️ **Complexity**: Significantly more complex than basic fact-checking
⚠️ **Performance**: Multiple approval tiers may slow publication
⚠️ **Storage**: Audit logs and versioning increase database size
⚠️ **Maintenance**: Transparency pages require annual reviews
⚠️ **SMTP Dependency**: Email system adds external dependency

### Mitigations
- **Complexity**: Comprehensive documentation and agent coordination
- **Performance**: Automated workflows, parallel peer reviews
- **Storage**: Archival strategy, log compression
- **Maintenance**: Automated review reminders
- **SMTP**: Graceful degradation if email unavailable

## Alternatives Considered

### 1. Single-Tier Approval
- **Rejected**: Doesn't meet EFCSN editorial review requirement
- **Risk**: Lower quality, potential bias

### 2. External Corrections Platform
- **Rejected**: EFCSN requires integrated corrections system
- **Risk**: Loss of control, poor UX

### 3. Manual Transparency Updates
- **Rejected**: Too error-prone, compliance risk
- **Selected**: Database-driven with automated reminders

## Next Steps

1. Create database migrations for new schema
2. Implement state machine for workflow
3. Build rating system with versioning
4. Create transparency page CMS
5. Implement corrections workflow
6. Build compliance dashboard
7. Setup email service with templates
8. Implement audit logging system

## References

- [EFCSN Code of Standards](https://efcsn.com/code-of-standards/)
- [GDPR Compliance Guide](https://gdpr.eu/)
- [Python Transitions Library](https://github.com/pytransitions/transitions)
- [ADR 0003: Code Quality](./0003-code-quality-and-pre-commit-workflow.md)
- [ADR 0004: Multilingual Support](./0004-multilingual-text-files.md)

## Author
System Architect (Claude) + Product Owner

## Related EPICs
- EPIC #6: EFCSN Rating System
- EPIC #7: Multi-Tier Approval Workflow
- EPIC #8: Evidence & Source Management
- EPIC #9: Corrections & Complaints System
- EPIC #10: Transparency & Methodology Pages
- EPIC #11: Analytics & Compliance Dashboard
- EPIC #12: GDPR & Data Retention
