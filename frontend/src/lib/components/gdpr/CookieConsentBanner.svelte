<!--
  CookieConsentBanner Component
  Issue #93: Frontend: Cookie Consent & GDPR Banners (TDD)
  EPIC #53: GDPR & Data Retention Compliance

  GDPR-compliant cookie consent banner with Accept All, Reject All, and Customize options.
  Persists preferences to localStorage with consent timestamp.
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';
	import PrivacyPreferencesModal from './PrivacyPreferencesModal.svelte';

	const CONSENT_KEY = 'ans-cookie-consent';

	interface CookieConsent {
		essential: boolean;
		analytics: boolean;
		marketing: boolean;
		timestamp: number;
	}

	let showBanner = $state(false);
	let showPreferencesModal = $state(false);

	onMount(() => {
		if (browser) {
			const stored = localStorage.getItem(CONSENT_KEY);
			if (!stored) {
				showBanner = true;
			}
		}
	});

	function saveConsent(consent: CookieConsent) {
		if (browser) {
			localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
		}
		showBanner = false;
	}

	function handleAcceptAll() {
		saveConsent({
			essential: true,
			analytics: true,
			marketing: true,
			timestamp: Date.now()
		});
	}

	function handleRejectAll() {
		saveConsent({
			essential: true,
			analytics: false,
			marketing: false,
			timestamp: Date.now()
		});
	}

	function handleCustomize() {
		showPreferencesModal = true;
	}

	function handlePreferencesClose() {
		showPreferencesModal = false;
		// Check if consent was saved in the modal
		if (browser) {
			const stored = localStorage.getItem(CONSENT_KEY);
			if (stored) {
				showBanner = false;
			}
		}
	}
</script>

{#if showBanner}
	<div
		data-testid="cookie-consent-banner"
		role="dialog"
		aria-label={$t('cookieConsent.banner.ariaLabel')}
		aria-describedby="cookie-consent-description"
		class="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-lg"
	>
		<div class="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
			<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
				<div class="flex-1">
					<h2 class="text-lg font-semibold text-gray-900">
						{$t('cookieConsent.banner.title')}
					</h2>
					<p id="cookie-consent-description" class="mt-1 text-sm text-gray-600">
						{$t('cookieConsent.banner.message')}
						<a
							href="/about/privacy-policy"
							class="text-primary-600 hover:text-primary-700 underline"
						>
							{$t('cookieConsent.banner.privacyPolicy')}
						</a>
					</p>
				</div>

				<div class="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto">
					<button
						onclick={handleCustomize}
						class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
					>
						{$t('cookieConsent.banner.customize')}
					</button>
					<button
						onclick={handleRejectAll}
						class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
					>
						{$t('cookieConsent.banner.rejectAll')}
					</button>
					<button
						onclick={handleAcceptAll}
						class="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
					>
						{$t('cookieConsent.banner.acceptAll')}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<PrivacyPreferencesModal open={showPreferencesModal} onClose={handlePreferencesClose} />
