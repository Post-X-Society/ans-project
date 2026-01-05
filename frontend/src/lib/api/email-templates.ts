/**
 * Email Template API client functions
 *
 * Issue #167: Email Template Admin Management UI
 * Provides API functions for managing email templates (admin only)
 */

import { apiClient } from './client';
import type {
	EmailTemplate,
	EmailTemplateCreate,
	EmailTemplateUpdate,
	EmailTemplateRenderRequest,
	EmailTemplateRenderResponse,
	EmailTemplateType
} from './types';

/**
 * List all email templates (admin only)
 *
 * @param includeInactive - Include inactive templates in the response
 * @param templateType - Filter by template type
 * @returns List of email templates
 */
export async function getEmailTemplates(
	includeInactive: boolean = false,
	templateType?: EmailTemplateType
): Promise<EmailTemplate[]> {
	const params: Record<string, unknown> = {};
	if (includeInactive) params.include_inactive = true;
	if (templateType) params.template_type = templateType;

	const response = await apiClient.get<EmailTemplate[]>('/api/v1/email-templates/', { params });
	return response.data;
}

/**
 * Get a single email template by key (admin only)
 *
 * @param templateKey - The unique template key
 * @returns The email template
 */
export async function getEmailTemplate(templateKey: string): Promise<EmailTemplate> {
	const response = await apiClient.get<EmailTemplate>(`/api/v1/email-templates/${templateKey}`);
	return response.data;
}

/**
 * Create a new email template (admin only)
 *
 * @param data - Template creation data
 * @returns The created email template
 */
export async function createEmailTemplate(data: EmailTemplateCreate): Promise<EmailTemplate> {
	const response = await apiClient.post<EmailTemplate>('/api/v1/email-templates/', data);
	return response.data;
}

/**
 * Update an existing email template (admin only)
 *
 * @param templateKey - The template key to update
 * @param data - Template update data
 * @returns The updated email template
 */
export async function updateEmailTemplate(
	templateKey: string,
	data: EmailTemplateUpdate
): Promise<EmailTemplate> {
	const response = await apiClient.patch<EmailTemplate>(
		`/api/v1/email-templates/${templateKey}`,
		data
	);
	return response.data;
}

/**
 * Deactivate an email template (admin only)
 * Note: Templates are not deleted, only deactivated for audit trail
 *
 * @param templateKey - The template key to deactivate
 */
export async function deactivateEmailTemplate(templateKey: string): Promise<void> {
	await apiClient.delete(`/api/v1/email-templates/${templateKey}`);
}

/**
 * Preview a rendered email template with test data (admin only)
 *
 * @param request - Render request with template key, context, and language
 * @returns The rendered template
 */
export async function renderEmailTemplate(
	request: EmailTemplateRenderRequest
): Promise<EmailTemplateRenderResponse> {
	const response = await apiClient.post<EmailTemplateRenderResponse>(
		'/api/v1/email-templates/render',
		request
	);
	return response.data;
}
