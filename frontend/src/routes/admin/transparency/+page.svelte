<!--
  Admin Transparency Pages List

  Issue #86: Frontend: Admin Transparency Page Editor
  EPIC #51: Transparency & Methodology Pages

  Lists all transparency pages with links to edit each one.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get } from 'svelte/store';
	import { isAdmin, isAuthenticated } from '$lib/stores/auth';
	import { t } from '$lib/i18n';
	import { getTransparencyPages } from '$lib/api/transparency';
	import type { TransparencyPageSummary } from '$lib/api/types';

	let pages = $state<TransparencyPageSummary[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let canAccess = $derived($isAuthenticated && $isAdmin);
	let isCheckingAuth = $state(true);

	// Format date
	function formatDate(dateString: string | null): string {
		if (!dateString) return 'N/A';
		const date = new Date(dateString);
		return new Intl.DateTimeFormat('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		}).format(date);
	}

	// Check if review is overdue
	function isOverdue(dateString: string | null): boolean {
		if (!dateString) return false;
		return new Date(dateString) < new Date();
	}

	async function loadPages() {
		isLoading = true;
		error = null;

		try {
			const response = await getTransparencyPages();
			pages = response.items;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load pages';
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		// Wait a tick for auth state to load from localStorage
		setTimeout(() => {
			isCheckingAuth = false;

			// Use get() to access store value inside callback
			const currentPage = get(page);
			const authenticated = get(isAuthenticated);
			const admin = get(isAdmin);

			if (!authenticated) {
				goto('/login?redirect=' + encodeURIComponent(currentPage.url.pathname));
			} else if (!admin) {
				goto('/');
			} else {
				loadPages();
			}
		}, 100);
	});
</script>

<svelte:head>
	<title>{$t('admin.transparencyPages')} | {$t('common.appName')}</title>
</svelte:head>

{#if isCheckingAuth}
	<div class="flex items-center justify-center min-h-screen">
		<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
	</div>
{:else if !canAccess}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<h1 class="text-2xl font-bold text-gray-900 mb-4">{$t('errors.unauthorized')}</h1>
			<p class="text-gray-600 mb-4">You must be an admin to access this page.</p>
			<a href="/login" class="text-primary-600 hover:text-primary-800">
				{$t('nav.login')}
			</a>
		</div>
	</div>
{:else}
	<div class="container mx-auto px-4 py-8">
		<div class="max-w-4xl mx-auto">
			<header class="mb-8">
				<h1 class="text-3xl font-bold text-gray-900">Transparency Pages</h1>
				<p class="mt-2 text-gray-600">
					Manage EFCSN-required transparency pages. Click on a page to edit its content.
				</p>
			</header>

			{#if isLoading}
				<div class="flex items-center justify-center py-12">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
					<span class="ml-3 text-gray-600">{$t('common.loading')}</span>
				</div>
			{:else if error}
				<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
					<h2 class="text-lg font-semibold text-red-800 mb-2">{$t('common.error')}</h2>
					<p class="text-red-600">{error}</p>
					<button
						onclick={() => loadPages()}
						class="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
					>
						{$t('common.tryAgain')}
					</button>
				</div>
			{:else}
				<div class="space-y-4">
					{#each pages as page (page.id)}
						<a
							href="/admin/transparency/{page.slug}"
							class="block bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-primary-300 transition-all"
						>
							<div class="flex items-start justify-between">
								<div class="flex-1">
									<h2 class="text-lg font-semibold text-gray-900">
										{page.title['en'] || page.slug}
									</h2>
									<p class="text-sm text-gray-500 mt-1">
										/{page.slug}
									</p>
								</div>

								<div class="text-right">
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
										Version {page.version}
									</span>
								</div>
							</div>

							<div class="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-500">
								<span>
									Last updated: {formatDate(page.updated_at)}
								</span>
								<span>|</span>
								<span class={isOverdue(page.next_review_due) ? 'text-red-600 font-medium' : ''}>
									Next review: {formatDate(page.next_review_due)}
									{#if isOverdue(page.next_review_due)}
										<span class="ml-1 text-red-600">(Overdue)</span>
									{/if}
								</span>
							</div>
						</a>
					{/each}

					{#if pages.length === 0}
						<div class="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
							<p class="text-gray-600">No transparency pages found.</p>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
{/if}
