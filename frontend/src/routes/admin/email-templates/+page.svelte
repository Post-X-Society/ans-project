<!--
  Email Templates Admin Page

  Issue #167: Email Template Admin Management UI
  Provides admin interface for managing email templates
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { createQuery, createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { t } from 'svelte-i18n';
	import {
		emailTemplatesQueryOptions,
		updateEmailTemplateMutationOptions,
		renderEmailTemplateMutationOptions
	} from '$lib/api/queries';
	import { updateEmailTemplate, renderEmailTemplate } from '$lib/api/email-templates';
	import EmailTemplatesList from '$lib/components/email-templates/EmailTemplatesList.svelte';
	import EmailTemplateEditor from '$lib/components/email-templates/EmailTemplateEditor.svelte';
	import EmailTemplatePreview from '$lib/components/email-templates/EmailTemplatePreview.svelte';
	import type {
		EmailTemplate,
		EmailTemplateUpdate,
		EmailTemplateRenderRequest,
		EmailTemplateRenderResponse
	} from '$lib/api/types';

	const queryClient = useQueryClient();

	// Query for fetching templates (include inactive for admin view)
	const templatesQuery = createQuery(() => emailTemplatesQueryOptions(true));

	// Derive state from query
	let templates = $derived($templatesQuery.data || []);
	let isLoading = $derived($templatesQuery.isLoading);
	let error = $derived($templatesQuery.error?.message || null);

	// Modal states
	let showEditorModal = $state(false);
	let showPreviewModal = $state(false);
	let selectedTemplate = $state<EmailTemplate | null>(null);

	// Editor states
	let isSaving = $state(false);
	let saveError = $state<string | null>(null);
	let saveSuccess = $state<string | null>(null);

	// Preview states
	let isRendering = $state(false);
	let renderError = $state<string | null>(null);
	let renderedPreview = $state<EmailTemplateRenderResponse | null>(null);

	function handleView(template: EmailTemplate) {
		selectedTemplate = template;
		showEditorModal = true;
	}

	function handleEdit(template: EmailTemplate) {
		selectedTemplate = template;
		showEditorModal = true;
	}

	function handlePreview(template: EmailTemplate) {
		selectedTemplate = template;
		renderedPreview = null;
		renderError = null;
		showPreviewModal = true;
	}

	async function handleToggleActive(template: EmailTemplate) {
		try {
			await updateEmailTemplate(template.template_key, {
				is_active: !template.is_active
			});
			queryClient.invalidateQueries({ queryKey: ['email-templates'] });
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'Unknown error';
			console.error('Error toggling template status:', message);
		}
	}

	async function handleSave(data: EmailTemplateUpdate) {
		if (!selectedTemplate) return;

		isSaving = true;
		saveError = null;
		saveSuccess = null;

		try {
			await updateEmailTemplate(selectedTemplate.template_key, data);
			saveSuccess = $t('emailTemplates.editor.success');
			queryClient.invalidateQueries({ queryKey: ['email-templates'] });

			// Close modal after short delay
			setTimeout(() => {
				showEditorModal = false;
				selectedTemplate = null;
				saveSuccess = null;
			}, 1500);
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'Unknown error';
			saveError = message;
		} finally {
			isSaving = false;
		}
	}

	function handleCancelEdit() {
		showEditorModal = false;
		selectedTemplate = null;
		saveError = null;
		saveSuccess = null;
	}

	async function handleRenderPreview(request: EmailTemplateRenderRequest) {
		isRendering = true;
		renderError = null;

		try {
			renderedPreview = await renderEmailTemplate(request);
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'Unknown error';
			renderError = message;
		} finally {
			isRendering = false;
		}
	}

	function handleClosePreview() {
		showPreviewModal = false;
		selectedTemplate = null;
		renderedPreview = null;
		renderError = null;
	}

	function handleRetry() {
		$templatesQuery.refetch();
	}
</script>

<svelte:head>
	<title>{$t('emailTemplates.title')} - {$t('common.appName')}</title>
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
	<EmailTemplatesList
		{templates}
		{isLoading}
		{error}
		onView={handleView}
		onEdit={handleEdit}
		onPreview={handlePreview}
		onToggleActive={handleToggleActive}
		onRetry={handleRetry}
	/>
</div>

<!-- Editor Modal -->
{#if showEditorModal && selectedTemplate}
	<div
		class="fixed inset-0 z-50 overflow-y-auto"
		aria-labelledby="modal-title"
		role="dialog"
		aria-modal="true"
	>
		<div class="flex min-h-screen items-end justify-center px-4 pb-20 pt-4 text-center sm:block sm:p-0">
			<!-- Background overlay -->
			<div
				class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity dark:bg-gray-900 dark:bg-opacity-75"
				aria-hidden="true"
				onclick={handleCancelEdit}
			></div>

			<!-- Modal panel -->
			<div
				class="inline-block transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left align-bottom shadow-xl transition-all dark:bg-gray-800 sm:my-8 sm:w-full sm:max-w-4xl sm:p-6 sm:align-middle"
			>
				{#if saveSuccess}
					<div class="mb-4 rounded-md bg-green-50 p-4 dark:bg-green-900/20">
						<p class="text-sm text-green-700 dark:text-green-300">{saveSuccess}</p>
					</div>
				{/if}

				{#if saveError}
					<div class="mb-4 rounded-md bg-red-50 p-4 dark:bg-red-900/20">
						<p class="text-sm text-red-700 dark:text-red-300">{saveError}</p>
					</div>
				{/if}

				<EmailTemplateEditor
					template={selectedTemplate}
					{isSaving}
					onSave={handleSave}
					onCancel={handleCancelEdit}
				/>
			</div>
		</div>
	</div>
{/if}

<!-- Preview Modal -->
{#if showPreviewModal && selectedTemplate}
	<div
		class="fixed inset-0 z-50 overflow-y-auto"
		aria-labelledby="preview-modal-title"
		role="dialog"
		aria-modal="true"
	>
		<div class="flex min-h-screen items-end justify-center px-4 pb-20 pt-4 text-center sm:block sm:p-0">
			<!-- Background overlay -->
			<div
				class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity dark:bg-gray-900 dark:bg-opacity-75"
				aria-hidden="true"
				onclick={handleClosePreview}
			></div>

			<!-- Modal panel -->
			<div
				class="inline-block transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left align-bottom shadow-xl transition-all dark:bg-gray-800 sm:my-8 sm:w-full sm:max-w-3xl sm:p-6 sm:align-middle"
			>
				<EmailTemplatePreview
					template={selectedTemplate}
					{renderedPreview}
					{isRendering}
					error={renderError}
					onRender={handleRenderPreview}
					onClose={handleClosePreview}
				/>
			</div>
		</div>
	</div>
{/if}
