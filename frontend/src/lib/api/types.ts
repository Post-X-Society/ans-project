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
