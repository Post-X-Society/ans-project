import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Layout from '../+layout.svelte';

describe('Layout Integration', () => {
	it('should render Header component', () => {
		render(Layout);

		// Header should have the app title
		expect(screen.getByRole('heading', { name: /ans/i })).toBeInTheDocument();
	});

	it('should render Nav component', () => {
		render(Layout);

		// Nav should have all three links
		expect(screen.getByRole('link', { name: /home/i })).toBeInTheDocument();
		expect(screen.getByRole('link', { name: /submit/i })).toBeInTheDocument();
		expect(screen.getByRole('link', { name: /admin/i })).toBeInTheDocument();
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
