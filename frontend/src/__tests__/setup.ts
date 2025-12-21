import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/svelte';
import * as matchers from '@testing-library/jest-dom/matchers';
import { init, register, locale } from 'svelte-i18n';

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Initialize svelte-i18n for tests
register('en', () => import('$lib/i18n/locales/en.json'));
register('nl', () => import('$lib/i18n/locales/nl.json'));

init({
	fallbackLocale: 'en',
	initialLocale: 'en'
});

// Set locale synchronously for tests
locale.set('en');

// Cleanup after each test
afterEach(() => {
	cleanup();
});
