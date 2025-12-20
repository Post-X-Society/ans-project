import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Nav from '../Nav.svelte';

// Mock $app/stores
vi.mock('$app/stores', () => ({
	page: {
		subscribe: (fn: (value: any) => void) => {
			fn({ url: { pathname: '/' } });
			return () => {};
		}
	}
}));

// Mock $app/navigation
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

// Mock auth API
vi.mock('$lib/api/auth', () => ({
	logout: vi.fn().mockResolvedValue({})
}));

describe('Nav', () => {
	it('should render as a nav element', () => {
		const { container } = render(Nav);

		const nav = container.querySelector('nav');
		expect(nav).toBeInTheDocument();
	});

	it('should render Home link', () => {
		render(Nav);

		const homeLink = screen.getByRole('link', { name: /^home$/i });
		expect(homeLink).toBeInTheDocument();
		expect(homeLink).toHaveAttribute('href', '/');
	});

	it('should render Login and Register links when not authenticated', () => {
		render(Nav);

		const loginLink = screen.getByRole('link', { name: /^login$/i });
		expect(loginLink).toBeInTheDocument();
		expect(loginLink).toHaveAttribute('href', '/login');

		const registerLink = screen.getByRole('link', { name: /^register$/i });
		expect(registerLink).toBeInTheDocument();
		expect(registerLink).toHaveAttribute('href', '/register');
	});

	it('should not render Submit link when not authenticated', () => {
		render(Nav);

		const submitLink = screen.queryByRole('link', { name: /^submit$/i });
		expect(submitLink).not.toBeInTheDocument();
	});

	it('should not render Admin link when not authenticated and not admin', () => {
		render(Nav);

		const adminLink = screen.queryByRole('link', { name: /^admin$/i });
		expect(adminLink).not.toBeInTheDocument();
	});
});
