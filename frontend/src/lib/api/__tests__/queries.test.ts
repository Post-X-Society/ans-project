import { describe, it, expect } from 'vitest';
import { submissionsQueryOptions, submissionQueryOptions, createSubmissionMutationOptions } from '../queries';

describe('TanStack Query Options', () => {
	describe('submissionsQueryOptions', () => {
		it('should have correct query key', () => {
			const options = submissionsQueryOptions(1, 50);
			expect(options.queryKey).toEqual(['submissions', { page: 1, page_size: 50 }]);
		});

		it('should have queryFn defined', () => {
			const options = submissionsQueryOptions();
			expect(options.queryFn).toBeDefined();
			expect(typeof options.queryFn).toBe('function');
		});

		it('should use default pagination values', () => {
			const options = submissionsQueryOptions();
			expect(options.queryKey).toEqual(['submissions', { page: 1, page_size: 50 }]);
		});
	});

	describe('submissionQueryOptions', () => {
		it('should have correct query key with ID', () => {
			const options = submissionQueryOptions('123');
			expect(options.queryKey).toEqual(['submissions', '123']);
		});

		it('should have queryFn defined', () => {
			const options = submissionQueryOptions('123');
			expect(options.queryFn).toBeDefined();
			expect(typeof options.queryFn).toBe('function');
		});
	});

	describe('createSubmissionMutationOptions', () => {
		it('should have mutationFn defined', () => {
			const options = createSubmissionMutationOptions();
			expect(options.mutationFn).toBeDefined();
			expect(typeof options.mutationFn).toBe('function');
		});
	});
});
