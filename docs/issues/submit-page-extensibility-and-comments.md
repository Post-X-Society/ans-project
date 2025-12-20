# Submit Page: Add extensible URL type support and user comment field

**Issue Title**: Submit Page: Add extensible URL type support and user comment field

**Labels**: `enhancement`, `frontend`, `backend`, `architecture`

---

## System Architect Analysis

### Current State

The submit page currently only supports Snapchat Spotlight URLs. After reviewing the architecture, I've identified both **flexibility concerns** and a **missing feature**.

### Architecture Review

#### Backend (`backend/app/`)
- **Submission model** has a generic `submission_type` field supporting `"text"`, `"image"`, `"video"`, `"spotlight"`
- **Generic endpoint** `POST /submissions` accepts `type: Literal["text", "image", "url"]`
- **Spotlight-specific endpoint** `POST /submissions/spotlight` is tightly coupled to Snapchat

#### Frontend (`frontend/src/routes/submit/`)
- `SubmissionForm.svelte` has **hardcoded Snapchat URL validation** (lines 26-29):
  ```javascript
  if (!url.hostname.includes('snapchat.com') || !url.pathname.includes('spotlight')) {
      errors.link = 'Please enter a valid Snapchat Spotlight link';
      return false;
  }
  ```
- Only calls `createSpotlightSubmission()` which hits the Spotlight-specific endpoint

---

## Issue 1: Lack of Flexibility for Future URL Types ❌

### Problem
The current architecture is **not ready for other URL types** (TikTok, YouTube, Instagram, etc.):

1. **Frontend**: Hardcoded Snapchat validation logic
2. **Backend**: Spotlight-specific endpoint with no abstraction
3. **Schemas**: `SpotlightSubmissionCreate` only has `spotlight_link` field
4. **Services**: `snapchat_service` is platform-specific

### Recommended Solution
Implement a **Platform Registry Pattern**:

1. **URL Type Detection Service**
   ```python
   class UrlTypeDetector:
       def detect(self, url: str) -> PlatformType:
           """Returns 'snapchat_spotlight', 'tiktok', 'youtube', etc."""
   ```

2. **Common Platform Handler Interface**
   ```python
   class PlatformHandler(Protocol):
       async def fetch_metadata(self, url: str) -> dict
       async def download_content(self, url: str, content_id: str) -> str
       def parse_metadata(self, raw: dict) -> ContentMetadata
   ```

3. **Platform Registry**
   ```python
   platform_registry = {
       "snapchat_spotlight": SnapchatHandler(),
       "tiktok": TikTokHandler(),  # Future
       "youtube": YouTubeHandler(),  # Future
   }
   ```

4. **Unified Endpoint**
   ```python
   @router.post("/url")
   async def submit_url(url: str, comment: Optional[str] = None):
       platform = url_detector.detect(url)
       handler = platform_registry[platform]
       # ... process with appropriate handler
   ```

5. **Frontend Abstraction**
   - Remove hardcoded Snapchat validation
   - Use backend validation to determine URL type
   - Display appropriate UI based on detected platform

---

## Issue 2: Missing User Comment Field ❌

### Problem
Users cannot provide context about **why** they're submitting content for fact-checking. This is critical for:
- Explaining specific concerns
- Highlighting which claims need verification
- Providing additional context or sources

### Current Schema (no comment field):
```python
class SpotlightSubmissionCreate(BaseModel):
    spotlight_link: str = Field(..., description="Full Snapchat Spotlight URL")
    # No comment field!
```

### Recommended Solution

1. **Add to schemas**:
   ```python
   class SpotlightSubmissionCreate(BaseModel):
       spotlight_link: str = Field(..., description="Full Snapchat Spotlight URL")
       user_comment: Optional[str] = Field(
           None,
           max_length=2000,
           description="Optional comment explaining why this content should be fact-checked"
       )
   ```

2. **Add to Submission model**:
   ```python
   user_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
   ```

3. **Add to frontend SubmissionForm.svelte**:
   ```svelte
   <textarea
       id="user-comment"
       bind:value={userComment}
       placeholder="Why should this content be fact-checked? What specific claims concern you?"
       rows="4"
   />
   ```

---

## Implementation Tasks

### Phase 1: Add User Comment Field (Quick Win)
- [ ] Add `user_comment` column to `submissions` table (migration)
- [ ] Update `SpotlightSubmissionCreate` schema
- [ ] Update `SubmissionForm.svelte` with textarea
- [ ] Update `create_spotlight_submission` endpoint
- [ ] Update tests

### Phase 2: Extensible URL Architecture (Future)
- [ ] Create `UrlTypeDetector` service
- [ ] Define `PlatformHandler` protocol
- [ ] Create platform registry
- [ ] Refactor Snapchat to use registry pattern
- [ ] Create unified `/submissions/url` endpoint
- [ ] Update frontend to use URL type detection

---

## Files Affected

### Phase 1 (Comment Field)
- `backend/app/schemas/spotlight.py`
- `backend/app/models/submission.py`
- `backend/app/api/v1/endpoints/submissions.py`
- `frontend/src/lib/components/SubmissionForm.svelte`
- `backend/alembic/versions/` (new migration)

### Phase 2 (Extensibility)
- `backend/app/services/` (new platform handlers)
- `backend/app/core/` (URL detection)
- `frontend/src/lib/api/` (updated API calls)

---

## Priority

**Phase 1 (Comment Field)**: High - Quick win with immediate user value
**Phase 2 (Extensibility)**: Medium - Future-proofing for platform expansion
