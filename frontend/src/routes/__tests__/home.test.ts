import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import HomePage from '../+page.svelte';

describe('Home Page', () => {
	it('should render the welcome heading', () => {
		render(HomePage);

		const heading = screen.getByRole('heading', { name: /welcome to ans/i });
		expect(heading).toBeInTheDocument();
	});

	it('should display the platform description', () => {
		render(HomePage);

		expect(screen.getByText(/AI-powered fact-checking platform/i)).toBeInTheDocument();
	});

	it('should have a call-to-action button to submit page', () => {
		render(HomePage);

		const ctaLink = screen.getByRole('link', { name: /submit a claim/i });
		expect(ctaLink).toBeInTheDocument();
		expect(ctaLink).toHaveAttribute('href', '/submit');
	});

	it('should have centered layout', () => {
		const { container } = render(HomePage);

		const wrapper = container.querySelector('.flex.items-center.justify-center');
		expect(wrapper).toBeInTheDocument();
	});

	it('should display content in the correct semantic structure', () => {
		render(HomePage);

		// Should have exactly one h1
		const headings = screen.getAllByRole('heading', { level: 1 });
		expect(headings).toHaveLength(1);
	});
});
