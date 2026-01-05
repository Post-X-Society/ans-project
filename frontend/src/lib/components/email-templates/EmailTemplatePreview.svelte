<!--
  EmailTemplatePreview Component

  Issue #167: Email Template Admin Management UI
  Renders a preview of an email template with test data
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import type {
		EmailTemplate,
		EmailTemplateRenderRequest,
		EmailTemplateRenderResponse
	} from '$lib/api/types';

	type SupportedLocale = 'en' | 'nl';

	interface Props {
		template: EmailTemplate;
		renderedPreview?: EmailTemplateRenderResponse | null;
		isRendering?: boolean;
		error?: string | null;
		onRender?: (request: EmailTemplateRenderRequest) => void;
		onClose?: () => void;
	}

	let {
		template,
		renderedPreview = null,
		isRendering = false,
		error = null,
		onRender,
		onClose
	}: Props = $props();

	// Preview language
	let previewLocale = $state<SupportedLocale>('en');

	// Get variable keys from template (reactive)
	let variableKeys = $derived(Object.keys(template.variables));

	// Test data for variables - initialized empty for each variable
	let testData = $state<Record<string, string>>({});

	// Initialize test data when variable keys change
	$effect(() => {
		testData = Object.fromEntries(variableKeys.map((key) => [key, '']));
	});

	function handleLocaleChange(locale: SupportedLocale) {
		previewLocale = locale;
	}

	function handleRender() {
		const request: EmailTemplateRenderRequest = {
			template_key: template.template_key,
			context: testData,
			language: previewLocale
		};
		onRender?.(request);
	}

	function handleClose() {
		onClose?.();
	}
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between border-b border-gray-200 pb-4 dark:border-gray-700">
		<div>
			<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
				{$t('emailTemplates.preview.title')}
			</h2>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				{template.name?.en || template.template_key}
			</p>
		</div>
		{#if onClose}
			<button
				type="button"
				onclick={handleClose}
				class="rounded-md text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
			>
				<span class="sr-only">{$t('common.close')}</span>
				<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				</svg>
			</button>
		{/if}
	</div>

	<!-- Language Selection -->
	<div>
		<span class="block text-sm font-medium text-gray-700 dark:text-gray-300">
			{$t('emailTemplates.preview.language')}
		</span>
		<div class="mt-2 flex gap-4">
			<button
				type="button"
				class="rounded-md px-3 py-2 text-sm font-medium {previewLocale === 'en'
					? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
					: 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'}"
				onclick={() => handleLocaleChange('en')}
			>
				{$t('language.english')}
			</button>
			<button
				type="button"
				class="rounded-md px-3 py-2 text-sm font-medium {previewLocale === 'nl'
					? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
					: 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'}"
				onclick={() => handleLocaleChange('nl')}
			>
				{$t('language.dutch')}
			</button>
		</div>
	</div>

	<!-- Test Data Input -->
	{#if variableKeys.length > 0}
		<div>
			<span class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{$t('emailTemplates.preview.testData')}
			</span>
			<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
				{$t('emailTemplates.preview.testDataDescription')}
			</p>
			<div class="mt-3 grid gap-3 sm:grid-cols-2">
				{#each variableKeys as varName}
					<div>
						<label
							for="var-{varName}"
							class="block text-sm font-medium text-gray-600 dark:text-gray-400"
						>
							{varName}
						</label>
						<input
							type="text"
							id="var-{varName}"
							aria-label={varName}
							bind:value={testData[varName]}
							placeholder={template.variables[varName] || 'string'}
							class="mt-1 block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
						/>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Render Button -->
	<div>
		<button
			type="button"
			onclick={handleRender}
			disabled={isRendering}
			class="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
		>
			{#if isRendering}
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
				{$t('emailTemplates.preview.rendering')}
			{:else}
				{$t('emailTemplates.preview.render')}
			{/if}
		</button>
	</div>

	<!-- Error -->
	{#if error}
		<div
			class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
		>
			<p class="text-sm text-red-700 dark:text-red-300">{error}</p>
		</div>
	{/if}

	<!-- Preview Output -->
	{#if renderedPreview}
		<div class="space-y-4 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
			<!-- Subject -->
			<div>
				<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">
					{$t('emailTemplates.preview.subject')}
				</h3>
				<p class="mt-1 text-gray-900 dark:text-white">{renderedPreview.subject}</p>
			</div>

			<!-- Plain Text -->
			<div>
				<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">
					{$t('emailTemplates.preview.textBody')}
				</h3>
				<pre
					class="mt-1 overflow-x-auto whitespace-pre-wrap rounded bg-white p-3 text-sm text-gray-900 dark:bg-gray-900 dark:text-white">{renderedPreview.body_text}</pre>
			</div>

			<!-- HTML Preview -->
			<div>
				<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">
					{$t('emailTemplates.preview.htmlBody')}
				</h3>
				<div
					class="mt-1 rounded border border-gray-200 bg-white p-4 dark:border-gray-600 dark:bg-gray-900"
				>
					<!-- eslint-disable-next-line svelte/no-at-html-tags -->
					{@html renderedPreview.body_html}
				</div>
			</div>
		</div>
	{/if}

	<!-- Close Button -->
	{#if onClose}
		<div class="flex justify-end border-t border-gray-200 pt-4 dark:border-gray-700">
			<button
				type="button"
				onclick={handleClose}
				class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
			>
				{$t('common.close')}
			</button>
		</div>
	{/if}
</div>
