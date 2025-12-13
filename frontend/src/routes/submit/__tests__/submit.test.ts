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

		const heading = screen.getByRole('heading', { name: /submit.*claim/i });
		expect(heading).toBeInTheDocument();
	});

	it('should display a description about submitting claims', () => {
		render(SubmitPageTest);

		// Should have paragraph with AI and verified text
		expect(screen.getByText(/AI.*analyze.*verified/i)).toBeInTheDocument();
	});

	it('should render the submission form', () => {
		render(SubmitPageTest);

		// Form should be present with textarea and button
		expect(screen.getByLabelText(/claim.*content/i)).toBeInTheDocument();
		expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
	});

	it('should render in a container', () => {
		const { container } = render(SubmitPageTest);

		const wrapper = container.querySelector('.container');
		expect(wrapper).toBeInTheDocument();
	});
});
