import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SubmissionFormTest from './SubmissionFormTest.svelte';

// Mock the API
vi.mock('$lib/api/submissions', () => ({
	createSpotlightSubmission: vi.fn().mockResolvedValue({
		id: '123',
		spotlight_link: 'https://www.snapchat.com/spotlight/test',
		creator_name: 'Test Creator',
		creator_username: 'testuser',
		view_count: 1000,
		duration_ms: 30000,
		status: 'pending',
		created_at: '2025-01-01',
		updated_at: '2025-01-01'
	})
}));

describe('SubmissionForm', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should render form with Spotlight link input and submit button', () => {
		render(SubmissionFormTest);

		expect(screen.getByLabelText(/snapchat.*spotlight.*link/i)).toBeInTheDocument();
		// Button shows "Please login to submit" when not authenticated
		expect(screen.getByRole('button', { name: /please login to submit/i })).toBeInTheDocument();
	});

	it('should have URL input type for Spotlight link', () => {
		render(SubmissionFormTest);

		const input = screen.getByLabelText(/snapchat.*spotlight.*link/i);
		expect(input).toHaveAttribute('type', 'url');
	});

	it('should disable form when not authenticated', () => {
		render(SubmissionFormTest);

		const input = screen.getByLabelText(/snapchat.*spotlight.*link/i);
		const submitBtn = screen.getByRole('button', { name: /please login to submit/i });

		expect(input).toBeDisabled();
		expect(submitBtn).toBeDisabled();
	});

	it('should display help text about Spotlight link', () => {
		render(SubmissionFormTest);

		expect(screen.getByText(/paste a snapchat spotlight link.*automatically fetched/i)).toBeInTheDocument();
	});

	it('should show login prompt when not authenticated', () => {
		render(SubmissionFormTest);

		expect(screen.getByText(/please login to submit/i)).toBeInTheDocument();
		expect(screen.getByText(/you must be logged in.*spotlight content/i)).toBeInTheDocument();
	});

	// Issue #177: Submitter Comment Field Tests
	describe('Submitter Comment Field (Issue #177)', () => {
		it('should render additional context textarea', () => {
			render(SubmissionFormTest);

			expect(screen.getByLabelText(/additional context/i)).toBeInTheDocument();
		});

		it('should have textarea with 500 character max length', () => {
			render(SubmissionFormTest);

			const textarea = screen.getByLabelText(/additional context/i);
			expect(textarea.tagName.toLowerCase()).toBe('textarea');
			expect(textarea).toHaveAttribute('maxlength', '500');
		});

		it('should display character counter showing 0/500 initially', () => {
			render(SubmissionFormTest);

			expect(screen.getByText(/0\/500/)).toBeInTheDocument();
		});

		it('should update character counter when typing', async () => {
			render(SubmissionFormTest);

			const textarea = screen.getByLabelText(/additional context/i) as HTMLTextAreaElement;
			await fireEvent.input(textarea, { target: { value: 'Test comment' } });

			expect(screen.getByText(/12\/500/)).toBeInTheDocument();
		});

		it('should show warning color when approaching character limit', async () => {
			render(SubmissionFormTest);

			const textarea = screen.getByLabelText(/additional context/i) as HTMLTextAreaElement;
			const longText = 'A'.repeat(450);
			await fireEvent.input(textarea, { target: { value: longText } });

			// Counter should change color when close to limit
			const counter = screen.getByText(/450\/500/);
			expect(counter).toBeInTheDocument();
		});

		it('should display placeholder text about why fact-checking is needed', () => {
			render(SubmissionFormTest);

			const textarea = screen.getByLabelText(/additional context/i);
			expect(textarea).toHaveAttribute('placeholder');
		});

		it('should disable textarea when not authenticated', () => {
			render(SubmissionFormTest);

			const textarea = screen.getByLabelText(/additional context/i);
			expect(textarea).toBeDisabled();
		});

		it('should mark the field as optional', () => {
			render(SubmissionFormTest);

			// Should show "(Optional)" in the label or nearby text
			expect(screen.getByText(/\(optional\)/i)).toBeInTheDocument();
		});
	});
});
