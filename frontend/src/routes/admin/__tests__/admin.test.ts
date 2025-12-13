import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import AdminPage from '../+page.svelte';

describe('Admin Page', () => {
	it('should render the page heading', () => {
		render(AdminPage);

		const heading = screen.getByRole('heading', { name: /admin/i });
		expect(heading).toBeInTheDocument();
	});

	it('should display coming soon message', () => {
		render(AdminPage);

		expect(screen.getByText(/coming soon/i)).toBeInTheDocument();
	});

	it('should render in a container', () => {
		const { container } = render(AdminPage);

		const wrapper = container.querySelector('.container');
		expect(wrapper).toBeInTheDocument();
	});

	it('should have centered content', () => {
		const { container } = render(AdminPage);

		const centerWrapper = container.querySelector('.text-center');
		expect(centerWrapper).toBeInTheDocument();
	});
});
