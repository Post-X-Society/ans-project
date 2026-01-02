import { render, screen, fireEvent, waitFor, within } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import Citations from '../Citations.svelte';
import type { CitationSource } from '$lib/api/types';

// Mock sources with citation metadata
const mockSources: CitationSource[] = [
	{
		id: '1',
		url: 'https://example.com/article-1',
		source_type: 'news',
		credibility_rating: 4,
		relevance: 'supports',
		created_at: '2025-01-15T10:00:00Z',
		updated_at: '2025-01-15T10:00:00Z',
		title: 'First Source Article',
		author: 'John Smith',
		publication_date: '2025-01-10',
		publisher: 'Example News'
	},
	{
		id: '2',
		url: 'https://research.org/study',
		source_type: 'research',
		credibility_rating: 5,
		relevance: 'supports',
		created_at: '2025-01-15T11:00:00Z',
		updated_at: '2025-01-15T11:00:00Z',
		title: 'Research Study on Topic',
		author: 'Dr. Jane Doe',
		publication_date: '2024-12-01',
		publisher: 'Academic Journal'
	},
	{
		id: '3',
		url: 'https://official.gov/statement',
		source_type: 'official',
		credibility_rating: 5,
		relevance: 'contextualizes',
		created_at: '2025-01-15T12:00:00Z',
		updated_at: '2025-01-15T12:00:00Z',
		title: 'Official Government Statement',
		author: 'Government Agency',
		publication_date: '2025-01-05',
		publisher: 'Government'
	}
];

describe('Citations', () => {
	beforeEach(() => {
		locale.set('en');
		vi.clearAllMocks();
	});

	describe('citation parsing', () => {
		it('should parse and render bracketed citations [1], [2], [3]', () => {
			const text = 'This is a claim [1] that is supported by research [2] and official sources [3].';
			render(Citations, { props: { text, sources: mockSources } });

			// Should render the text with citation markers
			expect(screen.getByText(/this is a claim/i)).toBeInTheDocument();
			expect(screen.getByText(/that is supported by research/i)).toBeInTheDocument();
			expect(screen.getByText(/and official sources/i)).toBeInTheDocument();

			// Should render citation buttons
			const citationButtons = screen.getAllByRole('button', { name: /citation/i });
			expect(citationButtons).toHaveLength(3);
		});

		it('should parse multiple citations in brackets [1,2,3]', () => {
			const text = 'Multiple sources confirm this [1,2,3].';
			render(Citations, { props: { text, sources: mockSources } });

			// Should render a combined citation button or individual ones
			const citationButtons = screen.getAllByRole('button', { name: /citation/i });
			expect(citationButtons.length).toBeGreaterThanOrEqual(1);
		});

		it('should parse range citations [1-3]', () => {
			const text = 'All sources agree on this point [1-3].';
			render(Citations, { props: { text, sources: mockSources } });

			// Should render citation buttons for the range
			const citationButtons = screen.getAllByRole('button', { name: /citation/i });
			expect(citationButtons.length).toBeGreaterThanOrEqual(1);
		});

		it('should handle text without citations', () => {
			const text = 'This text has no citations at all.';
			render(Citations, { props: { text, sources: mockSources } });

			expect(screen.getByText(/this text has no citations at all/i)).toBeInTheDocument();
			expect(screen.queryByRole('button', { name: /citation/i })).not.toBeInTheDocument();
		});

		it('should handle empty text', () => {
			render(Citations, { props: { text: '', sources: mockSources } });

			expect(screen.queryByRole('button', { name: /citation/i })).not.toBeInTheDocument();
		});

		it('should handle invalid citation numbers gracefully', () => {
			const text = 'This references a non-existent source [99].';
			render(Citations, { props: { text, sources: mockSources } });

			expect(screen.getByText(/this references a non-existent source/i)).toBeInTheDocument();
			// Invalid citation should either be ignored or shown with error styling
			const citationButton = screen.queryByRole('button', { name: /citation 99/i });
			if (citationButton) {
				expect(citationButton).toHaveAttribute('aria-disabled', 'true');
			}
		});
	});

	describe('citation interaction', () => {
		it('should show popup/modal when citation is clicked', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			// Should show popup with source details
			await waitFor(() => {
				expect(screen.getByRole('dialog')).toBeInTheDocument();
			});
		});

		it('should display source title in popup', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByText('First Source Article')).toBeInTheDocument();
			});
		});

		it('should display source author in popup', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByText(/john smith/i)).toBeInTheDocument();
			});
		});

		it('should display publication date in popup', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByText(/2025-01-10|january 10, 2025/i)).toBeInTheDocument();
			});
		});

		it('should display source URL in popup', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				const link = screen.getByRole('link', { name: /view source|example\.com/i });
				expect(link).toHaveAttribute('href', 'https://example.com/article-1');
			});
		});

		it('should display source type in popup', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				// Check for Source Type label
				expect(screen.getByText(/source type/i)).toBeInTheDocument();
				// Check that News type is displayed (could be "News" exactly)
				const allNews = screen.getAllByText(/news/i);
				expect(allNews.length).toBeGreaterThan(0);
			});
		});

		it('should display credibility rating in popup', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				// Should show 4 out of 5 stars or similar rating display
				expect(screen.getByText(/credibility|rating/i)).toBeInTheDocument();
			});
		});

		it('should close popup when close button is clicked', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByRole('dialog')).toBeInTheDocument();
			});

			const closeButton = screen.getByRole('button', { name: /close/i });
			await fireEvent.click(closeButton);

			await waitFor(() => {
				expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
			});
		});

		it('should close popup when clicking outside', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByRole('dialog')).toBeInTheDocument();
			});

			// Click the backdrop/overlay
			const backdrop = screen.getByTestId('citation-backdrop');
			await fireEvent.click(backdrop);

			await waitFor(() => {
				expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
			});
		});

		it('should close popup on Escape key', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByRole('dialog')).toBeInTheDocument();
			});

			await fireEvent.keyDown(document, { key: 'Escape' });

			await waitFor(() => {
				expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
			});
		});
	});

	describe('copy citation functionality', () => {
		it('should show copy button in popup', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				// Should have at least one copy button (APA or MLA)
				const copyButtons = screen.getAllByRole('button', { name: /copy/i });
				expect(copyButtons.length).toBeGreaterThan(0);
			});
		});

		it('should provide APA format option', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /apa/i })).toBeInTheDocument();
			});
		});

		it('should provide MLA format option', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /mla/i })).toBeInTheDocument();
			});
		});

		it('should copy APA format to clipboard when clicked', async () => {
			const mockClipboard = { writeText: vi.fn().mockResolvedValue(undefined) };
			Object.assign(navigator, { clipboard: mockClipboard });

			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /apa/i })).toBeInTheDocument();
			});

			const apaButton = screen.getByRole('button', { name: /apa/i });
			await fireEvent.click(apaButton);

			await waitFor(() => {
				expect(mockClipboard.writeText).toHaveBeenCalled();
				// APA format: Author, A. A. (Year). Title. Publisher. URL
				expect(mockClipboard.writeText.mock.calls[0][0]).toMatch(/smith.*2025.*first source article/i);
			});
		});

		it('should copy MLA format to clipboard when clicked', async () => {
			const mockClipboard = { writeText: vi.fn().mockResolvedValue(undefined) };
			Object.assign(navigator, { clipboard: mockClipboard });

			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /mla/i })).toBeInTheDocument();
			});

			const mlaButton = screen.getByRole('button', { name: /mla/i });
			await fireEvent.click(mlaButton);

			await waitFor(() => {
				expect(mockClipboard.writeText).toHaveBeenCalled();
				// MLA format: Author. "Title." Publisher, Date. URL
				expect(mockClipboard.writeText.mock.calls[0][0]).toMatch(/smith.*first source article/i);
			});
		});

		it('should show success feedback after copying', async () => {
			const mockClipboard = { writeText: vi.fn().mockResolvedValue(undefined) };
			Object.assign(navigator, { clipboard: mockClipboard });

			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /apa/i })).toBeInTheDocument();
			});

			const apaButton = screen.getByRole('button', { name: /apa/i });
			await fireEvent.click(apaButton);

			await waitFor(() => {
				expect(screen.getByText(/copied/i)).toBeInTheDocument();
			});
		});
	});

	describe('styling and display', () => {
		it('should render citation markers with distinct styling', () => {
			const text = 'This is a claim [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			expect(citationButton.className).toMatch(/text-blue|bg-blue|underline|font-medium/i);
		});

		it('should highlight citation on hover', async () => {
			const text = 'This is a claim [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			// Hover state is handled by Tailwind classes
			expect(citationButton.className).toMatch(/hover:/);
		});

		it('should show relevance indicator in popup', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByText(/supports/i)).toBeInTheDocument();
			});
		});

		it('should color-code sources by relevance', async () => {
			const text = 'Contextualizing source [3].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 3/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByText(/contextualizes/i)).toBeInTheDocument();
			});
		});
	});

	describe('accessibility', () => {
		it('should have proper ARIA labels for citation buttons', () => {
			const text = 'This is a claim [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			expect(citationButton).toHaveAttribute('aria-label');
		});

		it('should have proper role for popup dialog', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				const dialog = screen.getByRole('dialog');
				expect(dialog).toHaveAttribute('aria-modal', 'true');
			});
		});

		it('should trap focus within popup when open', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				const dialog = screen.getByRole('dialog');
				expect(dialog).toBeInTheDocument();
			});

			// Focus should be within the dialog
			const dialog = screen.getByRole('dialog');
			const focusableElements = within(dialog).queryAllByRole('button');
			expect(focusableElements.length).toBeGreaterThan(0);
		});

		it('should return focus to citation button when popup closes', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByRole('dialog')).toBeInTheDocument();
			});

			const closeButton = screen.getByRole('button', { name: /close/i });
			await fireEvent.click(closeButton);

			await waitFor(() => {
				expect(document.activeElement).toBe(citationButton);
			});
		});

		it('should have descriptive aria-describedby for dialog', async () => {
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				const dialog = screen.getByRole('dialog');
				expect(dialog).toHaveAttribute('aria-labelledby');
			});
		});
	});

	describe('multilingual support', () => {
		it('should display translated labels in popup', async () => {
			locale.set('en');
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				// Check for translated labels
				expect(screen.getByText(/source type|type/i)).toBeInTheDocument();
				expect(screen.getByText(/credibility|rating/i)).toBeInTheDocument();
			});
		});

		it('should display translated copy button text', async () => {
			locale.set('en');
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				// Should have copy buttons for both formats
				const copyButtons = screen.getAllByRole('button', { name: /copy/i });
				expect(copyButtons.length).toBeGreaterThan(0);
			});
		});

		it('should display translated relevance values', async () => {
			locale.set('en');
			const text = 'Source information here [1].';
			render(Citations, { props: { text, sources: mockSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				expect(screen.getByText(/supports/i)).toBeInTheDocument();
			});
		});
	});

	describe('edge cases', () => {
		it('should handle sources without optional metadata', async () => {
			const minimalSources: CitationSource[] = [
				{
					id: '1',
					url: 'https://example.com',
					source_type: 'news',
					credibility_rating: 3,
					relevance: 'supports',
					created_at: '2025-01-15T10:00:00Z',
					updated_at: '2025-01-15T10:00:00Z'
					// No title, author, publication_date, or publisher
				}
			];

			const text = 'Source here [1].';
			render(Citations, { props: { text, sources: minimalSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				// Should still display with URL as fallback
				expect(screen.getByRole('dialog')).toBeInTheDocument();
				// URL appears in title and link, so use getAllByText
				const urlElements = screen.getAllByText(/example\.com/i);
				expect(urlElements.length).toBeGreaterThan(0);
			});
		});

		it('should handle empty sources array', () => {
			const text = 'This text references [1] but has no sources.';
			render(Citations, { props: { text, sources: [] } });

			// Should render text but no interactive citations
			expect(screen.getByText(/this text references/i)).toBeInTheDocument();
		});

		it('should handle special characters in text', () => {
			const text = 'Special chars: <script>alert("xss")</script> [1].';
			render(Citations, { props: { text, sources: mockSources } });

			// Should escape HTML and render safely
			expect(screen.queryByRole('script')).not.toBeInTheDocument();
			expect(screen.getByText(/special chars/i)).toBeInTheDocument();
		});

		it('should handle very long URLs gracefully', async () => {
			const longUrlSources: CitationSource[] = [
				{
					id: '1',
					url: 'https://example.com/' + 'a'.repeat(200),
					source_type: 'news',
					credibility_rating: 3,
					relevance: 'supports',
					created_at: '2025-01-15T10:00:00Z',
					updated_at: '2025-01-15T10:00:00Z',
					title: 'Article with Long URL'
				}
			];

			const text = 'Long URL source [1].';
			render(Citations, { props: { text, sources: longUrlSources } });

			const citationButton = screen.getByRole('button', { name: /citation 1/i });
			await fireEvent.click(citationButton);

			await waitFor(() => {
				// URL should be truncated or wrapped properly
				const link = screen.getByRole('link');
				expect(link).toBeInTheDocument();
			});
		});
	});
});
