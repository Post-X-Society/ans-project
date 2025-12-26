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
	| 'privacy-policy';

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
