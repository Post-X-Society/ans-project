<!--
  EmailTemplateCard Component

  Issue #167: Email Template Admin Management UI
  Displays a single email template in a card format with actions
-->
<script lang="ts">
	import { t, locale } from 'svelte-i18n';
	import type { EmailTemplate } from '$lib/api/types';

	interface Props {
		template: EmailTemplate;
		locale?: string;
		onView?: (template: EmailTemplate) => void;
		onEdit?: (template: EmailTemplate) => void;
		onPreview?: (template: EmailTemplate) => void;
		onToggleActive?: (template: EmailTemplate) => void;
	}

	let {
		template,
		locale: propLocale,
		onView,
		onEdit,
		onPreview,
		onToggleActive
	}: Props = $props();

	// Get the current locale for displaying multilingual content
	let currentLocale = $derived(propLocale || ($locale as string) || 'en');

	// Get localized text with fallback to English
	function getLocalizedText(
		textMap: Record<string, string> | undefined,
		defaultText: string = ''
	): string {
		if (!textMap) return defaultText;
		return textMap[currentLocale] || textMap['en'] || defaultText;
	}

	// Count variables
	let variableCount = $derived(Object.keys(template.variables || {}).length);

	// Format date for display
	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString(currentLocale, {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	// Get template type translation key
	function getTemplateTypeLabel(type: string): string {
		const key = `emailTemplates.types.${type}`;
		return $t(key);
	}

	function handleView() {
		onView?.(template);
	}

	function handleEdit() {
		onEdit?.(template);
	}

	function handlePreview() {
		onPreview?.(template);
	}

	function handleToggleActive() {
		onToggleActive?.(template);
	}
</script>

<article
	class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
>
	<!-- Header: Name and Status -->
	<div class="mb-3 flex items-start justify-between">
		<div class="flex-1">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
				{getLocalizedText(template.name, template.template_key)}
			</h3>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				{getLocalizedText(template.description, '')}
			</p>
		</div>
		<span
			data-testid="status-badge"
			class="ml-2 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {template.is_active
				? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
				: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}"
		>
			{template.is_active ? $t('status.active') : $t('status.inactive')}
		</span>
	</div>

	<!-- Template Type Badge -->
	<div class="mb-3">
		<span
			class="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10 dark:bg-blue-900/30 dark:text-blue-300 dark:ring-blue-400/30"
		>
			{getTemplateTypeLabel(template.template_type)}
		</span>
	</div>

	<!-- Metadata -->
	<div class="mb-4 space-y-1 text-xs text-gray-500 dark:text-gray-400">
		<div class="flex items-center gap-2">
			<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
				/>
			</svg>
			<span>{$t('emailTemplates.list.version', { values: { version: template.version } })}</span>
		</div>

		{#if template.last_modified_by}
			<div class="flex items-center gap-2">
				<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
					/>
				</svg>
				<span
					>{$t('emailTemplates.list.lastModified', {
						values: { email: template.last_modified_by }
					})}</span
				>
			</div>
		{/if}

		<div class="flex items-center gap-2">
			<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"
				/>
			</svg>
			<span>{$t('emailTemplates.list.variables', { values: { count: variableCount } })}</span>
		</div>
	</div>

	<!-- Actions -->
	<div class="flex flex-wrap gap-2 border-t border-gray-100 pt-3 dark:border-gray-700">
		<button
			type="button"
			onclick={handleView}
			class="inline-flex items-center rounded-md bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
		>
			<svg class="mr-1.5 h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
				/>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
				/>
			</svg>
			{$t('emailTemplates.card.view')}
		</button>

		<button
			type="button"
			onclick={handleEdit}
			class="inline-flex items-center rounded-md bg-blue-100 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-900"
		>
			<svg class="mr-1.5 h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
				/>
			</svg>
			{$t('emailTemplates.card.edit')}
		</button>

		<button
			type="button"
			onclick={handlePreview}
			class="inline-flex items-center rounded-md bg-purple-100 px-3 py-1.5 text-xs font-medium text-purple-700 hover:bg-purple-200 dark:bg-purple-900/50 dark:text-purple-300 dark:hover:bg-purple-900"
		>
			<svg class="mr-1.5 h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
				/>
			</svg>
			{$t('emailTemplates.card.preview')}
		</button>

		<button
			type="button"
			onclick={handleToggleActive}
			class="inline-flex items-center rounded-md px-3 py-1.5 text-xs font-medium {template.is_active
				? 'bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/50 dark:text-red-300 dark:hover:bg-red-900'
				: 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/50 dark:text-green-300 dark:hover:bg-green-900'}"
		>
			<svg class="mr-1.5 h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				{#if template.is_active}
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
					/>
				{:else}
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
					/>
				{/if}
			</svg>
			{template.is_active
				? $t('emailTemplates.card.deactivate')
				: $t('emailTemplates.card.activate')}
		</button>
	</div>
</article>
