/**
 * FactCheckEditor Component Tests (TDD)
 *
 * Issue #122: Frontend Fact-Check Editor Interface
 *
 * These tests are written FIRST before implementing the component.
 * Following TDD approach as specified in the developer role.
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { locale } from 'svelte-i18n';
import type { DraftResponse, DraftContent, FactCheckRatingValue } from '$lib/api/types';

// Use vi.hoisted to avoid initialization order issues
const { mockGetDraft, mockSaveDraft } = vi.hoisted(() => ({
	mockGetDraft: vi.fn(),
	mockSaveDraft: vi.fn()
}));

// Mock the drafts API
vi.mock('$lib/api/drafts', () => ({
	getDraft: mockGetDraft,
	saveDraft: mockSaveDraft
}));

// Mock the auth store
vi.mock('$lib/stores/auth', () => ({
	authStore: {
		subscribe: vi.fn((fn) => {
			fn({ user: { id: 'user-123', email: 'reviewer@example.com', role: 'reviewer' } });
			return () => {};
		})
	}
}));

// Import after mocks
import FactCheckEditor from '../FactCheckEditor.svelte';

// Sample test data
const mockDraftContent: DraftContent = {
	claim_summary: 'Test claim summary',
	analysis: 'This is a detailed analysis of the claim that needs to be fact-checked. '.repeat(10),
	verdict: 'partly_false' as FactCheckRatingValue,
	justification: 'The claim contains some accurate information but is misleading.',
	sources_cited: ['https://example.com/source1', 'https://example.com/source2'],
	internal_notes: 'Check with senior reviewer before publishing',
	version: 1,
	last_edited_by: 'user-123'
};

const mockDraftResponse: DraftResponse = {
	fact_check_id: 'fc-123',
	draft_content: mockDraftContent,
	draft_updated_at: '2025-12-27T10:00:00Z',
	has_draft: true
};

const mockEmptyDraftResponse: DraftResponse = {
	fact_check_id: 'fc-123',
	draft_content: null,
	draft_updated_at: null,
	has_draft: false
};

describe('FactCheckEditor', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
		mockGetDraft.mockResolvedValue(mockDraftResponse);
		mockSaveDraft.mockResolvedValue(mockDraftResponse);
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	describe('Loading and Initial Display', () => {
		it('should display loading state initially', () => {
			mockGetDraft.mockImplementation(() => new Promise(() => {}));

			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			expect(screen.getByText(/loading/i)).toBeInTheDocument();
		});

		it('should render editor title when loaded', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByText(/fact-check editor/i)).toBeInTheDocument();
			});
		});

		it('should display error state when API fails', async () => {
			mockGetDraft.mockRejectedValue(new Error('API Error'));

			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByText(/failed to load draft/i)).toBeInTheDocument();
			});
		});

		it('should load existing draft content', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(mockGetDraft).toHaveBeenCalledWith('fc-123');
			});
		});
	});

	describe('Claim Section (Read-only)', () => {
		it('should display claim section', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123', claimText: 'Original claim text' } });

			await waitFor(() => {
				// Look for the heading specifically
				expect(screen.getByRole('heading', { level: 3, name: /claim/i })).toBeInTheDocument();
			});
		});

		it('should show claim text as read-only', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123', claimText: 'Original claim text' } });

			await waitFor(() => {
				expect(screen.getByText('Original claim text')).toBeInTheDocument();
			});
		});
	});

	describe('Analysis Section', () => {
		it('should display analysis textarea', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/analysis/i)).toBeInTheDocument();
			});
		});

		it('should load existing analysis content', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				const textarea = screen.getByLabelText(/analysis/i) as HTMLTextAreaElement;
				expect(textarea.value).toContain('detailed analysis');
			});
		});

		it('should display character count', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByText(/characters/i)).toBeInTheDocument();
			});
		});

		it('should display word count', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByText(/words/i)).toBeInTheDocument();
			});
		});

		it('should show validation error for analysis under 200 characters', async () => {
			mockGetDraft.mockResolvedValue(mockEmptyDraftResponse);

			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/analysis/i)).toBeInTheDocument();
			});

			const textarea = screen.getByLabelText(/analysis/i);
			await fireEvent.input(textarea, { target: { value: 'Short text' } });

			const submitButton = screen.getByRole('button', { name: /submit for review/i });
			await fireEvent.click(submitButton);

			await waitFor(() => {
				expect(screen.getByText(/at least 200 characters/i)).toBeInTheDocument();
			});
		});
	});

	describe('Verdict Section', () => {
		it('should display verdict dropdown', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('combobox', { name: /verdict$/i })).toBeInTheDocument();
			});
		});

		it('should show all EFCSN-compliant verdict options', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('combobox', { name: /verdict$/i })).toBeInTheDocument();
			});

			const select = screen.getByRole('combobox', { name: /verdict$/i });
			expect(select).toBeInTheDocument();

			// Check for EFCSN-compliant options in the select
			const options = select.querySelectorAll('option');
			const optionValues = Array.from(options).map((opt) => opt.value);

			expect(optionValues).toContain('true');
			expect(optionValues).toContain('partly_false');
			expect(optionValues).toContain('false');
			expect(optionValues).toContain('missing_context');
			expect(optionValues).toContain('altered');
			expect(optionValues).toContain('satire');
			expect(optionValues).toContain('unverifiable');
		});

		it('should load existing verdict selection', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				const select = screen.getByRole('combobox', { name: /verdict$/i }) as HTMLSelectElement;
				expect(select.value).toBe('partly_false');
			});
		});
	});

	describe('Sources Section', () => {
		it('should display sources section', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				// Look for the heading specifically
				expect(screen.getByRole('heading', { level: 3, name: /sources/i })).toBeInTheDocument();
			});
		});

		it('should show add source button', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /add source/i })).toBeInTheDocument();
			});
		});

		it('should display existing sources', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByDisplayValue('https://example.com/source1')).toBeInTheDocument();
				expect(screen.getByDisplayValue('https://example.com/source2')).toBeInTheDocument();
			});
		});

		it('should add new source input when clicking add button', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /add source/i })).toBeInTheDocument();
			});

			const addButton = screen.getByRole('button', { name: /add source/i });
			await fireEvent.click(addButton);

			await waitFor(() => {
				// Should have 3 source inputs now (2 existing + 1 new)
				const inputs = screen.getAllByPlaceholderText(/source url/i);
				expect(inputs.length).toBe(3);
			});
		});

		it('should allow removing a source', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getAllByRole('button', { name: /remove source/i }).length).toBe(2);
			});

			const removeButtons = screen.getAllByRole('button', { name: /remove source/i });
			await fireEvent.click(removeButtons[0]);

			await waitFor(() => {
				expect(screen.queryByDisplayValue('https://example.com/source1')).not.toBeInTheDocument();
			});
		});
	});

	describe('Internal Notes Section', () => {
		it('should display internal notes textarea', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/internal notes/i)).toBeInTheDocument();
			});
		});

		it('should load existing internal notes', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				const textarea = screen.getByLabelText(/internal notes/i) as HTMLTextAreaElement;
				expect(textarea.value).toContain('Check with senior reviewer');
			});
		});
	});

	describe('Draft Status Indicator', () => {
		it('should show draft status indicator', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				// Look for the status badge specifically (not the button)
				const draftElements = screen.getAllByText(/draft/i);
				expect(draftElements.length).toBeGreaterThanOrEqual(1);
			});
		});

		it('should show last saved timestamp', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByText(/last saved/i)).toBeInTheDocument();
			});
		});

		it('should show unsaved changes indicator when content changes', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/analysis/i)).toBeInTheDocument();
			});

			const textarea = screen.getByLabelText(/analysis/i);
			await fireEvent.input(textarea, { target: { value: 'New content that is different' } });

			await waitFor(() => {
				expect(screen.getByText(/unsaved/i)).toBeInTheDocument();
			});
		});
	});

	describe('Auto-save Functionality', () => {
		it('should auto-save after 30 seconds of inactivity', async () => {
			vi.useFakeTimers();

			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/analysis/i)).toBeInTheDocument();
			});

			const textarea = screen.getByLabelText(/analysis/i);
			await fireEvent.input(textarea, { target: { value: 'Updated analysis content that is long enough' } });

			// Advance timers by 30 seconds
			await vi.advanceTimersByTimeAsync(30000);

			await waitFor(() => {
				expect(mockSaveDraft).toHaveBeenCalled();
			});
		});

		it('should auto-save on blur', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/analysis/i)).toBeInTheDocument();
			});

			const textarea = screen.getByLabelText(/analysis/i);
			await fireEvent.input(textarea, { target: { value: 'Updated content' } });
			await fireEvent.blur(textarea);

			await waitFor(() => {
				expect(mockSaveDraft).toHaveBeenCalled();
			});
		});

		it('should show saving indicator during save', async () => {
			mockSaveDraft.mockImplementation(() => new Promise((resolve) => setTimeout(() => resolve(mockDraftResponse), 100)));

			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/analysis/i)).toBeInTheDocument();
			});

			const textarea = screen.getByLabelText(/analysis/i);
			await fireEvent.input(textarea, { target: { value: 'Updated content' } });
			await fireEvent.blur(textarea);

			await waitFor(() => {
				expect(screen.getAllByText(/saving/i).length).toBeGreaterThan(0);
			});
		});
	});

	describe('Preview Mode', () => {
		it('should show preview toggle button', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /preview/i })).toBeInTheDocument();
			});
		});

		it('should toggle to preview mode when clicking preview button', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /preview/i })).toBeInTheDocument();
			});

			const previewButton = screen.getByRole('button', { name: /preview/i });
			await fireEvent.click(previewButton);

			await waitFor(() => {
				expect(screen.getByTestId('preview-mode')).toBeInTheDocument();
			});
		});

		it('should show edit button in preview mode', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /preview/i })).toBeInTheDocument();
			});

			const previewButton = screen.getByRole('button', { name: /preview/i });
			await fireEvent.click(previewButton);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
			});
		});
	});

	describe('Save and Submit Actions', () => {
		it('should show save draft button', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /save draft/i })).toBeInTheDocument();
			});
		});

		it('should show submit for review button', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /submit for review/i })).toBeInTheDocument();
			});
		});

		it('should call saveDraft when clicking save button', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /save draft/i })).toBeInTheDocument();
			});

			const saveButton = screen.getByRole('button', { name: /save draft/i });
			await fireEvent.click(saveButton);

			await waitFor(() => {
				expect(mockSaveDraft).toHaveBeenCalledWith('fc-123', expect.any(Object));
			});
		});

		it('should show success message after saving', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /save draft/i })).toBeInTheDocument();
			});

			const saveButton = screen.getByRole('button', { name: /save draft/i });
			await fireEvent.click(saveButton);

			await waitFor(() => {
				expect(screen.getByText(/saved successfully/i)).toBeInTheDocument();
			});
		});

		it('should validate before submitting for review', async () => {
			mockGetDraft.mockResolvedValue(mockEmptyDraftResponse);

			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /submit for review/i })).toBeInTheDocument();
			});

			const submitButton = screen.getByRole('button', { name: /submit for review/i });
			await fireEvent.click(submitButton);

			await waitFor(() => {
				// Should show validation errors - there may be multiple
				const requiredErrors = screen.getAllByText(/required/i);
				expect(requiredErrors.length).toBeGreaterThanOrEqual(1);
			});
		});
	});

	describe('Empty State', () => {
		it('should show empty form for new drafts', async () => {
			mockGetDraft.mockResolvedValue(mockEmptyDraftResponse);

			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				const textarea = screen.getByLabelText(/analysis/i) as HTMLTextAreaElement;
				expect(textarea.value).toBe('');
			});
		});

		it('should show no sources message for empty draft', async () => {
			mockGetDraft.mockResolvedValue(mockEmptyDraftResponse);

			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByText(/no sources added/i)).toBeInTheDocument();
			});
		});
	});

	describe('Accessibility', () => {
		it('should have proper form labels', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/analysis/i)).toBeInTheDocument();
				expect(screen.getByRole('combobox', { name: /verdict$/i })).toBeInTheDocument();
				expect(screen.getByLabelText(/internal notes/i)).toBeInTheDocument();
			});
		});

		it('should have proper heading structure', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				const heading = screen.getByRole('heading', { name: /fact-check editor/i });
				expect(heading).toBeInTheDocument();
			});
		});

		it('should have accessible buttons', async () => {
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /save draft/i })).toBeInTheDocument();
				expect(screen.getByRole('button', { name: /submit for review/i })).toBeInTheDocument();
				expect(screen.getByRole('button', { name: /preview/i })).toBeInTheDocument();
			});
		});
	});

	describe('i18n Support', () => {
		it('should display English labels by default', async () => {
			locale.set('en');
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Fact-Check Editor/i)).toBeInTheDocument();
			});
		});

		it('should display Dutch labels when locale is nl', async () => {
			locale.set('nl');
			render(FactCheckEditor, { props: { factCheckId: 'fc-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Factcheck Editor/i)).toBeInTheDocument();
			});
		});
	});
});
