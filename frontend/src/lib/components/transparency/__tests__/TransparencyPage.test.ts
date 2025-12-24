/**
 * TransparencyPage Component Tests (TDD)
 *
 * Issue #85: Frontend: Public Transparency Pages
 * These tests are written FIRST before implementing the component.
 */

import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import TransparencyPage from '../TransparencyPage.svelte';
import type { TransparencyPage as TransparencyPageType } from '$lib/api/types';

// Mock the API
vi.mock('$lib/api/transparency', () => ({
	getTransparencyPage: vi.fn(),
	TRANSPARENCY_PAGE_SLUGS: [
		'methodology',
		'organization',
		'team',
		'funding',
		'partnerships',
		'corrections-policy',
		'privacy-policy'
	],
	isValidTransparencySlug: vi.fn((slug: string) =>
		[
			'methodology',
			'organization',
			'team',
			'funding',
			'partnerships',
			'corrections-policy',
			'privacy-policy'
		].includes(slug)
	)
}));

// Get the mocked function
import { getTransparencyPage } from '$lib/api/transparency';
const mockedGetTransparencyPage = vi.mocked(getTransparencyPage);

// Sample page data
const mockPage: TransparencyPageType = {
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

describe('TransparencyPage', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
	});

	it('should display loading state initially', () => {
		// Make the promise never resolve to test loading state
		mockedGetTransparencyPage.mockImplementation(
			() => new Promise(() => {})
		);

		render(TransparencyPage, { props: { slug: 'methodology' } });

		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it('should render page title in current language', async () => {
		mockedGetTransparencyPage.mockResolvedValue(mockPage);

		const { container } = render(TransparencyPage, { props: { slug: 'methodology' } });

		await waitFor(() => {
			// Get the h1 in the header specifically (page title, not markdown content)
			const headerH1 = container.querySelector('header h1');
			expect(headerH1).toHaveTextContent('Our Methodology');
		});
	});

	it('should render markdown content', async () => {
		mockedGetTransparencyPage.mockResolvedValue(mockPage);

		render(TransparencyPage, { props: { slug: 'methodology' } });

		await waitFor(() => {
			// Check that markdown is rendered (heading becomes h1)
			expect(screen.getByText('How We Fact-Check')).toBeInTheDocument();
		});
	});

	it('should display last updated timestamp', async () => {
		mockedGetTransparencyPage.mockResolvedValue(mockPage);

		render(TransparencyPage, { props: { slug: 'methodology' } });

		await waitFor(() => {
			// Should show formatted date
			expect(screen.getByText(/last updated/i)).toBeInTheDocument();
		});
	});

	it('should display version number', async () => {
		mockedGetTransparencyPage.mockResolvedValue(mockPage);

		render(TransparencyPage, { props: { slug: 'methodology' } });

		await waitFor(() => {
			expect(screen.getByText(/version 2/i)).toBeInTheDocument();
		});
	});

	it('should display error state when API fails', async () => {
		mockedGetTransparencyPage.mockRejectedValue(new Error('API Error'));

		render(TransparencyPage, { props: { slug: 'methodology' } });

		await waitFor(() => {
			// Check for error heading and error message
			expect(screen.getByRole('heading', { name: 'Error' })).toBeInTheDocument();
			expect(screen.getByText('API Error')).toBeInTheDocument();
		});
	});

	it('should display content in Dutch when locale is nl', async () => {
		locale.set('nl');
		mockedGetTransparencyPage.mockResolvedValue(mockPage);

		const { container } = render(TransparencyPage, { props: { slug: 'methodology' } });

		await waitFor(() => {
			// Get the h1 in the header specifically (page title, not markdown content)
			const headerH1 = container.querySelector('header h1');
			expect(headerH1).toHaveTextContent('Onze Methodologie');
		});
	});

	it('should have proper article structure for accessibility', async () => {
		mockedGetTransparencyPage.mockResolvedValue(mockPage);

		const { container } = render(TransparencyPage, { props: { slug: 'methodology' } });

		await waitFor(() => {
			const article = container.querySelector('article');
			expect(article).toBeInTheDocument();
		});
	});

	it('should apply prose styling to markdown content', async () => {
		mockedGetTransparencyPage.mockResolvedValue(mockPage);

		const { container } = render(TransparencyPage, { props: { slug: 'methodology' } });

		await waitFor(() => {
			// Check for prose class from Tailwind typography
			const proseElement = container.querySelector('.prose');
			expect(proseElement).toBeInTheDocument();
		});
	});
});
