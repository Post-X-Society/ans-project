// API Types matching backend schemas

export interface UserBasic {
	id: string;
	email: string;
}

export interface SpotlightContentBasic {
	spotlight_id: string;
	thumbnail_url: string;
	creator_name?: string;
	creator_username?: string;
	view_count?: number;
	duration_ms?: number;
}

export interface Submission {
	id: string;
	content: string;
	submission_type: 'text' | 'image' | 'url' | 'spotlight';
	status: 'pending' | 'processing' | 'completed';
	user_id: string | null;
	created_at: string;
	updated_at: string;
	user?: UserBasic;
	spotlight_content?: SpotlightContentBasic;
	reviewers: UserBasic[];
	/** ID of associated fact-check (if any) */
	fact_check_id?: string;
	/** Whether peer review has been triggered for this submission */
	peer_review_triggered?: boolean;
}

export interface SubmissionCreate {
	content: string;
	type: 'text' | 'image' | 'url';
}

export interface SpotlightSubmissionCreate {
	spotlight_link: string;
}

export interface SpotlightContent {
	id: string;
	submission_id: string;
	spotlight_link: string;
	spotlight_id: string;
	video_url: string;
	video_local_path: string | null;
	thumbnail_url: string;
	duration_ms: number | null;
	width: number | null;
	height: number | null;
	creator_username: string | null;
	creator_name: string | null;
	creator_url: string | null;
	view_count: number | null;
	share_count: number | null;
	comment_count: number | null;
	boost_count: number | null;
	recommend_count: number | null;
	upload_timestamp: number | null;
	raw_metadata: Record<string, any>;
	created_at: string;
	updated_at: string;
}

export interface SubmissionListResponse {
	items: Submission[];
	total: number;
	page: number;
	page_size: number;
	total_pages: number;
}

export interface ApiError {
	detail: string;
}

// Auth Types
export type UserRole = 'super_admin' | 'admin' | 'reviewer' | 'submitter';

export interface User {
	id: string;
	email: string;
	role: UserRole;
	is_active: boolean;
	created_at: string;
	updated_at: string;
}

export interface LoginRequest {
	email: string;
	password: string;
}

export interface RegisterRequest {
	email: string;
	password: string;
}

export interface AuthTokens {
	access_token: string;
	refresh_token: string;
	token_type: string;
}

export interface LoginResponse extends AuthTokens {
	user: User;
}

export interface RefreshRequest {
	refresh_token: string;
}

export interface UserCreate {
	email: string;
	password: string;
	role?: UserRole;
}

export interface UserUpdate {
	role?: UserRole;
	is_active?: boolean;
}

export interface UserListResponse {
	items: User[];
	total: number;
	page: number;
	page_size: number;
	total_pages: number;
}

// Transparency Page Types (Issue #85 - EFCSN Compliance)
export interface TransparencyPage {
	id: string;
	slug: string;
	title: Record<string, string>;
	content: Record<string, string>;
	version: number;
	last_reviewed: string | null;
	next_review_due: string | null;
	created_at: string;
	updated_at: string;
}

export interface TransparencyPageSummary {
	id: string;
	slug: string;
	title: Record<string, string>;
	version: number;
	last_reviewed: string | null;
	next_review_due: string | null;
	updated_at: string;
}

export interface TransparencyPageListResponse {
	items: TransparencyPageSummary[];
	total: number;
}

// Valid transparency page slugs for type safety
export type TransparencyPageSlug =
	| 'methodology'
	| 'organization'
	| 'team'
	| 'funding'
	| 'partnerships'
	| 'corrections-policy'
	| 'privacy-policy'
	| 'terms';

// Transparency page version (for version history)
export interface TransparencyPageVersion {
	id: string;
	page_id: string;
	version: number;
	title: Record<string, string>;
	content: Record<string, string>;
	changed_by_id: string;
	change_summary: string | null;
	created_at: string;
}

// Transparency page diff (for comparing versions)
export interface TransparencyPageDiff {
	slug: string;
	from_version: number;
	to_version: number;
	diff: Record<string, unknown>;
	language: string | null;
}

// Update payload for transparency pages
export interface TransparencyPageUpdate {
	title?: Record<string, string>;
	content?: Record<string, string>;
	change_summary: string;
}

// Rating Types (EFCSN Compliant - Issue #61)
export type FactCheckRatingValue =
	| 'true'
	| 'partly_false'
	| 'false'
	| 'missing_context'
	| 'altered'
	| 'satire'
	| 'unverifiable';

export interface RatingDefinition {
	id: string;
	rating: FactCheckRatingValue;
	name: Record<string, string>;
	description: Record<string, string>;
	color_hex: string;
	icon: string;
	display_order: number;
	created_at: string;
	updated_at: string;
}

export interface RatingDefinitionListResponse {
	items: RatingDefinition[];
	total: number;
}

export interface FactCheckRating {
	id: string;
	fact_check_id: string;
	rating: FactCheckRatingValue;
	justification: string;
	assigned_by_id: string;
	version: number;
	is_current: boolean;
	created_at: string;
}

export interface CurrentRatingResponse {
	rating: FactCheckRating | null;
	definition: RatingDefinition | null;
}

// Workflow Types (EFCSN Compliance - Issue #60, #62)
export type WorkflowState =
	| 'submitted'
	| 'queued'
	| 'duplicate_detected'
	| 'archived'
	| 'assigned'
	| 'in_research'
	| 'draft_ready'
	| 'needs_more_research'
	| 'admin_review'
	| 'peer_review'
	| 'final_approval'
	| 'published'
	| 'under_correction'
	| 'corrected'
	| 'rejected';

export interface WorkflowHistoryItem {
	id: string;
	submission_id: string;
	from_state: WorkflowState | null;
	to_state: WorkflowState;
	transitioned_by_id: string;
	transitioned_by?: UserBasic;
	reason: string | null;
	metadata: Record<string, unknown> | null;
	created_at: string;
}

export interface WorkflowHistoryResponse {
	items: WorkflowHistoryItem[];
	total: number;
	current_state: WorkflowState;
}

export interface WorkflowCurrentStateResponse {
	submission_id: string;
	current_state: WorkflowState;
	valid_transitions: WorkflowState[];
}

export interface WorkflowTransitionRequest {
	to_state: WorkflowState;
	reason?: string;
	metadata?: Record<string, unknown>;
}

// Peer Review Types (EFCSN Compliance - Issue #66, #68)
export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export interface PeerReviewerInfo {
	id: string;
	email: string;
}

export interface PeerReview {
	id: string;
	fact_check_id: string;
	reviewer_id: string;
	reviewer?: PeerReviewerInfo;
	approval_status: ApprovalStatus;
	comments: string | null;
	created_at: string;
	updated_at: string;
}

export interface PeerReviewStatusResponse {
	fact_check_id: string;
	consensus_reached: boolean;
	approved: boolean;
	total_reviews: number;
	approved_count: number;
	rejected_count: number;
	pending_count: number;
	needs_more_reviewers: boolean;
	reviews: PeerReview[];
}

// Draft Types (Issue #122 - Fact-Check Editor Interface)
export interface DraftContent {
	claim_summary: string | null;
	analysis: string | null;
	verdict: FactCheckRatingValue | null;
	justification: string | null;
	sources_cited: string[];
	internal_notes: string | null;
	version: number;
	last_edited_by: string | null;
}

export interface DraftUpdate {
	claim_summary?: string | null;
	analysis?: string | null;
	verdict?: FactCheckRatingValue | null;
	justification?: string | null;
	sources_cited?: string[] | null;
	internal_notes?: string | null;
}

export interface DraftResponse {
	fact_check_id: string;
	draft_content: DraftContent | null;
	draft_updated_at: string | null;
	has_draft: boolean;
}

// Peer Review Types (Issue #66 & #67 - EFCSN Compliance)
export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export interface PeerReview {
	id: string;
	fact_check_id: string;
	reviewer_id: string;
	approval_status: ApprovalStatus;
	comments: string | null;
	created_at: string;
	updated_at: string;
}

export interface PendingReviewItem {
	id: string;
	fact_check_id: string;
	created_at: string;
}

export interface PendingReviewsResponse {
	reviewer_id: string;
	total_count: number;
	reviews: PendingReviewItem[];
}

export interface PeerReviewStatusResponse {
	fact_check_id: string;
	consensus_reached: boolean;
	approved: boolean;
	total_reviews: number;
	approved_count: number;
	rejected_count: number;
	pending_count: number;
	needs_more_reviewers: boolean;
	reviews: PeerReview[];
}

export interface PeerReviewSubmit {
	approved: boolean;
	comments?: string | null;
}

export interface PeerReviewInitiate {
	reviewer_ids: string[];
}

export interface PeerReviewInitiateResponse {
	fact_check_id: string;
	reviews_created: number;
	reviews: PeerReview[];
}

// Extended submission type with fact-check data for dashboard
export interface SubmissionWithFactCheck extends Submission {
	fact_check?: {
		id: string;
		claim_summary: string | null;
		rating: FactCheckRatingValue | null;
		created_at: string;
	} | null;
}

// Source Types (Issue #73 - Source Management Interface)
export type SourceType = 'official' | 'news' | 'social_media' | 'research' | 'other';

export type SourceRelevance = 'supports' | 'contradicts' | 'contextualizes';

export interface Source {
	id: string;
	url: string;
	source_type: SourceType;
	credibility_rating: number; // 1-5
	relevance: SourceRelevance;
	fact_check_id?: string;
	created_at: string;
	updated_at: string;
}

export interface SourceCreate {
	url: string;
	source_type: SourceType;
	credibility_rating: number;
	relevance: SourceRelevance;
}

export interface SourceUpdate {
	url?: string;
	source_type?: SourceType;
	credibility_rating?: number;
	relevance?: SourceRelevance;
}

export interface SourceListResponse {
	items: Source[];
	total: number;
}

// Citation Types (Issue #74 - Citation Display Component)
// Extended source with metadata for proper citation formatting
export interface CitationSource extends Source {
	title?: string;
	author?: string;
	publication_date?: string;
	publisher?: string;
}

export interface CitationFormat {
	apa: string;
	mla: string;
}

// Correction Types (Issue #79 - Correction Request Form)
// EFCSN-compliant corrections system

export type CorrectionType = 'minor' | 'update' | 'substantial';

export type CorrectionStatus = 'pending' | 'accepted' | 'rejected';

export interface CorrectionCreate {
	fact_check_id: string;
	correction_type: CorrectionType;
	request_details: string;
	requester_email?: string;
}

export interface CorrectionResponse {
	id: string;
	fact_check_id: string;
	correction_type: CorrectionType;
	request_details: string;
	requester_email?: string;
	status: CorrectionStatus;
	reviewed_by_id?: string;
	reviewed_at?: string;
	resolution_notes?: string;
	sla_deadline?: string;
	created_at: string;
	updated_at: string;
}

export interface CorrectionSubmitResponse {
	id: string;
	fact_check_id: string;
	correction_type: CorrectionType;
	status: CorrectionStatus;
	requester_email?: string;
	sla_deadline?: string;
	acknowledgment_sent: boolean;
	created_at: string;
}

export interface CorrectionListResponse {
	fact_check_id?: string;
	corrections: CorrectionResponse[];
	total_count: number;
}

// =============================================================================
// Issue #80: Admin Correction Review Dashboard Types
// =============================================================================

/**
 * Response for pending corrections list (admin triage).
 * Includes overdue count for SLA monitoring.
 */
export interface CorrectionPendingListResponse {
	corrections: CorrectionResponse[];
	total_count: number;
	overdue_count: number;
}

/**
 * Response for listing all corrections with pagination (admin).
 */
export interface CorrectionAllListResponse {
	corrections: CorrectionResponse[];
	total_count: number;
	limit: number;
	offset: number;
}

/**
 * Request for reviewing (accepting/rejecting) a correction.
 */
export interface CorrectionReviewRequest {
	resolution_notes: string;
}

/**
 * Request for applying an accepted correction to a fact-check.
 */
export interface CorrectionApplyRequest {
	changes: Record<string, string | number | string[] | null>;
	changes_summary: string;
}

/**
 * Response after successfully applying a correction.
 */
export interface CorrectionApplicationResponse {
	id: string;
	correction_id: string;
	applied_by_id: string;
	version: number;
	applied_at: string;
	changes_summary: string;
	previous_content: Record<string, string | number | string[] | null>;
	new_content: Record<string, string | number | string[] | null>;
	is_current: boolean;
}

/**
 * Response for correction history (version audit trail).
 */
export interface CorrectionHistoryResponse {
	fact_check_id: string;
	applications: CorrectionApplicationResponse[];
	total_versions: number;
}

/**
 * Public log correction response (privacy-aware, no email).
 */
export interface PublicLogCorrectionResponse {
	id: string;
	fact_check_id: string;
	correction_type: CorrectionType;
	request_details: string;
	status: CorrectionStatus;
	reviewed_at?: string;
	resolution_notes?: string;
	created_at: string;
	updated_at: string;
}

/**
 * Public corrections log response.
 */
export interface PublicLogListResponse {
	corrections: PublicLogCorrectionResponse[];
	total_count: number;
}

// =============================================================================
// Issue #167: Email Template Admin Management UI Types
// =============================================================================

/**
 * Email template type enumeration (matches backend EmailTemplateType)
 */
export type EmailTemplateType =
	| 'submission_received'
	| 'reviewer_assigned'
	| 'review_assigned'
	| 'review_completed'
	| 'workflow_update'
	| 'workflow_submitted'
	| 'workflow_queued'
	| 'workflow_assigned'
	| 'workflow_in_research'
	| 'workflow_draft_ready'
	| 'workflow_admin_review'
	| 'workflow_peer_review'
	| 'workflow_final_approval'
	| 'workflow_published'
	| 'workflow_rejected'
	| 'correction_request_received'
	| 'correction_approved'
	| 'correction_rejected'
	| 'correction_resolution'
	| 'peer_review_request'
	| 'peer_review_completed'
	| 'fact_check_published'
	| 'draft_reminder'
	| 'transparency_page_review_reminder'
	| 'system_notification'
	| 'weekly_digest'
	| 'password_reset'
	| 'welcome_email'
	| 'account_verification';

/**
 * Email template response from API
 */
export interface EmailTemplate {
	id: string;
	template_key: string;
	template_type: EmailTemplateType;
	name: Record<string, string>;
	description: Record<string, string>;
	subject: Record<string, string>;
	body_text: Record<string, string>;
	body_html: Record<string, string>;
	variables: Record<string, string>;
	is_active: boolean;
	version: number;
	last_modified_by: string | null;
	notes: string | null;
	created_at: string;
	updated_at: string;
}

/**
 * Request to create a new email template
 */
export interface EmailTemplateCreate {
	template_key: string;
	template_type: EmailTemplateType;
	name: Record<string, string>;
	description: Record<string, string>;
	subject: Record<string, string>;
	body_text: Record<string, string>;
	body_html: Record<string, string>;
	variables: Record<string, string>;
	is_active?: boolean;
	notes?: string;
}

/**
 * Request to update an email template
 */
export interface EmailTemplateUpdate {
	name?: Record<string, string>;
	description?: Record<string, string>;
	subject?: Record<string, string>;
	body_text?: Record<string, string>;
	body_html?: Record<string, string>;
	variables?: Record<string, string>;
	is_active?: boolean;
	notes?: string;
}

/**
 * Request to render/preview a template
 */
export interface EmailTemplateRenderRequest {
	template_key: string;
	context: Record<string, string>;
	language: 'en' | 'nl';
}

/**
 * Response from rendering a template
 */
export interface EmailTemplateRenderResponse {
	subject: string;
	body_text: string;
	body_html: string;
}

// ============================================================================
// RTBF (Right to be Forgotten) Types
// Issue #92: Backend: Right to be Forgotten Workflow (TDD)
// EPIC #53: GDPR & Data Retention Compliance
// ============================================================================

/**
 * RTBF request status
 */
export type RTBFRequestStatus = 'pending' | 'processing' | 'completed' | 'rejected';

/**
 * RTBF Request
 */
export interface RTBFRequest {
	id: string;
	user_id: string;
	reason: string;
	status: RTBFRequestStatus;
	requester_date_of_birth?: string;
	processed_by_id?: string;
	completed_at?: string;
	rejection_reason?: string;
	deletion_summary?: Record<string, number>;
	notification_email?: string;
	created_at: string;
	updated_at: string;
}

/**
 * Request to create an RTBF request
 */
export interface RTBFRequestCreate {
	reason: string;
	date_of_birth?: string;
}

/**
 * Response when listing RTBF requests (admin)
 */
export interface RTBFRequestListResponse {
	items: RTBFRequest[];
	total: number;
	pending_count: number;
	processing_count: number;
}

/**
 * Result from processing an RTBF request
 */
export interface RTBFRequestProcessResult {
	success: boolean;
	request_id: string;
	summary: Record<string, number>;
	message: string;
}

/**
 * User data export response
 */
export interface DataExportResponse {
	user_id: string;
	email: string;
	full_name: string;
	created_at: string;
	submissions: Array<{
		id: string;
		claim_text: string;
		workflow_state: string;
		created_at: string;
	}>;
	corrections: Array<{
		id: string;
		correction_text: string;
		status: string;
		created_at: string;
	}>;
	ratings: Array<{
		id: string;
		rating: number;
		created_at: string;
	}>;
}

/**
 * Summary of user data for deletion preview
 */
export interface UserDataSummary {
	submissions_count: number;
	corrections_count: number;
	ratings_count: number;
	published_submissions_count: number;
}

// =============================================================================
// Analytics & Compliance Dashboard Types
// Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
// EPIC #52: Analytics & Compliance Dashboard
// =============================================================================

/**
 * Monthly fact-check count data point
 */
export interface MonthlyFactCheckCount {
	year: number;
	month: number;
	count: number;
	meets_efcsn_minimum: boolean;
}

/**
 * Response for monthly fact-check counts
 */
export interface MonthlyFactCheckCountResponse {
	months: MonthlyFactCheckCount[];
	total_count: number;
	average_per_month: number;
}

/**
 * Time to publication metrics
 */
export interface TimeToPublicationMetrics {
	average_hours: number;
	median_hours: number;
	min_hours: number;
	max_hours: number;
	total_published: number;
}

/**
 * Rating distribution item
 */
export interface RatingDistributionItem {
	rating: FactCheckRatingValue;
	count: number;
	percentage: number;
}

/**
 * Response for rating distribution
 */
export interface RatingDistributionResponse {
	ratings: RatingDistributionItem[];
	total_count: number;
	period_start: string | null;
	period_end: string | null;
}

/**
 * Source quality metrics for EFCSN compliance
 */
export interface SourceQualityMetrics {
	average_sources_per_fact_check: number;
	average_credibility_score: number;
	official_source_percentage: number;
	fact_checks_with_sources: number;
	total_sources: number;
}

/**
 * Correction rate metrics
 */
export interface CorrectionRateMetrics {
	total_fact_checks: number;
	total_corrections: number;
	corrections_accepted: number;
	corrections_rejected: number;
	corrections_pending: number;
	correction_rate: number;
	corrections_by_type: Record<string, number>;
}

/**
 * EFCSN compliance status enum
 */
export type EFCSNComplianceStatus = 'compliant' | 'at_risk' | 'non_compliant' | 'warning';

/**
 * EFCSN compliance checklist item
 */
export interface EFCSNComplianceChecklistItem {
	id: string;
	requirement: string;
	description: string;
	status: EFCSNComplianceStatus;
	details: string;
	value?: number;
	threshold?: number;
}

/**
 * EFCSN compliance status response
 */
export interface EFCSNComplianceResponse {
	overall_status: EFCSNComplianceStatus;
	compliance_score: number;
	checklist: EFCSNComplianceChecklistItem[];
	last_checked: string;
}

/**
 * Complete analytics dashboard response
 */
export interface AnalyticsDashboardResponse {
	monthly_fact_checks: MonthlyFactCheckCountResponse;
	time_to_publication: TimeToPublicationMetrics;
	rating_distribution: RatingDistributionResponse;
	source_quality: SourceQualityMetrics;
	correction_rate: CorrectionRateMetrics;
	efcsn_compliance: EFCSNComplianceResponse;
	generated_at: string;
}
