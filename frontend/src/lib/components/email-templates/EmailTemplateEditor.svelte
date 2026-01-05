<!--
  EmailTemplateEditor Component

  Issue #167: Email Template Admin Management UI
  Provides a form for editing email templates with multilingual support (EN/NL)
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { EmailTemplate, EmailTemplateUpdate } from '$lib/api/types';

	type SupportedLocale = 'en' | 'nl';

	interface Props {
		template: EmailTemplate;
		isSaving?: boolean;
		onSave?: (data: EmailTemplateUpdate) => void;
		onCancel?: () => void;
	}

	let { template, isSaving = false, onSave, onCancel }: Props = $props();

	// Current editing language
	let activeLocale = $state<SupportedLocale>('en');

	// Form state - initialized from template
	let formData = $state({
		name: {} as Record<string, string>,
		description: {} as Record<string, string>,
		subject: {} as Record<string, string>,
		body_text: {} as Record<string, string>,
		body_html: {} as Record<string, string>,
		variables: {} as Record<string, string>,
		is_active: true,
		notes: ''
	});

	// Track template ID to reset form when template changes
	let lastTemplateId = $state('');

	// Initialize form data when template changes
	$effect(() => {
		if (template.id !== lastTemplateId) {
			lastTemplateId = template.id;
			formData = {
				name: { ...template.name },
				description: { ...template.description },
				subject: { ...template.subject },
				body_text: { ...template.body_text },
				body_html: { ...template.body_html },
				variables: { ...template.variables },
				is_active: template.is_active,
				notes: template.notes || ''
			};
		}
	});

	// Get value for current locale with fallback
	function getLocalizedValue(map: Record<string, string>): string {
		return map[activeLocale] || map['en'] || '';
	}

	// Set value for current locale
	function setLocalizedValue(map: Record<string, string>, value: string): Record<string, string> {
		return { ...map, [activeLocale]: value };
	}

	function handleLocaleChange(locale: SupportedLocale) {
		activeLocale = locale;
	}

	function handleSave() {
		const updateData: EmailTemplateUpdate = {
			name: formData.name,
			description: formData.description,
			subject: formData.subject,
			body_text: formData.body_text,
			body_html: formData.body_html,
			variables: formData.variables,
			is_active: formData.is_active,
			notes: formData.notes || undefined
		};
		onSave?.(updateData);
	}

	function handleCancel() {
		onCancel?.();
	}
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="border-b border-gray-200 pb-4 dark:border-gray-700">
		<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
			{$t('emailTemplates.editor.title')}
		</h2>
		<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
			{template.template_key}
		</p>
	</div>

	<!-- Language Tabs -->
	<div class="border-b border-gray-200 dark:border-gray-700">
		<nav class="-mb-px flex gap-4" aria-label="Language tabs">
			<button
				type="button"
				class="whitespace-nowrap border-b-2 px-1 py-3 text-sm font-medium {activeLocale === 'en'
					? 'border-blue-500 text-blue-600 dark:text-blue-400'
					: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
				onclick={() => handleLocaleChange('en')}
			>
				{$t('language.english')}
			</button>
			<button
				type="button"
				class="whitespace-nowrap border-b-2 px-1 py-3 text-sm font-medium {activeLocale === 'nl'
					? 'border-blue-500 text-blue-600 dark:text-blue-400'
					: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
				onclick={() => handleLocaleChange('nl')}
			>
				{$t('language.dutch')}
			</button>
		</nav>
	</div>

	<!-- Form Fields -->
	<form onsubmit={(e) => { e.preventDefault(); handleSave(); }} class="space-y-6">
		<!-- Name -->
		<div>
			<label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{$t('emailTemplates.editor.name')}
			</label>
			<input
				type="text"
				id="name"
				value={getLocalizedValue(formData.name)}
				oninput={(e) => (formData.name = setLocalizedValue(formData.name, e.currentTarget.value))}
				placeholder={$t('emailTemplates.editor.namePlaceholder')}
				class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white sm:text-sm"
			/>
		</div>

		<!-- Description -->
		<div>
			<label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{$t('emailTemplates.editor.description')}
			</label>
			<textarea
				id="description"
				rows="2"
				value={getLocalizedValue(formData.description)}
				oninput={(e) =>
					(formData.description = setLocalizedValue(formData.description, e.currentTarget.value))}
				placeholder={$t('emailTemplates.editor.descriptionPlaceholder')}
				class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white sm:text-sm"
			></textarea>
		</div>

		<!-- Subject Line -->
		<div>
			<label for="subject" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{$t('emailTemplates.editor.subject')}
			</label>
			<input
				type="text"
				id="subject"
				value={getLocalizedValue(formData.subject)}
				oninput={(e) =>
					(formData.subject = setLocalizedValue(formData.subject, e.currentTarget.value))}
				placeholder={$t('emailTemplates.editor.subjectPlaceholder')}
				class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white sm:text-sm"
			/>
		</div>

		<!-- Plain Text Body -->
		<div>
			<label for="body_text" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{$t('emailTemplates.editor.bodyText')}
			</label>
			<textarea
				id="body_text"
				rows="6"
				value={getLocalizedValue(formData.body_text)}
				oninput={(e) =>
					(formData.body_text = setLocalizedValue(formData.body_text, e.currentTarget.value))}
				placeholder={$t('emailTemplates.editor.bodyTextPlaceholder')}
				class="mt-1 block w-full rounded-md border-gray-300 font-mono text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
			></textarea>
		</div>

		<!-- HTML Body -->
		<div>
			<label for="body_html" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{$t('emailTemplates.editor.bodyHtml')}
			</label>
			<textarea
				id="body_html"
				rows="10"
				value={getLocalizedValue(formData.body_html)}
				oninput={(e) =>
					(formData.body_html = setLocalizedValue(formData.body_html, e.currentTarget.value))}
				placeholder={$t('emailTemplates.editor.bodyHtmlPlaceholder')}
				class="mt-1 block w-full rounded-md border-gray-300 font-mono text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
			></textarea>
		</div>

		<!-- Template Variables (read-only display) -->
		<div>
			<span class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{$t('emailTemplates.editor.variables')}
			</span>
			<div
				class="mt-1 rounded-md border border-gray-300 bg-gray-50 p-3 dark:border-gray-600 dark:bg-gray-800"
			>
				{#if Object.keys(formData.variables).length > 0}
					<div class="flex flex-wrap gap-2">
						{#each Object.entries(formData.variables) as [key, type]}
							<span
								class="inline-flex items-center rounded-md bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800 dark:bg-blue-900/50 dark:text-blue-200"
							>
								{'{{' + key + '}}'}: {type}
							</span>
						{/each}
					</div>
				{:else}
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{$t('emailTemplates.card.noVariables')}
					</p>
				{/if}
			</div>
		</div>

		<!-- Notes -->
		<div>
			<label for="notes" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{$t('emailTemplates.editor.notes')}
			</label>
			<textarea
				id="notes"
				rows="3"
				bind:value={formData.notes}
				placeholder={$t('emailTemplates.editor.notesPlaceholder')}
				class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white sm:text-sm"
			></textarea>
		</div>

		<!-- Active Toggle -->
		<div class="flex items-center">
			<input
				type="checkbox"
				id="is_active"
				bind:checked={formData.is_active}
				class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
			/>
			<label for="is_active" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
				{$t('emailTemplates.editor.isActive')}
			</label>
		</div>

		<!-- Actions -->
		<div
			class="flex justify-end gap-3 border-t border-gray-200 pt-4 dark:border-gray-700"
		>
			<button
				type="button"
				onclick={handleCancel}
				class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
			>
				{$t('emailTemplates.editor.cancel')}
			</button>
			<button
				type="submit"
				disabled={isSaving}
				class="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
			>
				{#if isSaving}
					<svg class="mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
						<circle
							class="opacity-25"
							cx="12"
							cy="12"
							r="10"
							stroke="currentColor"
							stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					{$t('emailTemplates.editor.saving')}
				{:else}
					{$t('emailTemplates.editor.save')}
				{/if}
			</button>
		</div>
	</form>
</div>
