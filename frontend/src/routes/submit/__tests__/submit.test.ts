import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import SubmitPage from '../+page.svelte';

describe('Submit Page', () => {
	it('should render the page heading', () => {
		render(SubmitPage);

		const heading = screen.getByRole('heading', { name: /submit.*claim/i });
		expect(heading).toBeInTheDocument();
	});

	it('should display a description about submitting claims', () => {
		render(SubmitPage);

		// Should have paragraph with AI and verified text
		expect(screen.getByText(/AI.*analyze.*verified/i)).toBeInTheDocument();
	});

	it('should have a placeholder message for the form', () => {
		render(SubmitPage);

		// Since this is just a placeholder, expect "coming soon" or similar
		expect(screen.getByText(/form.*coming soon|placeholder/i)).toBeInTheDocument();
	});

	it('should render in a container', () => {
		const { container } = render(SubmitPage);

		const wrapper = container.querySelector('.container');
		expect(wrapper).toBeInTheDocument();
	});
});
