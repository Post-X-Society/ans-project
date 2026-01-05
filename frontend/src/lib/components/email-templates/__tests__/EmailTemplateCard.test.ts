/**
 * EmailTemplateCard Component Tests
 *
 * Issue #167: Email Template Admin Management UI
 * TDD: Tests written FIRST before implementation
 */

import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import EmailTemplateCard from '../EmailTemplateCard.svelte';
import type { EmailTemplate } from '$lib/api/types';

// Mock svelte-i18n
vi.mock('svelte-i18n', () => ({
	t: {
		subscribe: (fn: (value: (key: string, vars?: Record<string, unknown>) => string) => void) => {
			fn((key: string, vars?: Record<string, unknown>) => {
				// Simple translation mock
				const translations: Record<string, string> = {
					'emailTemplates.card.view': 'View',
					'emailTemplates.card.edit': 'Edit',
					'emailTemplates.card.preview': 'Preview',
					'emailTemplates.card.deactivate': 'Deactivate',
					'emailTemplates.card.activate': 'Activate',
					'emailTemplates.card.variables': 'Variables',
					'emailTemplates.card.noVariables': 'No variables defined',
					'emailTemplates.list.version': `Version ${vars?.values?.version || ''}`,
					'emailTemplates.list.lastModified': `Last modified by ${vars?.values?.email || ''}`,
					'emailTemplates.list.variables': `${vars?.values?.count || 0} variables`,
					'emailTemplates.types.submission_received': 'Submission Received',
					'emailTemplates.types.welcome_email': 'Welcome Email',
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

const mockTemplate: EmailTemplate = {
	id: 'test-uuid-123',
	template_key: 'welcome_email',
	template_type: 'welcome_email',
	name: { en: 'Welcome Email', nl: 'Welkomstmail' },
	description: { en: 'Sent to new users', nl: 'Verzonden naar nieuwe gebruikers' },
	subject: { en: 'Welcome to Ans!', nl: 'Welkom bij Ans!' },
	body_text: { en: 'Hello {{name}}!', nl: 'Hallo {{name}}!' },
	body_html: { en: '<h1>Welcome {{name}}!</h1>', nl: '<h1>Welkom {{name}}!</h1>' },
	variables: { name: 'string', email: 'string' },
	is_active: true,
	version: 3,
	last_modified_by: 'admin@example.com',
	notes: 'Updated for new branding',
	created_at: '2025-01-01T00:00:00Z',
	updated_at: '2025-01-05T12:30:00Z'
};

describe('EmailTemplateCard', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('Rendering', () => {
		it('should render the template name', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			// Name appears in the h3 heading
			const heading = screen.getByRole('heading', { level: 3 });
			expect(heading).toHaveTextContent('Welcome Email');
		});

		it('should render the template description', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			expect(screen.getByText('Sent to new users')).toBeInTheDocument();
		});

		it('should render the template type badge', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			// Type appears in multiple places - just check it's there
			const allTexts = screen.getAllByText('Welcome Email');
			expect(allTexts.length).toBeGreaterThanOrEqual(1);
		});

		it('should show active status badge when template is active', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			const activeBadge = screen.getByTestId('status-badge');
			expect(activeBadge).toHaveTextContent('Active');
		});

		it('should show inactive status badge when template is inactive', () => {
			const inactiveTemplate = { ...mockTemplate, is_active: false };
			render(EmailTemplateCard, { props: { template: inactiveTemplate } });

			const inactiveBadge = screen.getByTestId('status-badge');
			expect(inactiveBadge).toHaveTextContent('Inactive');
		});

		it('should display version number', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			expect(screen.getByText(/Version 3/)).toBeInTheDocument();
		});

		it('should display last modified by info', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			expect(screen.getByText(/admin@example.com/)).toBeInTheDocument();
		});

		it('should display variable count', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			expect(screen.getByText(/2 variables/)).toBeInTheDocument();
		});
	});

	describe('Actions', () => {
		it('should have View button', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			const buttons = screen.getAllByRole('button');
			const viewButton = buttons.find((b) => b.textContent?.includes('View'));
			expect(viewButton).toBeDefined();
		});

		it('should have Edit button', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			const buttons = screen.getAllByRole('button');
			const editButton = buttons.find((b) => b.textContent?.includes('Edit'));
			expect(editButton).toBeDefined();
		});

		it('should have Preview button', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			const buttons = screen.getAllByRole('button');
			const previewButton = buttons.find((b) => b.textContent?.includes('Preview'));
			expect(previewButton).toBeDefined();
		});

		it('should call onView when View button is clicked', async () => {
			const onView = vi.fn();
			render(EmailTemplateCard, {
				props: { template: mockTemplate, onView }
			});

			// Find button by text content
			const buttons = screen.getAllByRole('button');
			const viewButton = buttons.find((b) => b.textContent?.includes('View'));
			expect(viewButton).toBeDefined();
			await fireEvent.click(viewButton!);

			expect(onView).toHaveBeenCalledWith(mockTemplate);
		});

		it('should call onEdit when Edit button is clicked', async () => {
			const onEdit = vi.fn();
			render(EmailTemplateCard, {
				props: { template: mockTemplate, onEdit }
			});

			// Find button by text content
			const buttons = screen.getAllByRole('button');
			const editButton = buttons.find((b) => b.textContent?.includes('Edit'));
			expect(editButton).toBeDefined();
			await fireEvent.click(editButton!);

			expect(onEdit).toHaveBeenCalledWith(mockTemplate);
		});

		it('should call onPreview when Preview button is clicked', async () => {
			const onPreview = vi.fn();
			render(EmailTemplateCard, {
				props: { template: mockTemplate, onPreview }
			});

			// Find button by text content
			const buttons = screen.getAllByRole('button');
			const previewButton = buttons.find((b) => b.textContent?.includes('Preview'));
			expect(previewButton).toBeDefined();
			await fireEvent.click(previewButton!);

			expect(onPreview).toHaveBeenCalledWith(mockTemplate);
		});

		it('should show Deactivate button for active templates', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			const buttons = screen.getAllByRole('button');
			const deactivateButton = buttons.find((b) => b.textContent?.includes('Deactivate'));
			expect(deactivateButton).toBeDefined();
		});

		it('should show Activate button for inactive templates', () => {
			const inactiveTemplate = { ...mockTemplate, is_active: false };
			render(EmailTemplateCard, { props: { template: inactiveTemplate } });

			const buttons = screen.getAllByRole('button');
			const activateButton = buttons.find((b) => b.textContent?.includes('Activate'));
			expect(activateButton).toBeDefined();
		});

		it('should call onToggleActive when Deactivate button is clicked', async () => {
			const onToggleActive = vi.fn();
			render(EmailTemplateCard, {
				props: { template: mockTemplate, onToggleActive }
			});

			const buttons = screen.getAllByRole('button');
			const deactivateButton = buttons.find((b) => b.textContent?.includes('Deactivate'));
			expect(deactivateButton).toBeDefined();
			await fireEvent.click(deactivateButton!);

			expect(onToggleActive).toHaveBeenCalledWith(mockTemplate);
		});
	});

	describe('Accessibility', () => {
		it('should have accessible button labels', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			// Check that all 4 buttons exist (View, Edit, Preview, Deactivate)
			const buttons = screen.getAllByRole('button');
			expect(buttons.length).toBe(4);

			// Check button text content
			const buttonTexts = buttons.map((b) => b.textContent?.trim());
			expect(buttonTexts).toContain('View');
			expect(buttonTexts).toContain('Edit');
			expect(buttonTexts).toContain('Preview');
			expect(buttonTexts).toContain('Deactivate');
		});

		it('should use article role for the card', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			expect(screen.getByRole('article')).toBeInTheDocument();
		});
	});

	describe('Locale handling', () => {
		it('should display name in English by default', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate, locale: 'en' } });

			const heading = screen.getByRole('heading', { level: 3 });
			expect(heading).toHaveTextContent('Welcome Email');
		});

		it('should display name in Dutch when locale is nl', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate, locale: 'nl' } });

			const heading = screen.getByRole('heading', { level: 3 });
			expect(heading).toHaveTextContent('Welkomstmail');
		});

		it('should fallback to English when translation is missing', () => {
			const templateWithMissingNl = {
				...mockTemplate,
				name: { en: 'Welcome Email' } // No Dutch translation
			};
			render(EmailTemplateCard, { props: { template: templateWithMissingNl, locale: 'nl' } });

			const heading = screen.getByRole('heading', { level: 3 });
			expect(heading).toHaveTextContent('Welcome Email');
		});
	});

	describe('Variables display', () => {
		it('should show variable count when variables exist', () => {
			render(EmailTemplateCard, { props: { template: mockTemplate } });

			expect(screen.getByText(/2 variables/)).toBeInTheDocument();
		});

		it('should handle template with no variables', () => {
			const templateNoVars = { ...mockTemplate, variables: {} };
			render(EmailTemplateCard, { props: { template: templateNoVars } });

			expect(screen.getByText(/0 variables/)).toBeInTheDocument();
		});
	});
});
