/**
 * TransparencyEditor Component Tests (TDD)
 *
 * Issue #86: Frontend: Admin Transparency Page Editor
 * EPIC #51: Transparency & Methodology Pages
 *
 * These tests are written FIRST before implementing the component.
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import TransparencyEditor from '../TransparencyEditor.svelte';
import type { TransparencyPage, TransparencyPageVersion, TransparencyPageDiff } from '$lib/api/types';

// Mock the API functions
vi.mock('$lib/api/transparency', () => ({
	getTransparencyPage: vi.fn(),
	updateTransparencyPage: vi.fn(),
	getTransparencyPageVersions: vi.fn(),
	getTransparencyPageDiff: vi.fn(),
	markTransparencyPageReviewed: vi.fn()
}));

// Mock the auth store
vi.mock('$lib/stores/auth', () => ({
	isAdmin: { subscribe: vi.fn((fn) => { fn(true); return () => {}; }) },
	authStore: { subscribe: vi.fn((fn) => { fn({ user: { id: '123', role: 'admin' } }); return () => {}; }) }
}));

// Get the mocked functions
import {
	getTransparencyPage,
	updateTransparencyPage,
	getTransparencyPageVersions,
	getTransparencyPageDiff,
	markTransparencyPageReviewed
} from '$lib/api/transparency';

const mockedGetPage = vi.mocked(getTransparencyPage);
const mockedUpdatePage = vi.mocked(updateTransparencyPage);
const mockedGetVersions = vi.mocked(getTransparencyPageVersions);
const mockedGetDiff = vi.mocked(getTransparencyPageDiff);
const mockedMarkReviewed = vi.mocked(markTransparencyPageReviewed);

// Sample test data
const mockPage: TransparencyPage = {
	id: '123e4567-e89b-12d3-a456-426614174000',
	slug: 'methodology',
	title: {
		en: 'Our Methodology',
		nl: 'Onze Methodologie'
	},
	content: {
		en: '# How We Fact-Check\n\nWe follow strict standards.',
		nl: '# Hoe Wij Factchecken\n\nWij volgen strikte normen.'
	},
	version: 2,
	last_reviewed: '2025-12-20T10:00:00Z',
	next_review_due: '2026-12-20T10:00:00Z',
	created_at: '2025-01-01T00:00:00Z',
	updated_at: '2025-12-20T10:00:00Z'
};

const mockVersions: TransparencyPageVersion[] = [
	{
		id: 'version-1',
		page_id: '123e4567-e89b-12d3-a456-426614174000',
		version: 1,
		title: { en: 'Our Methodology', nl: 'Onze Methodologie' },
		content: { en: '# Initial Content', nl: '# Initiële Inhoud' },
		changed_by_id: 'user-1',
		change_summary: 'Initial version',
		created_at: '2025-01-01T00:00:00Z'
	}
];

const mockDiff: TransparencyPageDiff = {
	slug: 'methodology',
	from_version: 1,
	to_version: 2,
	diff: {
		en: {
			title: { from: 'Our Methodology', to: 'Our Methodology' },
			content: '- # Initial Content\n+ # How We Fact-Check\n+ \n+ We follow strict standards.'
		}
	},
	language: 'en'
};

describe('TransparencyEditor', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
		mockedGetPage.mockResolvedValue(mockPage);
		mockedGetVersions.mockResolvedValue(mockVersions);
		mockedGetDiff.mockResolvedValue(mockDiff);
		mockedMarkReviewed.mockResolvedValue(mockPage);
		mockedUpdatePage.mockResolvedValue(mockPage);
	});

	describe('Loading and Display', () => {
		it('should display loading state initially', () => {
			mockedGetPage.mockImplementation(() => new Promise(() => {}));

			render(TransparencyEditor, { props: { slug: 'methodology' } });

			expect(screen.getByText(/loading/i)).toBeInTheDocument();
		});

		it('should render page title when loaded', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByText(/our methodology/i)).toBeInTheDocument();
			});
		});

		it('should display error state when API fails', async () => {
			mockedGetPage.mockRejectedValue(new Error('API Error'));

			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				// Check for the error heading specifically
				expect(screen.getByRole('heading', { name: /error/i })).toBeInTheDocument();
				// And the error message
				expect(screen.getByText('API Error')).toBeInTheDocument();
			});
		});
	});

	describe('Language Tabs', () => {
		it('should show language tabs for EN and NL', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByRole('tab', { name: /english/i })).toBeInTheDocument();
				expect(screen.getByRole('tab', { name: /nederlands/i })).toBeInTheDocument();
			});
		});

		it('should switch content when clicking language tabs', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByRole('tab', { name: /english/i })).toBeInTheDocument();
			});

			// Click on Dutch tab
			const nlTab = screen.getByRole('tab', { name: /nederlands/i });
			await fireEvent.click(nlTab);

			// Content should update (we check for any tab state change)
			await waitFor(() => {
				expect(nlTab).toHaveAttribute('aria-selected', 'true');
			});
		});

		it('should have English tab selected by default', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				const enTab = screen.getByRole('tab', { name: /english/i });
				expect(enTab).toHaveAttribute('aria-selected', 'true');
			});
		});
	});

	describe('Markdown Editor', () => {
		it('should display markdown editor area', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				// Editor container should exist
				expect(screen.getByTestId('markdown-editor')).toBeInTheDocument();
			});
		});

		it('should show title input field', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				const titleInput = screen.getByLabelText(/title/i);
				expect(titleInput).toBeInTheDocument();
				expect(titleInput).toHaveValue('Our Methodology');
			});
		});
	});

	describe('Live Preview', () => {
		it('should display live preview pane', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByTestId('preview-pane')).toBeInTheDocument();
			});
		});

		it('should render markdown in preview', async () => {
			const { container } = render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				// The markdown heading should be rendered as h1 in the preview pane
				const previewPane = container.querySelector('[data-testid="preview-pane"]');
				expect(previewPane).toBeInTheDocument();
				// Check that the preview contains the rendered markdown heading
				const h1InPreview = previewPane?.querySelector('h1');
				expect(h1InPreview?.textContent).toBe('How We Fact-Check');
			});
		});
	});

	describe('Version History Sidebar', () => {
		it('should display version history sidebar', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByText(/version history/i)).toBeInTheDocument();
			});
		});

		it('should load and display version history', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(mockedGetVersions).toHaveBeenCalledWith('methodology');
			});

			await waitFor(() => {
				expect(screen.getByText(/version 1/i)).toBeInTheDocument();
				expect(screen.getByText(/initial version/i)).toBeInTheDocument();
			});
		});

		it('should show current version indicator', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				// The current version is shown in the header - check for Version 2
				expect(screen.getByText(/Current.*Version 2/i)).toBeInTheDocument();
			});
		});
	});

	describe('Diff Viewer', () => {
		it('should show compare button for versions', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /compare/i })).toBeInTheDocument();
			});
		});

		it('should display diff viewer when comparing versions', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /compare/i })).toBeInTheDocument();
			});

			const compareButton = screen.getByRole('button', { name: /compare/i });
			await fireEvent.click(compareButton);

			await waitFor(() => {
				expect(mockedGetDiff).toHaveBeenCalled();
			});

			await waitFor(() => {
				expect(screen.getByTestId('diff-viewer')).toBeInTheDocument();
			});
		});
	});

	describe('Mark as Reviewed', () => {
		it('should show mark as reviewed button', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /mark as reviewed/i })).toBeInTheDocument();
			});
		});

		it('should display next review due date', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByText(/next review/i)).toBeInTheDocument();
			});
		});

		it('should call API when mark as reviewed is clicked', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /mark as reviewed/i })).toBeInTheDocument();
			});

			const reviewButton = screen.getByRole('button', { name: /mark as reviewed/i });
			await fireEvent.click(reviewButton);

			await waitFor(() => {
				expect(mockedMarkReviewed).toHaveBeenCalledWith('methodology');
			});
		});
	});

	describe('Save Changes', () => {
		it('should show save button', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
			});
		});

		it('should require change summary before saving', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/change summary/i)).toBeInTheDocument();
			});
		});

		it('should call update API when saving', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
			});

			// Enter change summary
			const summaryInput = screen.getByLabelText(/change summary/i);
			await fireEvent.input(summaryInput, { target: { value: 'Updated content' } });

			// Click save
			const saveButton = screen.getByRole('button', { name: /save/i });
			await fireEvent.click(saveButton);

			await waitFor(() => {
				expect(mockedUpdatePage).toHaveBeenCalled();
			});
		});

		it('should show success message after saving', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
			});

			// Enter change summary
			const summaryInput = screen.getByLabelText(/change summary/i);
			await fireEvent.input(summaryInput, { target: { value: 'Updated content' } });

			// Click save
			const saveButton = screen.getByRole('button', { name: /save/i });
			await fireEvent.click(saveButton);

			await waitFor(() => {
				expect(screen.getByText(/saved successfully/i)).toBeInTheDocument();
			});
		});
	});

	describe('Accessibility', () => {
		it('should have proper heading structure', async () => {
			const { container } = render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				// Check for main page heading in header
				const headerH1 = container.querySelector('header h1');
				expect(headerH1).toBeInTheDocument();
				expect(headerH1?.textContent).toContain('Edit Transparency Page');
			});
		});

		it('should have accessible tab panel', async () => {
			render(TransparencyEditor, { props: { slug: 'methodology' } });

			await waitFor(() => {
				const tabList = screen.getByRole('tablist');
				expect(tabList).toBeInTheDocument();
			});
		});
	});
});
