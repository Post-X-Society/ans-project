# Phase 3: Claim Extraction and Submission with Authentication

## Overview

Phase 3 implements the claim extraction and submission workflow, integrating with the RBAC system from Phase 2. Users can submit content, which is then processed to extract verifiable claims for fact-checking.

## Architecture

### Data Flow

```
User Submission → Claim Extraction → Embedding Generation → Fact-Checking Queue
     ↓                    ↓                    ↓                       ↓
 Submission          Claim(s)            Vector DB          FactCheck Job
```

### Models

1. **Submission** (existing)
   - User-submitted content
   - Type: text, image, url
   - Status: pending, processing, completed, failed

2. **Claim** (existing)
   - Extracted verifiable claims
   - Source reference
   - Vector embedding for similarity search

3. **Submission-Claim Link** (new)
   - Many-to-many relationship
   - One submission can contain multiple claims
   - One claim can appear in multiple submissions

## API Endpoints

### POST /api/v1/submissions (authenticated)
Submit content for fact-checking.

**Authentication**: Required (any authenticated user)
**Rate Limit**: 10 per minute per user

**Request**:
```json
{
  "content": "The earth is flat and vaccines cause autism",
  "type": "text"
}
```

**Response** (201):
```json
{
  "submission_id": "uuid",
  "status": "processing",
  "extracted_claims_count": 2,
  "claims": [
    {
      "claim_id": "uuid",
      "content": "The earth is flat",
      "confidence": 0.95
    },
    {
      "claim_id": "uuid",
      "content": "Vaccines cause autism",
      "confidence": 0.92
    }
  ],
  "created_at": "2025-12-17T10:00:00Z"
}
```

### GET /api/v1/submissions/:id/claims (authenticated)
Get all claims extracted from a submission.

**Authentication**: Required (submission owner or admin+)

### POST /api/v1/claims/:id/fact-check (reviewer+)
Trigger fact-checking for a specific claim.

**Authentication**: Required (REVIEWER, ADMIN, or SUPER_ADMIN)

## Implementation Plan

### Step 1: Database Schema Updates
- [ ] Add submission_claims junction table
- [ ] Add migration for new relationships

### Step 2: Schemas (Pydantic)
- [ ] ClaimCreate
- [ ] ClaimResponse
- [ ] ClaimExtractResponse (with confidence)
- [ ] SubmissionWithClaimsResponse

### Step 3: Services
- [ ] claim_extraction_service.py
  - extract_claims(content: str) -> List[Claim]
  - Uses OpenAI GPT-4 for claim extraction
- [ ] embedding_service.py
  - generate_embedding(text: str) -> List[float]
  - Uses OpenAI text-embedding-3-small

### Step 4: Updated Submission Flow
1. User submits content (authenticated)
2. Create Submission record
3. Extract claims using AI
4. Generate embeddings for each claim
5. Store claims with embeddings
6. Link claims to submission
7. Return response with claims

### Step 5: Endpoints
- [ ] Update POST /api/v1/submissions to include claim extraction
- [ ] Add GET /api/v1/submissions/:id/claims
- [ ] Add POST /api/v1/claims/:id/fact-check

### Step 6: Tests (TDD)
- [ ] Test claim extraction with various inputs
- [ ] Test submission with authentication
- [ ] Test rate limiting
- [ ] Test claim-submission relationships
- [ ] Test permission checks (owner/admin access)

## Security Considerations

1. **Authentication Required**: All submission endpoints require JWT
2. **Rate Limiting**: Prevent abuse (10 submissions per minute)
3. **Content Validation**:
   - Max length: 5000 characters
   - Min length: 10 characters
   - Sanitize input
4. **Access Control**:
   - Users can only view their own submissions
   - Admins can view all submissions
   - Reviewers can trigger fact-checking

## OpenAI Integration

### Claim Extraction Prompt
```
Extract all verifiable factual claims from the following text.
Return only claims that can be fact-checked against reliable sources.
Ignore opinions, questions, and non-factual statements.

Text: {content}

Return a JSON array of objects with:
- content: the claim text
- confidence: 0.0-1.0 indicating how confident you are this is a factual claim
```

### Embedding Generation
```python
import openai
response = openai.Embedding.create(
    model="text-embedding-3-small",
    input=claim_content
)
embedding = response['data'][0]['embedding']  # List[float] of length 1536
```

## Testing Strategy

1. **Unit Tests**
   - Claim extraction logic
   - Embedding generation
   - Validation logic

2. **Integration Tests**
   - Full submission flow
   - Database relationships
   - API endpoint behavior

3. **Auth Tests**
   - Unauthenticated access denied
   - Rate limiting enforcement
   - Permission checks

## Success Criteria

- [ ] Users can submit content and get extracted claims
- [ ] Claims are stored with embeddings
- [ ] All endpoints require proper authentication
- [ ] 80%+ test coverage maintained
- [ ] All tests passing
- [ ] API documentation updated

## Future Enhancements (Phase 4+)

- Asynchronous processing with Celery/RQ
- Similar claim detection using vector search
- Claim deduplication
- Bulk submission support
- Webhook notifications for completed fact-checks
