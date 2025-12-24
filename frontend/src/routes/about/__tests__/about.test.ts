/**
 * About Page Route Tests
 *
 * Issue #85: Frontend: Public Transparency Pages
 */

import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import AboutLayout from '../+layout.svelte';

// Mock the page store
vi.mock('$app/stores', () => ({
	page: {
		subscribe: vi.fn((cb) => {
			cb({ params: { slug: 'methodology' } });
			return () => {};
		})
	}
}));

describe('About Layout', () => {
	beforeEach(() => {
		locale.set('en');
	});

	it('should render the transparency navigation', () => {
		render(AboutLayout);

		// Check for the navigation
		expect(screen.getByRole('navigation', { name: 'Transparency' })).toBeInTheDocument();
	});

	it('should render the language selector', () => {
		render(AboutLayout);

		// Check for language selector
		expect(screen.getByLabelText(/language/i)).toBeInTheDocument();
	});

	it('should render breadcrumb navigation', () => {
		render(AboutLayout);

		// Check for breadcrumb
		const breadcrumb = screen.getByRole('navigation', { name: 'Breadcrumb' });
		expect(breadcrumb).toBeInTheDocument();
		expect(screen.getByText('Home')).toBeInTheDocument();
		// Check for "About Us" within the breadcrumb specifically
		const breadcrumbAboutUs = breadcrumb.querySelector('span.text-gray-900');
		expect(breadcrumbAboutUs).toHaveTextContent('About Us');
	});

	it('should have correct structure with sidebar and main content', () => {
		const { container } = render(AboutLayout);

		// Check for aside (sidebar) element
		const aside = container.querySelector('aside');
		expect(aside).toBeInTheDocument();
	});
});
