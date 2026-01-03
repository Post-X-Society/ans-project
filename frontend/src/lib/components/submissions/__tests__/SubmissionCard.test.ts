import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { writable } from 'svelte/store';
import SubmissionCard from '../SubmissionCard.svelte';
import type { Submission } from '$lib/api/types';
import * as authStore from '$lib/stores/auth';

// Mock the auth store
vi.mock('$lib/stores/auth', () => ({
	currentUser: writable(null)
}));

// Mock the selfAssignToSubmission API function
vi.mock('$lib/api/submissions', () => ({
	selfAssignToSubmission: vi.fn()
}));

describe('SubmissionCard - Self-Assignment UI', () => {
	const mockSubmission: Submission = {
		id: 'test-123',
		user_id: 'user-456',
		content: 'Test claim about something',
		submission_type: 'text',
		status: 'pending',
		created_at: '2026-01-03T10:00:00Z',
		updated_at: '2026-01-03T10:00:00Z',
		reviewers: [],
		is_assigned_to_me: false,
		user: {
			id: 'user-456',
			email: 'submitter@example.com'
		}
	};

	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('Unassigned Badge', () => {
		it('should show "Unassigned" badge when no reviewers assigned', () => {
			const { container } = render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const badge = container.querySelector('[data-testid="assignment-badge"]');
			expect(badge).toBeInTheDocument();
			expect(badge).toHaveTextContent('Unassigned');
			expect(badge).toHaveClass('bg-gray-100', 'text-gray-700');
		});

		it('should show reviewer count badge when reviewers assigned', () => {
			const submissionWithReviewers = {
				...mockSubmission,
				reviewers: [
					{ id: 'rev-1', email: 'reviewer1@example.com' },
					{ id: 'rev-2', email: 'reviewer2@example.com' }
				]
			};

			const { container } = render(SubmissionCard, {
				props: { submission: submissionWithReviewers }
			});

			const badge = container.querySelector('[data-testid="assignment-badge"]');
			expect(badge).toHaveTextContent('2 Reviewers');
			expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
		});

		it('should show "Assigned to you" badge when current user is assigned', () => {
			authStore.currentUser.set({
				id: 'current-user',
				email: 'current@example.com',
				role: 'reviewer'
			});

			const submissionAssignedToMe = {
				...mockSubmission,
				reviewers: [{ id: 'current-user', email: 'current@example.com' }],
				is_assigned_to_me: true
			};

			const { container } = render(SubmissionCard, {
				props: { submission: submissionAssignedToMe }
			});

			const badge = container.querySelector('[data-testid="assignment-badge"]');
			expect(badge).toHaveTextContent('Assigned to you');
			expect(badge).toHaveClass('bg-green-100', 'text-green-800');
		});
	});

	describe('Assign to Me Button', () => {
		it('should show "Assign to Me" button for reviewer when not assigned', () => {
			authStore.currentUser.set({
				id: 'current-user',
				email: 'reviewer@example.com',
				role: 'reviewer'
			});

			render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const button = screen.getByRole('button', { name: 'Assign this submission to yourself' });
			expect(button).toBeInTheDocument();
			expect(button).not.toBeDisabled();
			expect(button).toHaveTextContent('Assign to Me');
		});

		it('should show "Assign to Me" button for admin', () => {
			authStore.currentUser.set({
				id: 'admin-user',
				email: 'admin@example.com',
				role: 'admin'
			});

			render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const button = screen.getByRole('button', { name: 'Assign this submission to yourself' });
			expect(button).toBeInTheDocument();
		});

		it('should show "Assign to Me" button for super_admin', () => {
			authStore.currentUser.set({
				id: 'super-admin-user',
				email: 'superadmin@example.com',
				role: 'super_admin'
			});

			render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const button = screen.getByRole('button', { name: 'Assign this submission to yourself' });
			expect(button).toBeInTheDocument();
		});

		it('should NOT show button for submitter role', () => {
			authStore.currentUser.set({
				id: 'submitter-user',
				email: 'submitter@example.com',
				role: 'submitter'
			});

			render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const button = screen.queryByRole('button', { name: 'Assign this submission to yourself' });
			expect(button).not.toBeInTheDocument();
		});

		it('should NOT show button when not logged in', () => {
			authStore.currentUser.set(null);

			render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const button = screen.queryByRole('button', { name: 'Assign this submission to yourself' });
			expect(button).not.toBeInTheDocument();
		});

		it('should hide button when user is already assigned', () => {
			authStore.currentUser.set({
				id: 'current-user',
				email: 'reviewer@example.com',
				role: 'reviewer'
			});

			const submissionAssignedToMe = {
				...mockSubmission,
				reviewers: [{ id: 'current-user', email: 'reviewer@example.com' }],
				is_assigned_to_me: true
			};

			render(SubmissionCard, {
				props: { submission: submissionAssignedToMe }
			});

			const button = screen.queryByRole('button', { name: 'Assign this submission to yourself' });
			expect(button).not.toBeInTheDocument();
		});

		it('should show button even when other reviewers are assigned', () => {
			authStore.currentUser.set({
				id: 'current-user',
				email: 'reviewer@example.com',
				role: 'reviewer'
			});

			const submissionWithOtherReviewers = {
				...mockSubmission,
				reviewers: [
					{ id: 'other-user-1', email: 'other1@example.com' },
					{ id: 'other-user-2', email: 'other2@example.com' }
				],
				is_assigned_to_me: false
			};

			render(SubmissionCard, {
				props: { submission: submissionWithOtherReviewers }
			});

			const button = screen.getByRole('button', { name: 'Assign this submission to yourself' });
			expect(button).toBeInTheDocument();
		});
	});

	describe('Self-Assignment Functionality', () => {
		it('should call selfAssignToSubmission when button clicked', async () => {
			const { selfAssignToSubmission } = await import('$lib/api/submissions');
			vi.mocked(selfAssignToSubmission).mockResolvedValue({
				message: 'You have been assigned to this submission',
				submission_id: 'test-123',
				reviewer_id: 'current-user'
			});

			authStore.currentUser.set({
				id: 'current-user',
				email: 'reviewer@example.com',
				role: 'reviewer'
			});

			render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const button = screen.getByRole('button', { name: 'Assign this submission to yourself' });
			await fireEvent.click(button);

			expect(selfAssignToSubmission).toHaveBeenCalledWith('test-123');
		});

		it('should show loading state while assigning', async () => {
			const { selfAssignToSubmission } = await import('$lib/api/submissions');
			// Simulate slow API call
			vi.mocked(selfAssignToSubmission).mockImplementation(
				() => new Promise((resolve) => setTimeout(resolve, 100))
			);

			authStore.currentUser.set({
				id: 'current-user',
				email: 'reviewer@example.com',
				role: 'reviewer'
			});

			render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const button = screen.getByRole('button', { name: 'Assign this submission to yourself' });
			await fireEvent.click(button);

			// Button should be disabled during loading
			expect(button).toBeDisabled();
			expect(button).toHaveTextContent('Assigning...');
		});

		it('should display error message when assignment fails', async () => {
			const { selfAssignToSubmission } = await import('$lib/api/submissions');
			vi.mocked(selfAssignToSubmission).mockRejectedValue(
				new Error('Failed to assign reviewer')
			);

			authStore.currentUser.set({
				id: 'current-user',
				email: 'reviewer@example.com',
				role: 'reviewer'
			});

			render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const button = screen.getByRole('button', { name: 'Assign this submission to yourself' });
			await fireEvent.click(button);

			// Wait for error to appear
			const errorMessage = await screen.findByText('Failed to assign. Please try again.');
			expect(errorMessage).toBeInTheDocument();
			expect(errorMessage).toHaveClass('text-red-600');
		});
	});

	describe('Accessibility', () => {
		it('should have accessible button with aria-label', () => {
			authStore.currentUser.set({
				id: 'current-user',
				email: 'reviewer@example.com',
				role: 'reviewer'
			});

			render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const button = screen.getByRole('button', { name: 'Assign this submission to yourself' });
			expect(button).toHaveAttribute('aria-label', 'Assign this submission to yourself');
		});

		it('should have proper badge contrast for accessibility', () => {
			const { container } = render(SubmissionCard, {
				props: { submission: mockSubmission }
			});

			const badge = container.querySelector('[data-testid="assignment-badge"]');
			// Gray badge should have sufficient contrast (WCAG AA)
			expect(badge).toHaveClass('bg-gray-100', 'text-gray-700');
		});
	});
});
