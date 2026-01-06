<!--
  PrivacyPreferencesModal Component
  Issue #93: Frontend: Cookie Consent & GDPR Banners (TDD)
  EPIC #53: GDPR & Data Retention Compliance

  Modal for granular cookie preference management with toggle switches
  for each cookie category (Essential, Analytics, Marketing).
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';

	const CONSENT_KEY = 'ans-cookie-consent';

	interface Props {
		open: boolean;
		onClose: () => void;
	}

	interface CookieConsent {
		essential: boolean;
		analytics: boolean;
		marketing: boolean;
		timestamp: number;
	}

	let { open, onClose }: Props = $props();

	let essential = $state(true); // Always true, cannot be disabled
	let analytics = $state(false);
	let marketing = $state(false);

	// Load existing preferences when modal opens
	$effect(() => {
		if (open && browser) {
			const stored = localStorage.getItem(CONSENT_KEY);
			if (stored) {
				try {
					const consent: CookieConsent = JSON.parse(stored);
					essential = consent.essential;
					analytics = consent.analytics;
					marketing = consent.marketing;
				} catch {
					// Invalid stored data, use defaults
				}
			}
		}
	});

	// Handle Escape key
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && open) {
			onClose();
		}
	}

	function handleBackdropClick() {
		onClose();
	}

	function handleSavePreferences() {
		if (browser) {
			const consent: CookieConsent = {
				essential: true, // Always true
				analytics,
				marketing,
				timestamp: Date.now()
			};
			localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
		}
		onClose();
	}

	onMount(() => {
		document.addEventListener('keydown', handleKeydown);
		return () => {
			document.removeEventListener('keydown', handleKeydown);
		};
	});
</script>

{#if open}
	<!-- Backdrop -->
	<div
		data-testid="modal-backdrop"
		class="fixed inset-0 z-50 bg-black bg-opacity-50 transition-opacity"
		onclick={handleBackdropClick}
		onkeydown={(e) => e.key === 'Enter' && handleBackdropClick()}
		role="presentation"
		tabindex="-1"
		aria-hidden="true"
	></div>

	<!-- Modal -->
	<div
		data-testid="privacy-preferences-modal"
		role="dialog"
		aria-modal="true"
		aria-labelledby="preferences-modal-title"
		class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
	>
		<div
			class="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto pointer-events-auto"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
			role="presentation"
		>
			<!-- Header -->
			<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
				<h2 id="preferences-modal-title" class="text-xl font-semibold text-gray-900">
					{$t('cookieConsent.preferences.title')}
				</h2>
				<button
					onclick={onClose}
					class="text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
					aria-label={$t('common.close')}
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Body -->
			<div class="px-6 py-4">
				<p class="text-sm text-gray-600 mb-6">
					{$t('cookieConsent.preferences.description')}
				</p>

				<!-- Cookie Categories -->
				<div class="space-y-4">
					<!-- Essential Cookies -->
					<div class="flex items-start justify-between p-4 bg-gray-50 rounded-lg">
						<div class="flex-1 pr-4">
							<h3 class="text-sm font-medium text-gray-900">
								{$t('cookieConsent.preferences.categories.essential.title')}
							</h3>
							<p class="text-sm text-gray-500 mt-1">
								{$t('cookieConsent.preferences.categories.essential.description')}
							</p>
						</div>
						<div class="flex items-center">
							<input
								type="checkbox"
								data-testid="toggle-essential"
								checked={essential}
								disabled
								class="h-4 w-4 text-primary-600 border-gray-300 rounded cursor-not-allowed opacity-60"
							/>
							<span class="ml-2 text-xs text-gray-500">
								{$t('cookieConsent.preferences.categories.essential.alwaysActive')}
							</span>
						</div>
					</div>

					<!-- Analytics Cookies -->
					<div class="flex items-start justify-between p-4 bg-gray-50 rounded-lg">
						<div class="flex-1 pr-4">
							<h3 class="text-sm font-medium text-gray-900">
								{$t('cookieConsent.preferences.categories.analytics.title')}
							</h3>
							<p class="text-sm text-gray-500 mt-1">
								{$t('cookieConsent.preferences.categories.analytics.description')}
							</p>
						</div>
						<div class="flex items-center">
							<label class="relative inline-flex items-center cursor-pointer">
								<input
									type="checkbox"
									data-testid="toggle-analytics"
									bind:checked={analytics}
									class="sr-only peer"
								/>
								<div
									class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"
								></div>
							</label>
						</div>
					</div>

					<!-- Marketing Cookies -->
					<div class="flex items-start justify-between p-4 bg-gray-50 rounded-lg">
						<div class="flex-1 pr-4">
							<h3 class="text-sm font-medium text-gray-900">
								{$t('cookieConsent.preferences.categories.marketing.title')}
							</h3>
							<p class="text-sm text-gray-500 mt-1">
								{$t('cookieConsent.preferences.categories.marketing.description')}
							</p>
						</div>
						<div class="flex items-center">
							<label class="relative inline-flex items-center cursor-pointer">
								<input
									type="checkbox"
									data-testid="toggle-marketing"
									bind:checked={marketing}
									class="sr-only peer"
								/>
								<div
									class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"
								></div>
							</label>
						</div>
					</div>
				</div>
			</div>

			<!-- Footer -->
			<div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
				<button
					onclick={onClose}
					class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
				>
					{$t('common.close')}
				</button>
				<button
					onclick={handleSavePreferences}
					class="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
				>
					{$t('cookieConsent.preferences.savePreferences')}
				</button>
			</div>
		</div>
	</div>
{/if}
