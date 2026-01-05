<!--
  EmailTemplatesList Component

  Issue #167: Email Template Admin Management UI
  Displays a filterable list of email templates with search and filter controls
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { EmailTemplate } from '$lib/api/types';
	import EmailTemplateCard from './EmailTemplateCard.svelte';

	type StatusFilter = 'all' | 'active' | 'inactive';

	interface Props {
		templates: EmailTemplate[];
		isLoading?: boolean;
		error?: string | null;
		onView?: (template: EmailTemplate) => void;
		onEdit?: (template: EmailTemplate) => void;
		onPreview?: (template: EmailTemplate) => void;
		onToggleActive?: (template: EmailTemplate) => void;
		onRetry?: () => void;
	}

	let {
		templates,
		isLoading = false,
		error = null,
		onView,
		onEdit,
		onPreview,
		onToggleActive,
		onRetry
	}: Props = $props();

	// Filter state
	let searchTerm = $state('');
	let statusFilter = $state<StatusFilter>('active');

	// Filtered templates
	let filteredTemplates = $derived.by(() => {
		let result = templates;

		// Filter by status
		if (statusFilter === 'active') {
			result = result.filter((t) => t.is_active);
		} else if (statusFilter === 'inactive') {
			result = result.filter((t) => !t.is_active);
		}

		// Filter by search term
		if (searchTerm.trim()) {
			const term = searchTerm.toLowerCase();
			result = result.filter((t) => {
				const nameEn = t.name?.en?.toLowerCase() || '';
				const nameNl = t.name?.nl?.toLowerCase() || '';
				const key = t.template_key.toLowerCase();
				const descEn = t.description?.en?.toLowerCase() || '';
				const descNl = t.description?.nl?.toLowerCase() || '';

				return (
					nameEn.includes(term) ||
					nameNl.includes(term) ||
					key.includes(term) ||
					descEn.includes(term) ||
					descNl.includes(term)
				);
			});
		}

		return result;
	});

	function handleStatusFilter(filter: StatusFilter) {
		statusFilter = filter;
	}

	function handleRetry() {
		onRetry?.();
	}
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="sm:flex sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
				{$t('emailTemplates.title')}
			</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				{$t('emailTemplates.description')}
			</p>
		</div>
	</div>

	<!-- Filters and Search -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<!-- Status Filter Tabs -->
		<div class="flex gap-2">
			<button
				type="button"
				class="rounded-md px-3 py-2 text-sm font-medium {statusFilter === 'all'
					? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
					: 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'}"
				onclick={() => handleStatusFilter('all')}
			>
				{$t('emailTemplates.filters.all')}
			</button>
			<button
				type="button"
				class="rounded-md px-3 py-2 text-sm font-medium {statusFilter === 'active'
					? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
					: 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'}"
				onclick={() => handleStatusFilter('active')}
			>
				{$t('emailTemplates.filters.active')}
			</button>
			<button
				type="button"
				class="rounded-md px-3 py-2 text-sm font-medium {statusFilter === 'inactive'
					? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
					: 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'}"
				onclick={() => handleStatusFilter('inactive')}
			>
				{$t('emailTemplates.filters.inactive')}
			</button>
		</div>

		<!-- Search Input -->
		<div class="relative w-full sm:w-64">
			<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
				<svg
					class="h-5 w-5 text-gray-400"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
					/>
				</svg>
			</div>
			<input
				type="text"
				bind:value={searchTerm}
				placeholder={$t('emailTemplates.search.placeholder')}
				aria-label={$t('emailTemplates.search.ariaLabel')}
				class="block w-full rounded-md border-gray-300 pl-10 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
			/>
		</div>
	</div>

	<!-- Loading State -->
	{#if isLoading}
		<div class="flex items-center justify-center py-12">
			<div class="flex items-center gap-3">
				<svg
					class="h-6 w-6 animate-spin text-blue-600"
					fill="none"
					viewBox="0 0 24 24"
				>
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
				<span class="text-gray-600 dark:text-gray-400">
					{$t('emailTemplates.loading')}
				</span>
			</div>
		</div>
	{:else if error}
		<!-- Error State -->
		<div
			class="rounded-lg border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/20"
		>
			<svg
				class="mx-auto h-12 w-12 text-red-500"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				/>
			</svg>
			<h3 class="mt-2 text-lg font-medium text-red-800 dark:text-red-200">
				{$t('emailTemplates.error')}
			</h3>
			<p class="mt-1 text-sm text-red-600 dark:text-red-300">{error}</p>
			{#if onRetry}
				<button
					type="button"
					onclick={handleRetry}
					class="mt-4 rounded-md bg-red-100 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-200 dark:bg-red-900/50 dark:text-red-200 dark:hover:bg-red-900"
				>
					{$t('emailTemplates.retry')}
				</button>
			{/if}
		</div>
	{:else if filteredTemplates.length === 0}
		<!-- Empty State -->
		<div
			class="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center dark:border-gray-700"
		>
			<svg
				class="mx-auto h-12 w-12 text-gray-400"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
				/>
			</svg>
			<h3 class="mt-2 text-lg font-medium text-gray-900 dark:text-white">
				{$t('emailTemplates.noTemplates')}
			</h3>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				{$t('emailTemplates.noTemplatesDescription')}
			</p>
		</div>
	{:else}
		<!-- Template Grid -->
		<ul
			role="list"
			aria-label={$t('emailTemplates.list.ariaLabel')}
			class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
		>
			{#each filteredTemplates as template (template.id)}
				<li>
					<EmailTemplateCard
						{template}
						{onView}
						{onEdit}
						{onPreview}
						{onToggleActive}
					/>
				</li>
			{/each}
		</ul>
	{/if}
</div>
