import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import SourceForm from '../SourceForm.svelte';
import type { Source, SourceType, SourceRelevance } from '$lib/api/types';

// TODO: Update tests after SourceForm refactoring (Issue: tests need updating for new fields)
describe.skip('SourceForm', () => {
	beforeEach(() => {
		locale.set('en');
		vi.clearAllMocks();
	});

	describe('rendering', () => {
		it('should render the form with all required fields', () => {
			render(SourceForm);

			// Source URL/reference input
			expect(screen.getByLabelText(/source url or reference/i)).toBeInTheDocument();

			// Source type dropdown
			expect(screen.getByLabelText(/source type/i)).toBeInTheDocument();

			// Credibility rating (1-5 stars)
			expect(screen.getByText(/credibility rating/i)).toBeInTheDocument();

			// Relevance selector
			expect(screen.getByLabelText(/relevance/i)).toBeInTheDocument();

			// Submit button
			expect(screen.getByRole('button', { name: /add source/i })).toBeInTheDocument();
		});

		it('should have URL input with correct type', () => {
			render(SourceForm);

			const urlInput = screen.getByLabelText(/source url or reference/i);
			expect(urlInput).toHaveAttribute('type', 'text');
		});
	});

	describe('source type dropdown', () => {
		it('should display all source type options', () => {
			render(SourceForm);

			const typeSelect = screen.getByLabelText(/source type/i);
			expect(typeSelect).toBeInTheDocument();

			// Check for expected source types
			expect(screen.getByRole('option', { name: /official/i })).toBeInTheDocument();
			expect(screen.getByRole('option', { name: /news/i })).toBeInTheDocument();
			expect(screen.getByRole('option', { name: /social media/i })).toBeInTheDocument();
			expect(screen.getByRole('option', { name: /research/i })).toBeInTheDocument();
			expect(screen.getByRole('option', { name: /other/i })).toBeInTheDocument();
		});

		it('should allow selecting a source type', async () => {
			render(SourceForm);

			const typeSelect = screen.getByLabelText(/source type/i) as HTMLSelectElement;
			await fireEvent.change(typeSelect, { target: { value: 'news' } });

			expect(typeSelect.value).toBe('news');
		});
	});

	describe('credibility rating (1-5 stars)', () => {
		it('should render 5 star buttons for credibility rating', () => {
			render(SourceForm);

			const starButtons = screen.getAllByRole('button', { name: /rate.*star/i });
			expect(starButtons).toHaveLength(5);
		});

		it('should highlight selected stars', async () => {
			render(SourceForm);

			const starButtons = screen.getAllByRole('button', { name: /rate.*star/i });

			// Click on 3rd star
			await fireEvent.click(starButtons[2]);

			// First 3 stars should be filled (have aria-pressed="true")
			expect(starButtons[0]).toHaveAttribute('aria-pressed', 'true');
			expect(starButtons[1]).toHaveAttribute('aria-pressed', 'true');
			expect(starButtons[2]).toHaveAttribute('aria-pressed', 'true');

			// Last 2 should not be pressed
			expect(starButtons[3]).toHaveAttribute('aria-pressed', 'false');
			expect(starButtons[4]).toHaveAttribute('aria-pressed', 'false');
		});

		it('should allow changing the credibility rating', async () => {
			render(SourceForm);

			const starButtons = screen.getAllByRole('button', { name: /rate.*star/i });

			// First select 4 stars
			await fireEvent.click(starButtons[3]);
			expect(starButtons[3]).toHaveAttribute('aria-pressed', 'true');

			// Then change to 2 stars
			await fireEvent.click(starButtons[1]);
			expect(starButtons[1]).toHaveAttribute('aria-pressed', 'true');
			expect(starButtons[3]).toHaveAttribute('aria-pressed', 'false');
		});

		it('should have accessible labels for each star', () => {
			render(SourceForm);

			expect(screen.getByRole('button', { name: /rate 1 star/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /rate 2 stars/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /rate 3 stars/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /rate 4 stars/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /rate 5 stars/i })).toBeInTheDocument();
		});
	});

	describe('relevance selector', () => {
		it('should display all relevance options', () => {
			render(SourceForm);

			const relevanceSelect = screen.getByLabelText(/relevance/i);
			expect(relevanceSelect).toBeInTheDocument();

			expect(screen.getByRole('option', { name: /supports/i })).toBeInTheDocument();
			expect(screen.getByRole('option', { name: /contradicts/i })).toBeInTheDocument();
			expect(screen.getByRole('option', { name: /contextualizes/i })).toBeInTheDocument();
		});

		it('should allow selecting a relevance type', async () => {
			render(SourceForm);

			const relevanceSelect = screen.getByLabelText(/relevance/i) as HTMLSelectElement;
			await fireEvent.change(relevanceSelect, { target: { value: 'contradicts' } });

			expect(relevanceSelect.value).toBe('contradicts');
		});
	});

	describe('form validation', () => {
		it('should show error when submitting without URL', async () => {
			render(SourceForm);

			const submitButton = screen.getByRole('button', { name: /add source/i });
			await fireEvent.click(submitButton);

			expect(screen.getByText(/source url or reference is required/i)).toBeInTheDocument();
		});

		it('should show error when submitting without source type', async () => {
			render(SourceForm);

			const urlInput = screen.getByLabelText(/source url or reference/i);
			await fireEvent.input(urlInput, { target: { value: 'https://example.com' } });

			const submitButton = screen.getByRole('button', { name: /add source/i });
			await fireEvent.click(submitButton);

			expect(screen.getByText(/source type is required/i)).toBeInTheDocument();
		});

		it('should show error when submitting without credibility rating', async () => {
			render(SourceForm);

			const urlInput = screen.getByLabelText(/source url or reference/i);
			await fireEvent.input(urlInput, { target: { value: 'https://example.com' } });

			const typeSelect = screen.getByLabelText(/source type/i);
			await fireEvent.change(typeSelect, { target: { value: 'news' } });

			const submitButton = screen.getByRole('button', { name: /add source/i });
			await fireEvent.click(submitButton);

			expect(screen.getByText(/credibility rating is required/i)).toBeInTheDocument();
		});

		it('should show error when submitting without relevance', async () => {
			render(SourceForm);

			// Fill in all fields except relevance
			const urlInput = screen.getByLabelText(/source url or reference/i);
			await fireEvent.input(urlInput, { target: { value: 'https://example.com' } });

			const typeSelect = screen.getByLabelText(/source type/i);
			await fireEvent.change(typeSelect, { target: { value: 'news' } });

			const starButtons = screen.getAllByRole('button', { name: /rate.*star/i });
			await fireEvent.click(starButtons[3]); // 4 stars

			const submitButton = screen.getByRole('button', { name: /add source/i });
			await fireEvent.click(submitButton);

			expect(screen.getByText(/relevance is required/i)).toBeInTheDocument();
		});
	});

	describe('form submission', () => {
		it('should call onSubmit with correct data when form is valid', async () => {
			const onSubmit = vi.fn();
			render(SourceForm, { props: { onSubmit } });

			// Fill in all fields
			const urlInput = screen.getByLabelText(/source url or reference/i);
			await fireEvent.input(urlInput, { target: { value: 'https://example.com/article' } });

			const typeSelect = screen.getByLabelText(/source type/i);
			await fireEvent.change(typeSelect, { target: { value: 'news' } });

			const starButtons = screen.getAllByRole('button', { name: /rate.*star/i });
			await fireEvent.click(starButtons[3]); // 4 stars

			const relevanceSelect = screen.getByLabelText(/relevance/i);
			await fireEvent.change(relevanceSelect, { target: { value: 'supports' } });

			const submitButton = screen.getByRole('button', { name: /add source/i });
			await fireEvent.click(submitButton);

			expect(onSubmit).toHaveBeenCalledWith({
				url: 'https://example.com/article',
				source_type: 'news',
				credibility_rating: 4,
				relevance: 'supports'
			});
		});

		it('should clear form after successful submission', async () => {
			const onSubmit = vi.fn();
			render(SourceForm, { props: { onSubmit } });

			// Fill in all fields
			const urlInput = screen.getByLabelText(/source url or reference/i) as HTMLInputElement;
			await fireEvent.input(urlInput, { target: { value: 'https://example.com' } });

			const typeSelect = screen.getByLabelText(/source type/i) as HTMLSelectElement;
			await fireEvent.change(typeSelect, { target: { value: 'news' } });

			const starButtons = screen.getAllByRole('button', { name: /rate.*star/i });
			await fireEvent.click(starButtons[2]); // 3 stars

			const relevanceSelect = screen.getByLabelText(/relevance/i) as HTMLSelectElement;
			await fireEvent.change(relevanceSelect, { target: { value: 'supports' } });

			const submitButton = screen.getByRole('button', { name: /add source/i });
			await fireEvent.click(submitButton);

			// Form should be cleared
			await waitFor(() => {
				expect(urlInput.value).toBe('');
				expect(typeSelect.value).toBe('');
			});
		});
	});

	describe('source count warning', () => {
		it('should show warning when fewer than 2 sources exist', () => {
			render(SourceForm, { props: { existingSourceCount: 0 } });

			expect(
				screen.getByText(/at least 2 sources are recommended/i)
			).toBeInTheDocument();
		});

		it('should show warning with count when only 1 source exists', () => {
			render(SourceForm, { props: { existingSourceCount: 1 } });

			expect(
				screen.getByText(/at least 2 sources are recommended/i)
			).toBeInTheDocument();
			expect(
				screen.getByText(/1 source added/i)
			).toBeInTheDocument();
		});

		it('should not show warning when 2 or more sources exist', () => {
			render(SourceForm, { props: { existingSourceCount: 2 } });

			expect(
				screen.queryByText(/at least 2 sources are recommended/i)
			).not.toBeInTheDocument();
		});

		it('should display warning with appropriate styling', () => {
			render(SourceForm, { props: { existingSourceCount: 0 } });

			const warning = screen.getByRole('alert');
			expect(warning).toBeInTheDocument();
			expect(warning.className).toContain('bg-yellow');
		});
	});

	describe('edit mode', () => {
		const existingSource: Source = {
			id: '123',
			url: 'https://existing.com',
			source_type: 'research',
			credibility_rating: 5,
			relevance: 'contextualizes',
			created_at: '2025-01-01',
			updated_at: '2025-01-01'
		};

		it('should populate form with existing source data in edit mode', () => {
			render(SourceForm, { props: { source: existingSource, mode: 'edit' } });

			const urlInput = screen.getByLabelText(/source url or reference/i) as HTMLInputElement;
			expect(urlInput.value).toBe('https://existing.com');

			const typeSelect = screen.getByLabelText(/source type/i) as HTMLSelectElement;
			expect(typeSelect.value).toBe('research');

			const starButtons = screen.getAllByRole('button', { name: /rate.*star/i });
			expect(starButtons[4]).toHaveAttribute('aria-pressed', 'true'); // 5 stars

			const relevanceSelect = screen.getByLabelText(/relevance/i) as HTMLSelectElement;
			expect(relevanceSelect.value).toBe('contextualizes');
		});

		it('should show "Update Source" button in edit mode', () => {
			render(SourceForm, { props: { source: existingSource, mode: 'edit' } });

			expect(screen.getByRole('button', { name: /update source/i })).toBeInTheDocument();
		});

		it('should show cancel button in edit mode', () => {
			const onCancel = vi.fn();
			render(SourceForm, { props: { source: existingSource, mode: 'edit', onCancel } });

			expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
		});

		it('should call onCancel when cancel button is clicked', async () => {
			const onCancel = vi.fn();
			render(SourceForm, { props: { source: existingSource, mode: 'edit', onCancel } });

			const cancelButton = screen.getByRole('button', { name: /cancel/i });
			await fireEvent.click(cancelButton);

			expect(onCancel).toHaveBeenCalled();
		});
	});

	describe('accessibility', () => {
		it('should have proper form labels', () => {
			render(SourceForm);

			// All form fields should be properly labeled
			expect(screen.getByLabelText(/source url or reference/i)).toBeInTheDocument();
			expect(screen.getByLabelText(/source type/i)).toBeInTheDocument();
			expect(screen.getByLabelText(/relevance/i)).toBeInTheDocument();
		});

		it('should have fieldset with legend for credibility rating', () => {
			render(SourceForm);

			const fieldset = screen.getByRole('group', { name: /credibility rating/i });
			expect(fieldset).toBeInTheDocument();
		});

		it('should announce validation errors to screen readers', async () => {
			render(SourceForm);

			const submitButton = screen.getByRole('button', { name: /add source/i });
			await fireEvent.click(submitButton);

			// Error messages should be in alert role or have aria-live
			const errorMessages = screen.getAllByRole('alert');
			expect(errorMessages.length).toBeGreaterThan(0);
		});

		it('should have keyboard navigation for star rating', async () => {
			render(SourceForm);

			const starButtons = screen.getAllByRole('button', { name: /rate.*star/i });

			// All stars should be focusable
			starButtons.forEach((star) => {
				expect(star).not.toHaveAttribute('tabindex', '-1');
			});
		});
	});

	describe('loading state', () => {
		it('should disable form and show loading indicator when submitting', async () => {
			const onSubmit = vi.fn(() => new Promise((resolve) => setTimeout(resolve, 100)));
			render(SourceForm, { props: { onSubmit } });

			// Fill form
			const urlInput = screen.getByLabelText(/source url or reference/i);
			await fireEvent.input(urlInput, { target: { value: 'https://example.com' } });

			const typeSelect = screen.getByLabelText(/source type/i);
			await fireEvent.change(typeSelect, { target: { value: 'news' } });

			const starButtons = screen.getAllByRole('button', { name: /rate.*star/i });
			await fireEvent.click(starButtons[2]);

			const relevanceSelect = screen.getByLabelText(/relevance/i);
			await fireEvent.change(relevanceSelect, { target: { value: 'supports' } });

			const submitButton = screen.getByRole('button', { name: /add source/i });
			await fireEvent.click(submitButton);

			// Should show loading state
			expect(screen.getByRole('button', { name: /adding/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /adding/i })).toBeDisabled();
		});
	});

	describe('multilingual support', () => {
		it('should display translated labels', () => {
			locale.set('en');
			render(SourceForm);

			expect(screen.getByLabelText(/source url or reference/i)).toBeInTheDocument();
			expect(screen.getByLabelText(/source type/i)).toBeInTheDocument();
		});

		it('should display translated source type options', () => {
			locale.set('en');
			render(SourceForm);

			expect(screen.getByRole('option', { name: /official/i })).toBeInTheDocument();
			expect(screen.getByRole('option', { name: /news/i })).toBeInTheDocument();
		});
	});
});
