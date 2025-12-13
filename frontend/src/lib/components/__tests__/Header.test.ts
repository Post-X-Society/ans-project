import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Header from '../Header.svelte';

describe('Header', () => {
	it('should render the app logo and title', () => {
		render(Header);

		// Check for app title
		expect(screen.getByRole('heading', { name: /ans/i })).toBeInTheDocument();
	});

	it('should render as a header element', () => {
		const { container } = render(Header);

		const header = container.querySelector('header');
		expect(header).toBeInTheDocument();
	});

	it('should have proper styling classes', () => {
		const { container } = render(Header);

		const header = container.querySelector('header');
		expect(header).toHaveClass('bg-primary-600');
	});

	it('should display the tagline', () => {
		render(Header);

		expect(screen.getByText(/AI-powered fact-checking/i)).toBeInTheDocument();
	});
});
