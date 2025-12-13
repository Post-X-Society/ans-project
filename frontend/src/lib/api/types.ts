// API Types matching backend schemas

export interface Submission {
	id: string;
	content: string;
	submission_type: 'text' | 'image' | 'url';
	status: 'pending' | 'processing' | 'completed';
	user_id: string | null;
	created_at: string;
	updated_at: string;
}

export interface SubmissionCreate {
	content: string;
	type: 'text' | 'image' | 'url';
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
