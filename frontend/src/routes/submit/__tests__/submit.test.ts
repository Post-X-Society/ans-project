import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import SubmitPageTest from './SubmitPageTest.svelte';

// Mock the API
vi.mock('$lib/api/submissions', () => ({
	createSubmission: vi.fn().mockResolvedValue({
		id: '123',
		content: 'Test',
		submission_type: 'text',
		status: 'pending',
		user_id: null,
		created_at: '2025-01-01',
		updated_at: '2025-01-01'
	})
}));

describe('Submit Page', () => {
	it('should render the page heading', () => {
		render(SubmitPageTest);

		const heading = screen.getByRole('heading', { name: /submit.*snapchat.*spotlight/i });
		expect(heading).toBeInTheDocument();
	});

	it('should display a description about submitting Spotlight content', () => {
		render(SubmitPageTest);

		// Should have paragraph mentioning automatically fetch
		expect(screen.getByText(/automatically fetch.*video.*metadata/i)).toBeInTheDocument();
	});

	it('should render the submission form', () => {
		render(SubmitPageTest);

		// Form should be present with input field for Spotlight link and button
		expect(screen.getByLabelText(/snapchat.*spotlight.*link/i)).toBeInTheDocument();
		// When not authenticated, button shows "Please login to submit"
		expect(screen.getByRole('button', { name: /please login to submit/i })).toBeInTheDocument();
	});

	it('should render in a container', () => {
		const { container } = render(SubmitPageTest);

		const wrapper = container.querySelector('.container');
		expect(wrapper).toBeInTheDocument();
	});
});
