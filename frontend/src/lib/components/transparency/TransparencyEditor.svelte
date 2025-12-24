<!--
  TransparencyEditor Component

  Issue #86: Frontend: Admin Transparency Page Editor
  EPIC #51: Transparency & Methodology Pages
  ADR 0005: EFCSN Compliance Architecture

  Admin-only component for editing transparency pages with:
  - Markdown editor with CodeMirror
  - Language tabs (EN/NL)
  - Live preview
  - Version history sidebar
  - Diff viewer between versions
  - Mark as reviewed button
-->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { t, locale } from '$lib/i18n';
	import type { SupportedLocale } from '$lib/i18n';
	import {
		getTransparencyPage,
		updateTransparencyPage,
		getTransparencyPageVersions,
		getTransparencyPageDiff,
		markTransparencyPageReviewed
	} from '$lib/api/transparency';
	import type {
		TransparencyPage,
		TransparencyPageVersion,
		TransparencyPageDiff
	} from '$lib/api/types';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';

	// CodeMirror imports
	import { EditorView, basicSetup } from 'codemirror';
	import { EditorState } from '@codemirror/state';
	import { markdown } from '@codemirror/lang-markdown';
	import { oneDark } from '@codemirror/theme-one-dark';

	interface Props {
		slug: string;
	}

	let { slug }: Props = $props();

	// Page state
	let page = $state<TransparencyPage | null>(null);
	let error = $state<string | null>(null);
	let isLoading = $state(true);
	let isSaving = $state(false);
	let isMarkingReviewed = $state(false);
	let saveSuccess = $state(false);

	// Editor state
	let selectedLang = $state<SupportedLocale>('en');
	let editedTitle = $state<Record<string, string>>({ en: '', nl: '' });
	let editedContent = $state<Record<string, string>>({ en: '', nl: '' });
	let changeSummary = $state('');

	// Version history state
	let versions = $state<TransparencyPageVersion[]>([]);
	let isLoadingVersions = $state(false);
	let showDiff = $state(false);
	let selectedVersionForDiff = $state<number | null>(null);
	let diffData = $state<TransparencyPageDiff | null>(null);
	let isLoadingDiff = $state(false);

	// CodeMirror
	let editorContainer: HTMLDivElement;
	let editorView: EditorView | null = null;

	// Computed values
	let currentTitle = $derived(editedTitle[selectedLang] || '');
	let currentContent = $derived(editedContent[selectedLang] || '');

	// Parse markdown to HTML and sanitize
	let renderedPreview = $derived(() => {
		if (!currentContent) return '';
		const html = marked.parse(currentContent);
		if (browser && typeof html === 'string') {
			return DOMPurify.sanitize(html);
		}
		return typeof html === 'string' ? html : '';
	});

	// Format dates
	function formatDate(dateString: string | null): string {
		if (!dateString) return 'N/A';
		const date = new Date(dateString);
		return new Intl.DateTimeFormat('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		}).format(date);
	}

	// Format date for version history
	function formatVersionDate(dateString: string): string {
		const date = new Date(dateString);
		return new Intl.DateTimeFormat('en-US', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		}).format(date);
	}

	// Initialize CodeMirror editor
	function initEditor() {
		if (!browser || !editorContainer || editorView) return;

		const state = EditorState.create({
			doc: currentContent,
			extensions: [
				basicSetup,
				markdown(),
				oneDark,
				EditorView.updateListener.of((update) => {
					if (update.docChanged) {
						editedContent[selectedLang] = update.state.doc.toString();
					}
				}),
				EditorView.theme({
					'&': { height: '400px' },
					'.cm-scroller': { overflow: 'auto' }
				})
			]
		});

		editorView = new EditorView({
			state,
			parent: editorContainer
		});
	}

	// Update editor content when language changes
	function updateEditorContent() {
		if (!editorView) return;

		const newContent = editedContent[selectedLang] || '';
		editorView.dispatch({
			changes: {
				from: 0,
				to: editorView.state.doc.length,
				insert: newContent
			}
		});
	}

	// Load page data
	async function loadPage() {
		isLoading = true;
		error = null;

		try {
			page = await getTransparencyPage(slug);
			editedTitle = { ...page.title };
			editedContent = { ...page.content };
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load page';
			page = null;
		} finally {
			isLoading = false;
		}
	}

	// Load version history
	async function loadVersions() {
		isLoadingVersions = true;
		try {
			versions = await getTransparencyPageVersions(slug);
		} catch (err) {
			console.error('Failed to load version history:', err);
			versions = [];
		} finally {
			isLoadingVersions = false;
		}
	}

	// Load diff between versions
	async function loadDiff(fromVersion: number) {
		if (!page) return;

		isLoadingDiff = true;
		selectedVersionForDiff = fromVersion;
		showDiff = true;

		try {
			diffData = await getTransparencyPageDiff(slug, fromVersion, page.version, selectedLang);
		} catch (err) {
			console.error('Failed to load diff:', err);
			diffData = null;
		} finally {
			isLoadingDiff = false;
		}
	}

	// Save changes
	async function handleSave() {
		if (!changeSummary.trim()) {
			error = 'Please provide a change summary';
			return;
		}

		isSaving = true;
		error = null;
		saveSuccess = false;

		try {
			const updatedPage = await updateTransparencyPage(slug, {
				title: editedTitle,
				content: editedContent,
				change_summary: changeSummary
			});

			page = updatedPage;
			changeSummary = '';
			saveSuccess = true;

			// Reload versions
			await loadVersions();

			// Hide success message after 3 seconds
			setTimeout(() => {
				saveSuccess = false;
			}, 3000);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to save changes';
		} finally {
			isSaving = false;
		}
	}

	// Mark page as reviewed
	async function handleMarkReviewed() {
		isMarkingReviewed = true;
		error = null;

		try {
			page = await markTransparencyPageReviewed(slug);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to mark as reviewed';
		} finally {
			isMarkingReviewed = false;
		}
	}

	// Switch language tab
	function switchLanguage(lang: SupportedLocale) {
		selectedLang = lang;
		updateEditorContent();
	}

	// Close diff viewer
	function closeDiff() {
		showDiff = false;
		selectedVersionForDiff = null;
		diffData = null;
	}

	// Lifecycle
	onMount(() => {
		loadPage();
		loadVersions();
	});

	onDestroy(() => {
		if (editorView) {
			editorView.destroy();
			editorView = null;
		}
	});

	// Initialize editor after page loads
	$effect(() => {
		if (page && browser && editorContainer && !editorView) {
			initEditor();
		}
	});

	// Update editor when language changes
	$effect(() => {
		if (selectedLang && editorView) {
			updateEditorContent();
		}
	});
</script>

<div class="min-h-screen bg-gray-50">
	{#if isLoading}
		<div class="flex items-center justify-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
			<span class="ml-3 text-gray-600">{$t('transparency.editor.loading')}</span>
		</div>
	{:else if error && !page}
		<div class="max-w-4xl mx-auto px-4 py-8">
			<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
				<h2 class="text-lg font-semibold text-red-800 mb-2">{$t('common.error')}</h2>
				<p class="text-red-600">{error}</p>
				<button
					onclick={() => loadPage()}
					class="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
				>
					{$t('common.tryAgain')}
				</button>
			</div>
		</div>
	{:else if page}
		<div class="max-w-7xl mx-auto px-4 py-6">
			<!-- Header -->
			<header class="mb-6">
				<h1 class="text-2xl font-bold text-gray-900">
					{$t('transparency.editor.title')}: {page.title[$locale as string] || page.title['en']}
				</h1>
				<div class="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500">
					<span>{$t('transparency.editor.currentVersion')}: Version {page.version}</span>
					<span>|</span>
					<span>
						{$t('transparency.editor.nextReview')}: {formatDate(page.next_review_due)}
					</span>
				</div>
			</header>

			<!-- Success/Error Messages -->
			{#if saveSuccess}
				<div class="mb-4 bg-green-50 border border-green-200 rounded-lg p-4">
					<p class="text-green-800">{$t('transparency.editor.savedSuccessfully')}</p>
				</div>
			{/if}

			{#if error}
				<div class="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
					<p class="text-red-800">{error}</p>
				</div>
			{/if}

			<div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
				<!-- Main Editor Area (3 cols) -->
				<div class="lg:col-span-3 space-y-6">
					<!-- Language Tabs -->
					<div class="bg-white rounded-lg shadow-sm">
						<div role="tablist" class="flex border-b border-gray-200">
							<button
								role="tab"
								aria-selected={selectedLang === 'en'}
								onclick={() => switchLanguage('en')}
								class="px-6 py-3 text-sm font-medium transition-colors {selectedLang === 'en'
									? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50'
									: 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}"
							>
								English
							</button>
							<button
								role="tab"
								aria-selected={selectedLang === 'nl'}
								onclick={() => switchLanguage('nl')}
								class="px-6 py-3 text-sm font-medium transition-colors {selectedLang === 'nl'
									? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50'
									: 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}"
							>
								Nederlands
							</button>
						</div>

						<!-- Title Input -->
						<div class="p-4 border-b border-gray-200">
							<label for="title-input" class="block text-sm font-medium text-gray-700 mb-2">
								{$t('transparency.editor.pageTitle')} ({selectedLang.toUpperCase()})
							</label>
							<input
								id="title-input"
								type="text"
								bind:value={editedTitle[selectedLang]}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
								placeholder={$t('transparency.editor.titlePlaceholder')}
							/>
						</div>

						<!-- Editor and Preview -->
						<div class="grid grid-cols-1 xl:grid-cols-2">
							<!-- Markdown Editor -->
							<div class="border-r border-gray-200 p-4">
								<h3 class="text-sm font-medium text-gray-700 mb-2">
									{$t('transparency.editor.markdownEditor')}
								</h3>
								<div
									bind:this={editorContainer}
									data-testid="markdown-editor"
									class="border border-gray-300 rounded-md overflow-hidden"
								></div>
							</div>

							<!-- Live Preview -->
							<div class="p-4">
								<h3 class="text-sm font-medium text-gray-700 mb-2">
									{$t('transparency.editor.preview')}
								</h3>
								<div
									data-testid="preview-pane"
									class="border border-gray-200 rounded-md p-4 h-[400px] overflow-auto bg-gray-50"
								>
									<div class="prose prose-gray max-w-none">
										<!-- eslint-disable-next-line svelte/no-at-html-tags -- sanitized with DOMPurify -->
										{@html renderedPreview()}
									</div>
								</div>
							</div>
						</div>
					</div>

					<!-- Save Section -->
					<div class="bg-white rounded-lg shadow-sm p-4">
						<div class="space-y-4">
							<div>
								<label for="change-summary" class="block text-sm font-medium text-gray-700 mb-2">
									{$t('transparency.editor.changeSummary')} *
								</label>
								<input
									id="change-summary"
									type="text"
									bind:value={changeSummary}
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
									placeholder={$t('transparency.editor.changeSummaryPlaceholder')}
								/>
							</div>

							<div class="flex items-center justify-between">
								<button
									onclick={handleMarkReviewed}
									disabled={isMarkingReviewed}
									class="px-4 py-2 border border-green-600 text-green-600 rounded-md hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
								>
									{#if isMarkingReviewed}
										{$t('transparency.editor.markingReviewed')}
									{:else}
										{$t('transparency.editor.markAsReviewed')}
									{/if}
								</button>

								<button
									onclick={handleSave}
									disabled={isSaving || !changeSummary.trim()}
									class="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
								>
									{#if isSaving}
										{$t('transparency.editor.saving')}
									{:else}
										{$t('common.save')}
									{/if}
								</button>
							</div>
						</div>
					</div>
				</div>

				<!-- Version History Sidebar (1 col) -->
				<div class="lg:col-span-1">
					<div class="bg-white rounded-lg shadow-sm p-4 sticky top-4">
						<h2 class="text-lg font-semibold text-gray-900 mb-4">
							{$t('transparency.editor.versionHistory')}
						</h2>

						{#if isLoadingVersions}
							<div class="flex items-center justify-center py-4">
								<div class="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
							</div>
						{:else if versions.length === 0}
							<p class="text-sm text-gray-500">{$t('transparency.editor.noVersionHistory')}</p>
						{:else}
							<div class="space-y-3">
								{#each versions as version (version.id)}
									<div class="border border-gray-200 rounded-md p-3">
										<div class="flex items-center justify-between mb-1">
											<span class="text-sm font-medium text-gray-900">
												Version {version.version}
											</span>
											<button
												onclick={() => loadDiff(version.version)}
												class="text-xs text-primary-600 hover:text-primary-800"
											>
												{$t('transparency.editor.compare')}
											</button>
										</div>
										<p class="text-xs text-gray-500 mb-1">
											{formatVersionDate(version.created_at)}
										</p>
										{#if version.change_summary}
											<p class="text-xs text-gray-600">{version.change_summary}</p>
										{/if}
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- Diff Viewer Modal -->
			{#if showDiff}
				<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
					<div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
						<div class="flex items-center justify-between p-4 border-b border-gray-200">
							<h3 class="text-lg font-semibold text-gray-900">
								{$t('transparency.editor.diffTitle', {
									values: {
										from: selectedVersionForDiff,
										to: page?.version
									}
								})}
							</h3>
							<button
								onclick={closeDiff}
								class="text-gray-400 hover:text-gray-600"
								aria-label="Close"
							>
								<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M6 18L18 6M6 6l12 12"
									/>
								</svg>
							</button>
						</div>

						<div data-testid="diff-viewer" class="p-4 overflow-auto max-h-[calc(90vh-80px)]">
							{#if isLoadingDiff}
								<div class="flex items-center justify-center py-8">
									<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
								</div>
							{:else if diffData}
								<div class="font-mono text-sm whitespace-pre-wrap bg-gray-50 p-4 rounded-md">
									{#if diffData.diff && typeof diffData.diff === 'object'}
										{#each Object.entries(diffData.diff) as [lang, langDiff]}
											<div class="mb-4">
												<h4 class="font-bold text-gray-700 mb-2">
													{lang === 'en' ? 'English' : 'Nederlands'}
												</h4>
												{#if typeof langDiff === 'object' && langDiff !== null}
													{#if 'content' in langDiff}
														<div class="diff-content">
															{#each String(langDiff.content).split('\n') as line}
																<div
																	class="{line.startsWith('+')
																		? 'bg-green-100 text-green-800'
																		: line.startsWith('-')
																			? 'bg-red-100 text-red-800'
																			: ''}"
																>
																	{line}
																</div>
															{/each}
														</div>
													{/if}
												{/if}
											</div>
										{/each}
									{:else}
										<p class="text-gray-500">
											{$t('transparency.editor.noDiffAvailable')}
										</p>
									{/if}
								</div>
							{:else}
								<p class="text-gray-500">{$t('transparency.editor.noDiffAvailable')}</p>
							{/if}
						</div>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>
