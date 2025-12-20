import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import Layout from '../+layout.svelte';

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

describe('Layout Integration', () => {
	it('should render Header component', () => {
		render(Layout);

		// Header should have the app title
		expect(screen.getByRole('heading', { name: /ans/i })).toBeInTheDocument();
	});

	it('should render Nav component', () => {
		render(Layout);

		// Nav should have Home link
		expect(screen.getByRole('link', { name: /^home$/i })).toBeInTheDocument();
		// When not authenticated, Login and Register links should be present
		expect(screen.getByRole('link', { name: /^login$/i })).toBeInTheDocument();
		expect(screen.getByRole('link', { name: /^register$/i })).toBeInTheDocument();
	});

	it('should render Footer component', () => {
		render(Layout);

		// Footer should have copyright
		const currentYear = new Date().getFullYear();
		expect(screen.getByText(new RegExp(`© ${currentYear}`, 'i'))).toBeInTheDocument();
	});

	it('should have proper layout structure (header, nav, main, footer)', () => {
		const { container } = render(Layout);

		expect(container.querySelector('header')).toBeInTheDocument();
		expect(container.querySelector('nav')).toBeInTheDocument();
		expect(container.querySelector('main')).toBeInTheDocument();
		expect(container.querySelector('footer')).toBeInTheDocument();
	});

	it('should render slot content in main', () => {
		const { container } = render(Layout);

		const main = container.querySelector('main');
		expect(main).toBeInTheDocument();
	});
});
