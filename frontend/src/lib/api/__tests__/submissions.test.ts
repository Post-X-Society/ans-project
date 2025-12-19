import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createSubmission, getSubmissions, getSubmission } from '../submissions';
import { apiClient } from '../client';
import type { SubmissionCreate, Submission, SubmissionListResponse } from '../types';

// Mock axios client
vi.mock('../client', () => ({
	apiClient: {
		post: vi.fn(),
		get: vi.fn()
	}
}));

describe('Submissions API', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('createSubmission', () => {
		it('should post to /api/v1/submissions with correct data', async () => {
			const mockSubmission: Submission = {
				id: '123',
				content: 'Test claim',
				submission_type: 'text',
				status: 'pending',
				user_id: null,
				created_at: '2025-01-01T00:00:00Z',
				updated_at: '2025-01-01T00:00:00Z',
				reviewers: []
			};

			const mockResponse = { data: mockSubmission };
			vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

			const data: SubmissionCreate = {
				content: 'Test claim',
				type: 'text'
			};

			const result = await createSubmission(data);

			expect(apiClient.post).toHaveBeenCalledWith('/api/v1/submissions', data);
			expect(result).toEqual(mockSubmission);
		});
	});

	describe('getSubmissions', () => {
		it('should get from /api/v1/submissions with pagination params', async () => {
			const mockResponse: SubmissionListResponse = {
				items: [],
				total: 0,
				page: 1,
				page_size: 50,
				total_pages: 0
			};

			vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

			const result = await getSubmissions(1, 50);

			expect(apiClient.get).toHaveBeenCalledWith('/api/v1/submissions', {
				params: { page: 1, page_size: 50 }
			});
			expect(result).toEqual(mockResponse);
		});

		it('should use default pagination values', async () => {
			const mockResponse: SubmissionListResponse = {
				items: [],
				total: 0,
				page: 1,
				page_size: 50,
				total_pages: 0
			};

			vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

			await getSubmissions();

			expect(apiClient.get).toHaveBeenCalledWith('/api/v1/submissions', {
				params: { page: 1, page_size: 50 }
			});
		});
	});

	describe('getSubmission', () => {
		it('should get single submission by ID', async () => {
			const mockSubmission: Submission = {
				id: '123',
				content: 'Test claim',
				submission_type: 'text',
				status: 'pending',
				user_id: null,
				created_at: '2025-01-01T00:00:00Z',
				updated_at: '2025-01-01T00:00:00Z',
				reviewers: []
			};

			vi.mocked(apiClient.get).mockResolvedValue({ data: mockSubmission });

			const result = await getSubmission('123');

			expect(apiClient.get).toHaveBeenCalledWith('/api/v1/submissions/123');
			expect(result).toEqual(mockSubmission);
		});
	});
});
