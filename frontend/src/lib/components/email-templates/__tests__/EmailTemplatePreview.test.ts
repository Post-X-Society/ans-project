/**
 * EmailTemplatePreview Component Tests
 *
 * Issue #167: Email Template Admin Management UI
 * TDD: Tests written FIRST before implementation
 */

import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import EmailTemplatePreview from '../EmailTemplatePreview.svelte';
import type { EmailTemplate, EmailTemplateRenderResponse } from '$lib/api/types';

// Mock svelte-i18n
vi.mock('svelte-i18n', () => ({
	t: {
		subscribe: (fn: (value: (key: string) => string) => void) => {
			fn((key: string) => {
				const translations: Record<string, string> = {
					'emailTemplates.preview.title': 'Template Preview',
					'emailTemplates.preview.language': 'Preview Language',
					'emailTemplates.preview.testData': 'Test Data',
					'emailTemplates.preview.testDataDescription':
						'Enter test values for template variables',
					'emailTemplates.preview.render': 'Render Preview',
					'emailTemplates.preview.rendering': 'Rendering...',
					'emailTemplates.preview.subject': 'Subject',
					'emailTemplates.preview.textBody': 'Plain Text',
					'emailTemplates.preview.htmlBody': 'HTML Preview',
					'emailTemplates.preview.error': 'Failed to render preview',
					'language.english': 'English',
					'language.dutch': 'Nederlands',
					'common.close': 'Close'
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
	subject: { en: 'Welcome {{name}}!', nl: 'Welkom {{name}}!' },
	body_text: { en: 'Hello {{name}}!', nl: 'Hallo {{name}}!' },
	body_html: {
		en: '<h1>Welcome {{name}}!</h1>',
		nl: '<h1>Welkom {{name}}!</h1>'
	},
	variables: { name: 'string', email: 'string' },
	is_active: true,
	version: 3,
	last_modified_by: 'admin@example.com',
	notes: null,
	created_at: '2025-01-01T00:00:00Z',
	updated_at: '2025-01-05T12:30:00Z'
};

const mockRenderedPreview: EmailTemplateRenderResponse = {
	subject: 'Welcome John!',
	body_text: 'Hello John!',
	body_html: '<h1>Welcome John!</h1>'
};

describe('EmailTemplatePreview', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('Rendering', () => {
		it('should render the preview title', () => {
			render(EmailTemplatePreview, { props: { template: mockTemplate } });

			expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Template Preview');
		});

		it('should render language selection', () => {
			render(EmailTemplatePreview, { props: { template: mockTemplate } });

			expect(screen.getByText('English')).toBeInTheDocument();
			expect(screen.getByText('Nederlands')).toBeInTheDocument();
		});

		it('should render input fields for each template variable', () => {
			render(EmailTemplatePreview, { props: { template: mockTemplate } });

			expect(screen.getByLabelText('name')).toBeInTheDocument();
			expect(screen.getByLabelText('email')).toBeInTheDocument();
		});

		it('should render the Render Preview button', () => {
			render(EmailTemplatePreview, { props: { template: mockTemplate } });

			const buttons = screen.getAllByRole('button');
			const renderButton = buttons.find((b) => b.textContent?.includes('Render Preview'));
			expect(renderButton).toBeDefined();
		});
	});

	describe('Preview rendering', () => {
		it('should call onRender when Render Preview button is clicked', async () => {
			const onRender = vi.fn().mockResolvedValue(mockRenderedPreview);
			render(EmailTemplatePreview, { props: { template: mockTemplate, onRender } });

			// Fill in variable values
			const nameInput = screen.getByLabelText('name');
			await fireEvent.input(nameInput, { target: { value: 'John' } });

			// Click render button
			const buttons = screen.getAllByRole('button');
			const renderButton = buttons.find((b) => b.textContent?.includes('Render Preview'));
			await fireEvent.click(renderButton!);

			expect(onRender).toHaveBeenCalled();
		});

		it('should display rendered preview when available', () => {
			render(EmailTemplatePreview, {
				props: { template: mockTemplate, renderedPreview: mockRenderedPreview }
			});

			// Subject appears in the preview (may appear in multiple places)
			const allMatches = screen.getAllByText('Welcome John!');
			expect(allMatches.length).toBeGreaterThanOrEqual(1);
		});
	});

	describe('Close action', () => {
		it('should call onClose when close button is clicked', async () => {
			const onClose = vi.fn();
			render(EmailTemplatePreview, { props: { template: mockTemplate, onClose } });

			const buttons = screen.getAllByRole('button');
			const closeButton = buttons.find((b) => b.textContent?.includes('Close'));
			expect(closeButton).toBeDefined();
			await fireEvent.click(closeButton!);

			expect(onClose).toHaveBeenCalled();
		});
	});
});
