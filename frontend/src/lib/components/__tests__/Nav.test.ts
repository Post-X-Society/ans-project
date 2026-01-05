import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Nav from '../Nav.svelte';
import { authStore } from '$lib/stores/auth';

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

// Helper to set up admin authentication
function setupAdminAuth() {
	authStore.setAuth(
		{
			id: 'admin-1',
			email: 'admin@test.com',
			role: 'admin',
			is_active: true,
			created_at: new Date().toISOString(),
			updated_at: new Date().toISOString()
		},
		'test-token',
		'test-refresh-token'
	);
}

describe('Nav', () => {
	beforeEach(() => {
		// Clear auth state before each test
		authStore.clearAuth();
	});

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

	describe('Admin Dropdown', () => {
		beforeEach(() => {
			setupAdminAuth();
		});

		it('should render Admin dropdown button when authenticated as admin', () => {
			render(Nav);

			const adminButton = screen.getByRole('button', { name: /admin/i });
			expect(adminButton).toBeInTheDocument();
		});

		it('should show Corrections link in admin dropdown when clicked', async () => {
			render(Nav);

			// Click the admin dropdown button
			const adminButton = screen.getByRole('button', { name: /admin/i });
			await fireEvent.click(adminButton);

			// Check for corrections link in dropdown using href to distinguish from main nav "Corrections Log"
			const allCorrectionsLinks = screen.getAllByRole('link', { name: /corrections/i });
			const correctionsLink = allCorrectionsLinks.find(
				(link) => link.getAttribute('href') === '/admin/corrections'
			);
			expect(correctionsLink).toBeInTheDocument();
		});

		it('should show User Management link in admin dropdown', async () => {
			render(Nav);

			const adminButton = screen.getByRole('button', { name: /admin/i });
			await fireEvent.click(adminButton);

			const userManagementLink = screen.getByRole('link', { name: /user management/i });
			expect(userManagementLink).toBeInTheDocument();
			expect(userManagementLink).toHaveAttribute('href', '/admin');
		});

		it('should show Transparency Pages link in admin dropdown', async () => {
			render(Nav);

			const adminButton = screen.getByRole('button', { name: /admin/i });
			await fireEvent.click(adminButton);

			const transparencyLink = screen.getByRole('link', { name: /transparency pages/i });
			expect(transparencyLink).toBeInTheDocument();
			expect(transparencyLink).toHaveAttribute('href', '/admin/transparency');
		});
	});
});
