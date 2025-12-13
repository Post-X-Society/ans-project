import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Nav from '../Nav.svelte';

describe('Nav', () => {
	it('should render as a nav element', () => {
		const { container } = render(Nav);

		const nav = container.querySelector('nav');
		expect(nav).toBeInTheDocument();
	});

	it('should render Home link', () => {
		render(Nav);

		const homeLink = screen.getByRole('link', { name: /home/i });
		expect(homeLink).toBeInTheDocument();
		expect(homeLink).toHaveAttribute('href', '/');
	});

	it('should render Submit link', () => {
		render(Nav);

		const submitLink = screen.getByRole('link', { name: /submit/i });
		expect(submitLink).toBeInTheDocument();
		expect(submitLink).toHaveAttribute('href', '/submit');
	});

	it('should render Admin link', () => {
		render(Nav);

		const adminLink = screen.getByRole('link', { name: /admin/i });
		expect(adminLink).toBeInTheDocument();
		expect(adminLink).toHaveAttribute('href', '/admin');
	});

	it('should have all three navigation links', () => {
		render(Nav);

		const links = screen.getAllByRole('link');
		expect(links).toHaveLength(3);
	});
});
