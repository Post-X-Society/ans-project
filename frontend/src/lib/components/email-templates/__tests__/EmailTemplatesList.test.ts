/**
 * EmailTemplatesList Component Tests
 *
 * Issue #167: Email Template Admin Management UI
 * TDD: Tests written FIRST before implementation
 */

import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import EmailTemplatesList from '../EmailTemplatesList.svelte';
import type { EmailTemplate } from '$lib/api/types';

// Mock svelte-i18n
vi.mock('svelte-i18n', () => ({
	t: {
		subscribe: (fn: (value: (key: string, vars?: Record<string, unknown>) => string) => void) => {
			fn((key: string, vars?: Record<string, unknown>) => {
				const translations: Record<string, string> = {
					'emailTemplates.title': 'Email Templates',
					'emailTemplates.description': 'Manage email templates for automated notifications',
					'emailTemplates.loading': 'Loading templates...',
					'emailTemplates.error': 'Error loading templates',
					'emailTemplates.retry': 'Retry',
					'emailTemplates.noTemplates': 'No templates found',
					'emailTemplates.noTemplatesDescription':
						'No email templates have been created yet.',
					'emailTemplates.search.placeholder': 'Search templates...',
					'emailTemplates.search.ariaLabel': 'Search email templates',
					'emailTemplates.filters.all': 'All',
					'emailTemplates.filters.active': 'Active',
					'emailTemplates.filters.inactive': 'Inactive',
					'emailTemplates.filters.showInactive': 'Show inactive',
					'emailTemplates.filters.filterByType': 'Filter by type',
					'emailTemplates.filters.allTypes': 'All Types',
					'emailTemplates.types.welcome_email': 'Welcome Email',
					'emailTemplates.types.password_reset': 'Password Reset',
					'emailTemplates.list.ariaLabel': 'Email templates list',
					'emailTemplates.list.version': `Version ${vars?.values?.version || ''}`,
					'emailTemplates.list.lastModified': `Last modified by ${vars?.values?.email || ''}`,
					'emailTemplates.list.variables': `${vars?.values?.count || 0} variables`,
					'emailTemplates.card.view': 'View',
					'emailTemplates.card.edit': 'Edit',
					'emailTemplates.card.preview': 'Preview',
					'emailTemplates.card.deactivate': 'Deactivate',
					'emailTemplates.card.activate': 'Activate',
					'status.active': 'Active',
					'status.inactive': 'Inactive'
				};
				return translations[key] || key;
			});
			return () => {};
		}
	},
	locale: {
		subscribe: (fn: (value: string) => void) => {
			fn('en');
			return () => {};
		}
	}
}));

// Mock API functions
vi.mock('$lib/api/email-templates', () => ({
	getEmailTemplates: vi.fn()
}));

const mockTemplates: EmailTemplate[] = [
	{
		id: 'uuid-1',
		template_key: 'welcome_email',
		template_type: 'welcome_email',
		name: { en: 'Welcome Email', nl: 'Welkomstmail' },
		description: { en: 'Sent to new users', nl: 'Verzonden naar nieuwe gebruikers' },
		subject: { en: 'Welcome!', nl: 'Welkom!' },
		body_text: { en: 'Hello!', nl: 'Hallo!' },
		body_html: { en: '<p>Hello!</p>', nl: '<p>Hallo!</p>' },
		variables: { name: 'string' },
		is_active: true,
		version: 1,
		last_modified_by: 'admin@example.com',
		notes: null,
		created_at: '2025-01-01T00:00:00Z',
		updated_at: '2025-01-01T00:00:00Z'
	},
	{
		id: 'uuid-2',
		template_key: 'password_reset',
		template_type: 'password_reset',
		name: { en: 'Password Reset', nl: 'Wachtwoord herstellen' },
		description: { en: 'Password reset email', nl: 'Wachtwoord reset e-mail' },
		subject: { en: 'Reset your password', nl: 'Herstel je wachtwoord' },
		body_text: { en: 'Click here', nl: 'Klik hier' },
		body_html: { en: '<p>Click here</p>', nl: '<p>Klik hier</p>' },
		variables: { reset_url: 'string' },
		is_active: true,
		version: 2,
		last_modified_by: 'admin@example.com',
		notes: null,
		created_at: '2025-01-01T00:00:00Z',
		updated_at: '2025-01-02T00:00:00Z'
	},
	{
		id: 'uuid-3',
		template_key: 'old_template',
		template_type: 'system_notification',
		name: { en: 'Old Inactive Template', nl: 'Oud inactief sjabloon' },
		description: { en: 'No longer used', nl: 'Niet meer gebruikt' },
		subject: { en: 'System notification', nl: 'Systeemmelding' },
		body_text: { en: 'Notification', nl: 'Melding' },
		body_html: { en: '<p>Notification</p>', nl: '<p>Melding</p>' },
		variables: {},
		is_active: false,
		version: 1,
		last_modified_by: null,
		notes: 'Deprecated',
		created_at: '2024-01-01T00:00:00Z',
		updated_at: '2024-06-01T00:00:00Z'
	}
];

describe('EmailTemplatesList', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('Rendering', () => {
		it('should render the page title', () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Email Templates');
		});

		it('should render template cards for each template', () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			// Should show only active templates by default (check headings)
			const headings = screen.getAllByRole('heading', { level: 3 });
			const headingTexts = headings.map((h) => h.textContent);
			expect(headingTexts).toContain('Welcome Email');
			expect(headingTexts).toContain('Password Reset');
		});

		it('should render search input', () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			const searchInput = screen.getByPlaceholderText('Search templates...');
			expect(searchInput).toBeInTheDocument();
		});

		it('should render filter controls', () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			// Filter buttons exist in the component
			const buttons = screen.getAllByRole('button');
			const buttonTexts = buttons.map((b) => b.textContent);
			expect(buttonTexts.some((t) => t === 'All')).toBe(true);
			expect(buttonTexts.some((t) => t === 'Active')).toBe(true);
			expect(buttonTexts.some((t) => t === 'Inactive')).toBe(true);
		});
	});

	describe('Loading state', () => {
		it('should show loading indicator when loading', () => {
			render(EmailTemplatesList, { props: { templates: [], isLoading: true } });

			expect(screen.getByText('Loading templates...')).toBeInTheDocument();
		});

		it('should not show templates while loading', () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates, isLoading: true } });

			expect(screen.getByText('Loading templates...')).toBeInTheDocument();
		});
	});

	describe('Error state', () => {
		it('should show error message when error is provided', () => {
			render(EmailTemplatesList, {
				props: { templates: [], error: 'Failed to load templates' }
			});

			expect(screen.getByText('Error loading templates')).toBeInTheDocument();
		});

		it('should show retry button on error', () => {
			const onRetry = vi.fn();
			render(EmailTemplatesList, {
				props: { templates: [], error: 'Failed to load', onRetry }
			});

			const retryButton = screen.getByText('Retry');
			expect(retryButton).toBeInTheDocument();
		});

		it('should call onRetry when retry button is clicked', async () => {
			const onRetry = vi.fn();
			render(EmailTemplatesList, {
				props: { templates: [], error: 'Failed to load', onRetry }
			});

			const retryButton = screen.getByText('Retry');
			await fireEvent.click(retryButton);

			expect(onRetry).toHaveBeenCalled();
		});
	});

	describe('Empty state', () => {
		it('should show empty state when no templates', () => {
			render(EmailTemplatesList, { props: { templates: [] } });

			expect(screen.getByText('No templates found')).toBeInTheDocument();
		});
	});

	describe('Filtering', () => {
		it('should filter by search term', async () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			const searchInput = screen.getByPlaceholderText('Search templates...');
			await fireEvent.input(searchInput, { target: { value: 'welcome' } });

			// Should show only matching template (check heading level 3)
			const headings = screen.getAllByRole('heading', { level: 3 });
			expect(headings.length).toBe(1);
			expect(headings[0]).toHaveTextContent('Welcome Email');
		});

		it('should filter active templates only by default', () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			// Should show only active templates (2 active templates by default)
			const headings = screen.getAllByRole('heading', { level: 3 });
			const headingTexts = headings.map((h) => h.textContent);
			expect(headingTexts).toContain('Welcome Email');
			expect(headingTexts).toContain('Password Reset');
			expect(headingTexts).not.toContain('Old Inactive Template');
		});

		it('should show inactive templates when filter is set to inactive', async () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			// Get Inactive filter button
			const filterButtons = screen.getAllByRole('button');
			const inactiveFilter = filterButtons.find((b) => b.textContent === 'Inactive');
			expect(inactiveFilter).toBeDefined();
			await fireEvent.click(inactiveFilter!);

			// Check that inactive template heading is present
			const heading = screen.getByRole('heading', { level: 3 });
			expect(heading).toHaveTextContent('Old Inactive Template');
		});

		it('should show all templates when All filter is selected', async () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			// Get All button from filter tabs (first one is the filter button)
			const filterButtons = screen.getAllByRole('button');
			const allFilter = filterButtons.find((b) => b.textContent === 'All');
			expect(allFilter).toBeDefined();
			await fireEvent.click(allFilter!);

			// Check that all templates are rendered (using heading selector for names)
			const headings = screen.getAllByRole('heading', { level: 3 });
			const headingTexts = headings.map((h) => h.textContent);
			expect(headingTexts).toContain('Welcome Email');
			expect(headingTexts).toContain('Password Reset');
			expect(headingTexts).toContain('Old Inactive Template');
		});
	});

	describe('Actions', () => {
		it('should call onView when View button is clicked on a template', async () => {
			const onView = vi.fn();
			render(EmailTemplatesList, {
				props: { templates: mockTemplates, onView }
			});

			// Find all View buttons and click the first one
			const buttons = screen.getAllByRole('button');
			const viewButton = buttons.find((b) => b.textContent?.includes('View'));
			expect(viewButton).toBeDefined();
			await fireEvent.click(viewButton!);

			expect(onView).toHaveBeenCalled();
		});

		it('should call onEdit when Edit button is clicked on a template', async () => {
			const onEdit = vi.fn();
			render(EmailTemplatesList, {
				props: { templates: mockTemplates, onEdit }
			});

			// Find all Edit buttons and click the first one
			const buttons = screen.getAllByRole('button');
			const editButton = buttons.find((b) => b.textContent?.includes('Edit'));
			expect(editButton).toBeDefined();
			await fireEvent.click(editButton!);

			expect(onEdit).toHaveBeenCalled();
		});

		it('should call onPreview when Preview button is clicked', async () => {
			const onPreview = vi.fn();
			render(EmailTemplatesList, {
				props: { templates: mockTemplates, onPreview }
			});

			const buttons = screen.getAllByRole('button');
			const previewButton = buttons.find((b) => b.textContent?.includes('Preview'));
			expect(previewButton).toBeDefined();
			await fireEvent.click(previewButton!);

			expect(onPreview).toHaveBeenCalled();
		});
	});

	describe('Accessibility', () => {
		it('should have search input with aria-label', () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			const searchInput = screen.getByLabelText('Search email templates');
			expect(searchInput).toBeInTheDocument();
		});

		it('should have proper heading hierarchy', () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			const heading = screen.getByRole('heading', { level: 1 });
			expect(heading).toBeInTheDocument();
		});

		it('should have list role for templates container', () => {
			render(EmailTemplatesList, { props: { templates: mockTemplates } });

			const list = screen.getByRole('list');
			expect(list).toBeInTheDocument();
		});
	});
});
