/**
 * CookieConsentBanner Component Tests
 * Issue #93: Frontend: Cookie Consent & GDPR Banners (TDD)
 * EPIC #53: GDPR & Data Retention Compliance
 *
 * TDD Red Phase: Tests written FIRST before implementation.
 * These tests define the expected behavior of the CookieConsentBanner component
 * for GDPR-compliant cookie consent management.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { locale } from 'svelte-i18n';
import CookieConsentBannerTest from './CookieConsentBannerTest.svelte';

// Mock localStorage
const localStorageMock = (() => {
	let store: Record<string, string> = {};
	return {
		getItem: vi.fn((key: string) => store[key] || null),
		setItem: vi.fn((key: string, value: string) => {
			store[key] = value;
		}),
		removeItem: vi.fn((key: string) => {
			delete store[key];
		}),
		clear: vi.fn(() => {
			store = {};
		})
	};
})();

Object.defineProperty(window, 'localStorage', {
	value: localStorageMock
});

describe('CookieConsentBanner', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		localStorageMock.clear();
		locale.set('en');
	});

	afterEach(() => {
		localStorageMock.clear();
	});

	describe('Initial Rendering', () => {
		it('should show banner when no consent is stored', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByTestId('cookie-consent-banner')).toBeInTheDocument();
			});
		});

		it('should hide banner when consent is already stored', async () => {
			localStorageMock.setItem(
				'ans-cookie-consent',
				JSON.stringify({
					essential: true,
					analytics: false,
					marketing: false,
					timestamp: Date.now()
				})
			);

			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.queryByTestId('cookie-consent-banner')).not.toBeInTheDocument();
			});
		});

		it('should display privacy message text', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByText(/we use cookies/i)).toBeInTheDocument();
			});
		});

		it('should have Accept All button', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /accept all/i })).toBeInTheDocument();
			});
		});

		it('should have Reject All button', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /reject all/i })).toBeInTheDocument();
			});
		});

		it('should have Customize button', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /customize/i })).toBeInTheDocument();
			});
		});

		it('should have link to privacy policy', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				const link = screen.getByRole('link', { name: /privacy policy/i });
				expect(link).toBeInTheDocument();
				expect(link).toHaveAttribute('href', '/about/privacy-policy');
			});
		});
	});

	describe('Accept All Action', () => {
		it('should save all preferences as true when Accept All is clicked', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByTestId('cookie-consent-banner')).toBeInTheDocument();
			});

			const acceptButton = screen.getByRole('button', { name: /accept all/i });
			await fireEvent.click(acceptButton);

			await waitFor(() => {
				const savedConsent = JSON.parse(localStorageMock.setItem.mock.calls[0][1]);
				expect(savedConsent.essential).toBe(true);
				expect(savedConsent.analytics).toBe(true);
				expect(savedConsent.marketing).toBe(true);
				expect(savedConsent.timestamp).toBeDefined();
			});
		});

		it('should hide banner after Accept All is clicked', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByTestId('cookie-consent-banner')).toBeInTheDocument();
			});

			const acceptButton = screen.getByRole('button', { name: /accept all/i });
			await fireEvent.click(acceptButton);

			await waitFor(() => {
				expect(screen.queryByTestId('cookie-consent-banner')).not.toBeInTheDocument();
			});
		});
	});

	describe('Reject All Action', () => {
		it('should save only essential preference as true when Reject All is clicked', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByTestId('cookie-consent-banner')).toBeInTheDocument();
			});

			const rejectButton = screen.getByRole('button', { name: /reject all/i });
			await fireEvent.click(rejectButton);

			await waitFor(() => {
				const savedConsent = JSON.parse(localStorageMock.setItem.mock.calls[0][1]);
				expect(savedConsent.essential).toBe(true);
				expect(savedConsent.analytics).toBe(false);
				expect(savedConsent.marketing).toBe(false);
				expect(savedConsent.timestamp).toBeDefined();
			});
		});

		it('should hide banner after Reject All is clicked', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByTestId('cookie-consent-banner')).toBeInTheDocument();
			});

			const rejectButton = screen.getByRole('button', { name: /reject all/i });
			await fireEvent.click(rejectButton);

			await waitFor(() => {
				expect(screen.queryByTestId('cookie-consent-banner')).not.toBeInTheDocument();
			});
		});
	});

	describe('Customize Action', () => {
		it('should open preferences modal when Customize is clicked', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByTestId('cookie-consent-banner')).toBeInTheDocument();
			});

			const customizeButton = screen.getByRole('button', { name: /customize/i });
			await fireEvent.click(customizeButton);

			await waitFor(() => {
				expect(screen.getByTestId('privacy-preferences-modal')).toBeInTheDocument();
			});
		});
	});

	describe('Accessibility', () => {
		it('should have proper ARIA role for the banner', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				const banner = screen.getByTestId('cookie-consent-banner');
				expect(banner).toHaveAttribute('role', 'dialog');
			});
		});

		it('should have aria-label for the banner', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				const banner = screen.getByTestId('cookie-consent-banner');
				expect(banner).toHaveAttribute('aria-label');
			});
		});

		it('should have aria-describedby pointing to the description', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				const banner = screen.getByTestId('cookie-consent-banner');
				expect(banner).toHaveAttribute('aria-describedby');
			});
		});
	});

	describe('Internationalization', () => {
		it('should display translated text when locale is Dutch', async () => {
			locale.set('nl');

			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByText(/wij gebruiken cookies/i)).toBeInTheDocument();
			});
		});

		it('should have translated Accept All button in Dutch', async () => {
			locale.set('nl');

			render(CookieConsentBannerTest);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /alles accepteren/i })).toBeInTheDocument();
			});
		});
	});

	describe('Banner Position', () => {
		it('should be fixed at the bottom of the page', async () => {
			render(CookieConsentBannerTest);

			await waitFor(() => {
				const banner = screen.getByTestId('cookie-consent-banner');
				expect(banner).toHaveClass('fixed', 'bottom-0');
			});
		});
	});
});
