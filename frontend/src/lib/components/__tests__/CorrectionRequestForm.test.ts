/**
 * CorrectionRequestForm Component Tests
 * Issue #79: Frontend Correction Request Form (TDD)
 *
 * TDD Red Phase: Tests written FIRST before implementation.
 * These tests define the expected behavior of the CorrectionRequestForm component.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import CorrectionRequestFormTest from './CorrectionRequestFormTest.svelte';

// Mock the API
vi.mock('$lib/api/corrections', () => ({
	submitCorrectionRequest: vi.fn()
}));

import { submitCorrectionRequest } from '$lib/api/corrections';

describe('CorrectionRequestForm', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
	});

	describe('Form Rendering', () => {
		it('should render the form title', () => {
			render(CorrectionRequestFormTest);

			expect(screen.getByRole('heading', { name: /request a correction/i })).toBeInTheDocument();
		});

		it('should render the form description with EFCSN guidelines reference', () => {
			render(CorrectionRequestFormTest);

			expect(screen.getByText(/7 days per EFCSN guidelines/i)).toBeInTheDocument();
		});

		it('should render error type dropdown with label', () => {
			render(CorrectionRequestFormTest);

			expect(screen.getByLabelText(/type of error/i)).toBeInTheDocument();
		});

		it('should render all three error type options', () => {
			render(CorrectionRequestFormTest);

			const select = screen.getByLabelText(/type of error/i) as HTMLSelectElement;
			expect(select).toBeInTheDocument();

			// Check options within the select element
			const options = select.querySelectorAll('option');
			const optionTexts = Array.from(options).map((opt) => opt.textContent);

			expect(optionTexts).toContain('Minor Error');
			expect(optionTexts).toContain('New Information');
			expect(optionTexts).toContain('Substantial Error');
		});

		it('should render evidence/details textarea with label', () => {
			render(CorrectionRequestFormTest);

			expect(screen.getByLabelText(/evidence and details/i)).toBeInTheDocument();
		});

		it('should render email input field (optional)', () => {
			render(CorrectionRequestFormTest);

			const emailInput = screen.getByLabelText(/your email/i);
			expect(emailInput).toBeInTheDocument();
			expect(emailInput).toHaveAttribute('type', 'email');
		});

		it('should render submit button', () => {
			render(CorrectionRequestFormTest);

			expect(
				screen.getByRole('button', { name: /submit correction request/i })
			).toBeInTheDocument();
		});

		it('should render EFCSN escalation link', () => {
			render(CorrectionRequestFormTest);

			expect(screen.getByText(/not satisfied\? escalate to efcsn/i)).toBeInTheDocument();
		});
	});

	describe('Form Validation', () => {
		it('should show error when submitting without selecting error type', async () => {
			render(CorrectionRequestFormTest);

			// Fill details but not type to bypass native validation on type
			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'Some valid details text here.' }
			});

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/please select an error type/i)).toBeInTheDocument();
			});
		});

		it('should show error when submitting without details', async () => {
			render(CorrectionRequestFormTest);

			// Select an error type first
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/please provide details about the error/i)).toBeInTheDocument();
			});
		});

		it('should show error when details are less than 10 characters', async () => {
			render(CorrectionRequestFormTest);

			// Select an error type
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			// Enter short details
			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, { target: { value: 'Too short' } });

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/details must be at least 10 characters/i)).toBeInTheDocument();
			});
		});

		it('should show error for invalid email format', async () => {
			render(CorrectionRequestFormTest);

			// Fill required fields
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'This is a valid error description with enough characters.' }
			});

			// Enter invalid email
			const emailInput = screen.getByLabelText(/your email/i);
			await fireEvent.input(emailInput, { target: { value: 'invalid-email' } });

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
			});
		});

		it('should allow submission without email (optional field)', async () => {
			vi.mocked(submitCorrectionRequest).mockResolvedValueOnce({
				id: 'test-id',
				fact_check_id: 'test-fact-check-id',
				correction_type: 'minor',
				status: 'pending',
				sla_deadline: '2026-01-12T00:00:00Z',
				acknowledgment_sent: false,
				created_at: '2026-01-05T00:00:00Z'
			});

			render(CorrectionRequestFormTest);

			// Fill required fields only
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'This is a valid error description with enough characters.' }
			});

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(submitCorrectionRequest).toHaveBeenCalled();
			});
		});
	});

	describe('Form Submission', () => {
		it('should call API with correct data on valid submission', async () => {
			vi.mocked(submitCorrectionRequest).mockResolvedValueOnce({
				id: 'test-id',
				fact_check_id: 'test-fact-check-id',
				correction_type: 'substantial',
				status: 'pending',
				requester_email: 'test@example.com',
				sla_deadline: '2026-01-12T00:00:00Z',
				acknowledgment_sent: true,
				created_at: '2026-01-05T00:00:00Z'
			});

			render(CorrectionRequestFormTest);

			// Fill all fields
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'substantial' } });

			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'This is a substantial error in the rating. The claim was rated false but evidence shows it is true.' }
			});

			const emailInput = screen.getByLabelText(/your email/i);
			await fireEvent.input(emailInput, { target: { value: 'test@example.com' } });

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(submitCorrectionRequest).toHaveBeenCalledWith({
					fact_check_id: 'test-fact-check-id',
					correction_type: 'substantial',
					request_details: 'This is a substantial error in the rating. The claim was rated false but evidence shows it is true.',
					requester_email: 'test@example.com'
				});
			});
		});

		it('should show loading state during submission', async () => {
			vi.mocked(submitCorrectionRequest).mockImplementation(
				() => new Promise((resolve) => setTimeout(resolve, 100))
			);

			render(CorrectionRequestFormTest);

			// Fill required fields
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'This is a valid error description with enough characters.' }
			});

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			expect(screen.getByText(/submitting/i)).toBeInTheDocument();
		});

		it('should show success message after successful submission', async () => {
			vi.mocked(submitCorrectionRequest).mockResolvedValueOnce({
				id: 'test-id',
				fact_check_id: 'test-fact-check-id',
				correction_type: 'minor',
				status: 'pending',
				sla_deadline: '2026-01-12T00:00:00Z',
				acknowledgment_sent: false,
				created_at: '2026-01-05T00:00:00Z'
			});

			render(CorrectionRequestFormTest);

			// Fill required fields
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'This is a valid error description with enough characters.' }
			});

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/correction request submitted/i)).toBeInTheDocument();
			});
		});

		it('should show SLA deadline in success message', async () => {
			vi.mocked(submitCorrectionRequest).mockResolvedValueOnce({
				id: 'test-id',
				fact_check_id: 'test-fact-check-id',
				correction_type: 'minor',
				status: 'pending',
				sla_deadline: '2026-01-12T00:00:00Z',
				acknowledgment_sent: false,
				created_at: '2026-01-05T00:00:00Z'
			});

			render(CorrectionRequestFormTest);

			// Fill required fields
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'This is a valid error description with enough characters.' }
			});

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/expected response by/i)).toBeInTheDocument();
			});
		});

		it('should show acknowledgment message when email was sent', async () => {
			vi.mocked(submitCorrectionRequest).mockResolvedValueOnce({
				id: 'test-id',
				fact_check_id: 'test-fact-check-id',
				correction_type: 'minor',
				status: 'pending',
				requester_email: 'test@example.com',
				sla_deadline: '2026-01-12T00:00:00Z',
				acknowledgment_sent: true,
				created_at: '2026-01-05T00:00:00Z'
			});

			render(CorrectionRequestFormTest);

			// Fill required fields with email
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'This is a valid error description with enough characters.' }
			});

			const emailInput = screen.getByLabelText(/your email/i);
			await fireEvent.input(emailInput, { target: { value: 'test@example.com' } });

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/confirmation email has been sent/i)).toBeInTheDocument();
			});
		});

		it('should call onSuccess callback after successful submission', async () => {
			const onSuccess = vi.fn();
			vi.mocked(submitCorrectionRequest).mockResolvedValueOnce({
				id: 'test-id',
				fact_check_id: 'test-fact-check-id',
				correction_type: 'minor',
				status: 'pending',
				sla_deadline: '2026-01-12T00:00:00Z',
				acknowledgment_sent: false,
				created_at: '2026-01-05T00:00:00Z'
			});

			render(CorrectionRequestFormTest, { props: { onSuccess } });

			// Fill required fields
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'This is a valid error description with enough characters.' }
			});

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(onSuccess).toHaveBeenCalled();
			});
		});
	});

	describe('Error Handling', () => {
		it('should show error message when submission fails', async () => {
			vi.mocked(submitCorrectionRequest).mockRejectedValueOnce(new Error('Network error'));

			render(CorrectionRequestFormTest);

			// Fill required fields
			const select = screen.getByLabelText(/type of error/i);
			await fireEvent.change(select, { target: { value: 'minor' } });

			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'This is a valid error description with enough characters.' }
			});

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/failed to submit correction request/i)).toBeInTheDocument();
			});
		});
	});

	describe('Internationalization', () => {
		it('should display Dutch translations when locale is nl', async () => {
			locale.set('nl');

			render(CorrectionRequestFormTest);

			await waitFor(() => {
				expect(screen.getByRole('heading', { name: /correctie aanvragen/i })).toBeInTheDocument();
			});
		});

		it('should display Dutch error type options when locale is nl', async () => {
			locale.set('nl');

			render(CorrectionRequestFormTest);

			await waitFor(() => {
				const select = screen.getByLabelText(/type fout/i) as HTMLSelectElement;
				const options = select.querySelectorAll('option');
				const optionTexts = Array.from(options).map((opt) => opt.textContent);

				expect(optionTexts).toContain('Kleine Fout');
				expect(optionTexts).toContain('Nieuwe Informatie');
				expect(optionTexts).toContain('Substantiële Fout');
			});
		});
	});

	describe('Accessibility', () => {
		it('should have proper form labels for all inputs', () => {
			render(CorrectionRequestFormTest);

			// All form controls should have associated labels
			expect(screen.getByLabelText(/type of error/i)).toBeInTheDocument();
			expect(screen.getByLabelText(/evidence and details/i)).toBeInTheDocument();
			expect(screen.getByLabelText(/your email/i)).toBeInTheDocument();
		});

		it('should have aria-describedby for error messages', async () => {
			render(CorrectionRequestFormTest);

			// Fill details to bypass native required validation on textarea
			const textarea = screen.getByLabelText(/evidence and details/i);
			await fireEvent.input(textarea, {
				target: { value: 'Some valid details text here.' }
			});

			const submitBtn = screen.getByRole('button', { name: /submit correction request/i });
			await fireEvent.click(submitBtn);

			// Wait for error to appear, then check aria-describedby
			await waitFor(() => {
				const select = screen.getByLabelText(/type of error/i);
				expect(select).toHaveAttribute('aria-describedby', 'correction-type-error');
			});
		});

		it('should have required attribute on mandatory fields', () => {
			render(CorrectionRequestFormTest);

			const select = screen.getByLabelText(/type of error/i);
			const textarea = screen.getByLabelText(/evidence and details/i);

			expect(select).toHaveAttribute('required');
			expect(textarea).toHaveAttribute('required');
		});

		it('should not have required attribute on optional email field', () => {
			render(CorrectionRequestFormTest);

			const emailInput = screen.getByLabelText(/your email/i);
			expect(emailInput).not.toHaveAttribute('required');
		});
	});

	describe('Error Type Descriptions', () => {
		it('should show description for minor error type', () => {
			render(CorrectionRequestFormTest);

			expect(screen.getByText(/typos, grammar, or formatting issues/i)).toBeInTheDocument();
		});

		it('should show description for update error type', () => {
			render(CorrectionRequestFormTest);

			expect(screen.getByText(/additional sources or updated information/i)).toBeInTheDocument();
		});

		it('should show description for substantial error type', () => {
			render(CorrectionRequestFormTest);

			expect(screen.getByText(/rating change or major factual error/i)).toBeInTheDocument();
		});
	});
});
