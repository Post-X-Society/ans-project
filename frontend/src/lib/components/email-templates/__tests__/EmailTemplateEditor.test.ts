/**
 * EmailTemplateEditor Component Tests
 *
 * Issue #167: Email Template Admin Management UI
 * TDD: Tests written FIRST before implementation
 */

import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import EmailTemplateEditor from '../EmailTemplateEditor.svelte';
import type { EmailTemplate } from '$lib/api/types';

// Mock svelte-i18n
vi.mock('svelte-i18n', () => ({
	t: {
		subscribe: (fn: (value: (key: string) => string) => void) => {
			fn((key: string) => {
				const translations: Record<string, string> = {
					'emailTemplates.editor.title': 'Edit Template',
					'emailTemplates.editor.createTitle': 'Create Template',
					'emailTemplates.editor.language': 'Language',
					'emailTemplates.editor.name': 'Name',
					'emailTemplates.editor.namePlaceholder': 'Template name',
					'emailTemplates.editor.description': 'Description',
					'emailTemplates.editor.descriptionPlaceholder': 'Template description',
					'emailTemplates.editor.subject': 'Subject Line',
					'emailTemplates.editor.subjectPlaceholder': 'Email subject',
					'emailTemplates.editor.bodyText': 'Plain Text Body',
					'emailTemplates.editor.bodyTextPlaceholder': 'Plain text version of email...',
					'emailTemplates.editor.bodyHtml': 'HTML Body',
					'emailTemplates.editor.bodyHtmlPlaceholder': '<html>...</html>',
					'emailTemplates.editor.variables': 'Template Variables',
					'emailTemplates.editor.notes': 'Internal Notes',
					'emailTemplates.editor.notesPlaceholder': 'Notes for admins...',
					'emailTemplates.editor.isActive': 'Template Active',
					'emailTemplates.editor.save': 'Save Template',
					'emailTemplates.editor.saving': 'Saving...',
					'emailTemplates.editor.cancel': 'Cancel',
					'emailTemplates.editor.success': 'Template saved successfully',
					'emailTemplates.editor.error': 'Failed to save template',
					'language.english': 'English',
					'language.dutch': 'Nederlands'
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
	subject: { en: 'Welcome!', nl: 'Welkom!' },
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

describe('EmailTemplateEditor', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('Rendering', () => {
		it('should render the editor title for editing', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Edit Template');
		});

		it('should render language selector tabs', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			expect(screen.getByText('English')).toBeInTheDocument();
			expect(screen.getByText('Nederlands')).toBeInTheDocument();
		});

		it('should render name input field', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			expect(screen.getByLabelText('Name')).toBeInTheDocument();
		});

		it('should render subject input field', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			expect(screen.getByLabelText('Subject Line')).toBeInTheDocument();
		});

		it('should render body text textarea', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			expect(screen.getByLabelText('Plain Text Body')).toBeInTheDocument();
		});

		it('should render body HTML textarea', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			expect(screen.getByLabelText('HTML Body')).toBeInTheDocument();
		});

		it('should render save and cancel buttons', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			const buttons = screen.getAllByRole('button');
			const buttonTexts = buttons.map((b) => b.textContent);
			expect(buttonTexts).toContain('Save Template');
			expect(buttonTexts).toContain('Cancel');
		});
	});

	describe('Form pre-population', () => {
		it('should populate name field with template data', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			const nameInput = screen.getByLabelText('Name') as HTMLInputElement;
			expect(nameInput.value).toBe('Welcome Email');
		});

		it('should populate subject field with template data', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			const subjectInput = screen.getByLabelText('Subject Line') as HTMLInputElement;
			expect(subjectInput.value).toBe('Welcome!');
		});
	});

	describe('Language switching', () => {
		it('should switch to Dutch content when NL tab is clicked', async () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			const nlTab = screen.getByText('Nederlands');
			await fireEvent.click(nlTab);

			const nameInput = screen.getByLabelText('Name') as HTMLInputElement;
			expect(nameInput.value).toBe('Welkomstmail');
		});
	});

	describe('Form submission', () => {
		it('should call onSave when save button is clicked', async () => {
			const onSave = vi.fn();
			render(EmailTemplateEditor, { props: { template: mockTemplate, onSave } });

			const buttons = screen.getAllByRole('button');
			const saveButton = buttons.find((b) => b.textContent?.includes('Save'));
			expect(saveButton).toBeDefined();
			await fireEvent.click(saveButton!);

			expect(onSave).toHaveBeenCalled();
		});

		it('should call onCancel when cancel button is clicked', async () => {
			const onCancel = vi.fn();
			render(EmailTemplateEditor, { props: { template: mockTemplate, onCancel } });

			const buttons = screen.getAllByRole('button');
			const cancelButton = buttons.find((b) => b.textContent?.includes('Cancel'));
			expect(cancelButton).toBeDefined();
			await fireEvent.click(cancelButton!);

			expect(onCancel).toHaveBeenCalled();
		});
	});

	describe('Accessibility', () => {
		it('should have proper form labels', () => {
			render(EmailTemplateEditor, { props: { template: mockTemplate } });

			expect(screen.getByLabelText('Name')).toBeInTheDocument();
			expect(screen.getByLabelText('Subject Line')).toBeInTheDocument();
			expect(screen.getByLabelText('Plain Text Body')).toBeInTheDocument();
			expect(screen.getByLabelText('HTML Body')).toBeInTheDocument();
		});
	});
});
