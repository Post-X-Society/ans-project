import { browser } from '$app/environment';
import { init, register, locale, t, locales, addMessages } from 'svelte-i18n';

// Import translation files
import en from './locales/en.json';
import nl from './locales/nl.json';

// Supported locales
export const SUPPORTED_LOCALES = ['en', 'nl'] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];
export const DEFAULT_LOCALE: SupportedLocale = 'en';

// Language display names
export const LOCALE_NAMES: Record<SupportedLocale, string> = {
	en: 'English',
	nl: 'Nederlands'
};

// Local storage key for persisting language preference
const LOCALE_STORAGE_KEY = 'ans-locale';

/**
 * Register all locales with svelte-i18n
 */
function registerLocales() {
	// Use addMessages for immediate availability instead of async register
	// This ensures translations are available synchronously
	addMessages('en', en);
	addMessages('nl', nl);
}

/**
 * Get the initial locale based on user preferences
 */
function getInitialLocale(): SupportedLocale {
	if (browser) {
		// 1. Check localStorage for saved preference
		const savedLocale = localStorage.getItem(LOCALE_STORAGE_KEY);
		if (savedLocale && SUPPORTED_LOCALES.includes(savedLocale as SupportedLocale)) {
			return savedLocale as SupportedLocale;
		}

		// 2. Check browser language
		const browserLang = navigator.language.split('-')[0];
		if (SUPPORTED_LOCALES.includes(browserLang as SupportedLocale)) {
			return browserLang as SupportedLocale;
		}
	}

	// 3. Default to English
	return DEFAULT_LOCALE;
}

/**
 * Set and persist the locale
 */
export function setLocale(newLocale: SupportedLocale): void {
	if (!SUPPORTED_LOCALES.includes(newLocale)) {
		console.warn(`Unsupported locale: ${newLocale}, falling back to ${DEFAULT_LOCALE}`);
		newLocale = DEFAULT_LOCALE;
	}

	locale.set(newLocale);

	if (browser) {
		localStorage.setItem(LOCALE_STORAGE_KEY, newLocale);
		// Update HTML lang attribute for accessibility
		document.documentElement.lang = newLocale;
	}
}

/**
 * Get the current locale
 */
export function getCurrentLocale(): SupportedLocale {
	let currentLocale: SupportedLocale = DEFAULT_LOCALE;
	locale.subscribe((value) => {
		if (value && SUPPORTED_LOCALES.includes(value as SupportedLocale)) {
			currentLocale = value as SupportedLocale;
		}
	})();
	return currentLocale;
}

/**
 * Initialize the i18n system
 */
export function initI18n(): void {
	registerLocales();

	init({
		fallbackLocale: DEFAULT_LOCALE,
		initialLocale: getInitialLocale()
	});

	// Set HTML lang attribute on initial load
	if (browser) {
		const initialLocale = getInitialLocale();
		document.documentElement.lang = initialLocale;
	}
}

// Re-export svelte-i18n utilities
export { t, locale, locales };
