import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SubmissionFormTest from './SubmissionFormTest.svelte';

// Mock the API
vi.mock('$lib/api/submissions', () => ({
	createSubmission: vi.fn().mockResolvedValue({
		id: '123',
		content: 'Test',
		submission_type: 'text',
		status: 'pending',
		user_id: null,
		created_at: '2025-01-01',
		updated_at: '2025-01-01'
	})
}));

describe('SubmissionForm', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should render form with textarea and submit type selector', () => {
		render(SubmissionFormTest);

		expect(screen.getByLabelText(/claim.*content/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/submission type/i)).toBeInTheDocument();
		expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
	});

	it('should have text, image, and url options in type selector', () => {
		render(SubmissionFormTest);

		const select = screen.getByLabelText(/submission type/i) as HTMLSelectElement;
		const options = Array.from(select.options).map((opt) => opt.value);

		expect(options).toContain('text');
		expect(options).toContain('image');
		expect(options).toContain('url');
	});

	it('should show validation error for content less than 10 characters', async () => {
		render(SubmissionFormTest);

		const textarea = screen.getByLabelText(/claim.*content/i);
		const submitBtn = screen.getByRole('button', { name: /submit/i });

		await fireEvent.input(textarea, { target: { value: 'short' } });
		await fireEvent.click(submitBtn);

		await waitFor(() => {
			expect(screen.getByText(/at least 10 characters/i)).toBeInTheDocument();
		});
	});

	it('should show validation error for content more than 5000 characters', async () => {
		render(SubmissionFormTest);

		const textarea = screen.getByLabelText(/claim.*content/i);
		const submitBtn = screen.getByRole('button', { name: /submit/i });

		const longText = 'a'.repeat(5001);
		await fireEvent.input(textarea, { target: { value: longText } });
		await fireEvent.click(submitBtn);

		await waitFor(() => {
			expect(screen.getByText(/maximum.*5000 characters/i)).toBeInTheDocument();
		});
	});

	it('should show validation error for empty content', async () => {
		render(SubmissionFormTest);

		const submitBtn = screen.getByRole('button', { name: /submit/i });
		await fireEvent.click(submitBtn);

		await waitFor(() => {
			expect(screen.getByText(/required|cannot be empty/i)).toBeInTheDocument();
		});
	});

	it('should display character count', async () => {
		render(SubmissionFormTest);

		const textarea = screen.getByLabelText(/claim.*content/i);
		await fireEvent.input(textarea, { target: { value: 'Test content' } });

		expect(screen.getByText(/12.*5000/)).toBeInTheDocument();
	});

	it('should have text as default submission type', () => {
		render(SubmissionFormTest);

		const select = screen.getByLabelText(/submission type/i) as HTMLSelectElement;
		expect(select.value).toBe('text');
	});
});
