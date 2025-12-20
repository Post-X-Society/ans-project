import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import AdminPage from '../+page.svelte';

// Mock the users API
vi.mock('$lib/api/users', () => ({
	getUsers: vi.fn().mockResolvedValue([]),
	createUser: vi.fn().mockResolvedValue({}),
	updateUserRole: vi.fn().mockResolvedValue({}),
	updateUser: vi.fn().mockResolvedValue({})
}));

describe('Admin Page', () => {
	it('should render the page heading', () => {
		render(AdminPage);

		const heading = screen.getByRole('heading', { name: /user management/i });
		expect(heading).toBeInTheDocument();
	});

	it('should display loading state initially', () => {
		render(AdminPage);

		expect(screen.getByText(/loading users/i)).toBeInTheDocument();
	});

	it('should render in a container', () => {
		const { container } = render(AdminPage);

		const wrapper = container.querySelector('.container');
		expect(wrapper).toBeInTheDocument();
	});

	it('should have create user button', () => {
		render(AdminPage);

		const createButton = screen.getByRole('button', { name: /create user/i });
		expect(createButton).toBeInTheDocument();
	});
});
