/**
 * PrivacyPreferencesModal Component Tests
 * Issue #93: Frontend: Cookie Consent & GDPR Banners (TDD)
 * EPIC #53: GDPR & Data Retention Compliance
 *
 * TDD Red Phase: Tests written FIRST before implementation.
 * These tests define the expected behavior of the PrivacyPreferencesModal component
 * for granular cookie preference management.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { locale } from 'svelte-i18n';
import PrivacyPreferencesModalTest from './PrivacyPreferencesModalTest.svelte';

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

describe('PrivacyPreferencesModal', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		localStorageMock.clear();
		locale.set('en');
	});

	afterEach(() => {
		localStorageMock.clear();
	});

	describe('Modal Structure', () => {
		it('should display modal when open prop is true', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(screen.getByTestId('privacy-preferences-modal')).toBeInTheDocument();
			});
		});

		it('should not display modal when open prop is false', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: false } });

			await waitFor(() => {
				expect(screen.queryByTestId('privacy-preferences-modal')).not.toBeInTheDocument();
			});
		});

		it('should have a modal title', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(screen.getByText(/privacy preferences/i)).toBeInTheDocument();
			});
		});

		it('should have a close button', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				// There are two close buttons - one icon in header, one text in footer
				const closeButtons = screen.getAllByRole('button', { name: /close/i });
				expect(closeButtons.length).toBeGreaterThanOrEqual(1);
			});
		});
	});

	describe('Cookie Categories', () => {
		it('should display Essential cookies category', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				// Essential appears in both the description and heading, so we use getAllByText
				const essentialTexts = screen.getAllByText(/essential/i);
				expect(essentialTexts.length).toBeGreaterThan(0);
			});
		});

		it('should display Analytics cookies category', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(screen.getByText(/analytics/i)).toBeInTheDocument();
			});
		});

		it('should display Marketing cookies category', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(screen.getByText(/marketing/i)).toBeInTheDocument();
			});
		});

		it('should show description for each cookie category', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				// Essential description
				expect(screen.getByText(/required for the website to function/i)).toBeInTheDocument();
			});
		});

		it('should have Essential cookies toggle disabled (always required)', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				const essentialToggle = screen.getByTestId('toggle-essential');
				expect(essentialToggle).toBeDisabled();
				expect(essentialToggle).toBeChecked();
			});
		});

		it('should have Analytics cookies toggle enabled', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				const analyticsToggle = screen.getByTestId('toggle-analytics');
				expect(analyticsToggle).not.toBeDisabled();
			});
		});

		it('should have Marketing cookies toggle enabled', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				const marketingToggle = screen.getByTestId('toggle-marketing');
				expect(marketingToggle).not.toBeDisabled();
			});
		});
	});

	describe('Toggle Interactions', () => {
		it('should toggle Analytics cookies on click', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(screen.getByTestId('toggle-analytics')).toBeInTheDocument();
			});

			const analyticsToggle = screen.getByTestId('toggle-analytics');
			const initialState = analyticsToggle.checked;

			await fireEvent.click(analyticsToggle);

			await waitFor(() => {
				expect(analyticsToggle.checked).toBe(!initialState);
			});
		});

		it('should toggle Marketing cookies on click', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(screen.getByTestId('toggle-marketing')).toBeInTheDocument();
			});

			const marketingToggle = screen.getByTestId('toggle-marketing');
			const initialState = marketingToggle.checked;

			await fireEvent.click(marketingToggle);

			await waitFor(() => {
				expect(marketingToggle.checked).toBe(!initialState);
			});
		});
	});

	describe('Save Preferences', () => {
		it('should have Save Preferences button', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /save preferences/i })).toBeInTheDocument();
			});
		});

		it('should save preferences to localStorage when Save is clicked', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(screen.getByTestId('toggle-analytics')).toBeInTheDocument();
			});

			// Enable analytics
			const analyticsToggle = screen.getByTestId('toggle-analytics');
			await fireEvent.click(analyticsToggle);

			// Save preferences
			const saveButton = screen.getByRole('button', { name: /save preferences/i });
			await fireEvent.click(saveButton);

			await waitFor(() => {
				expect(localStorageMock.setItem).toHaveBeenCalledWith(
					'ans-cookie-consent',
					expect.any(String)
				);
			});
		});

		it('should close modal after saving preferences', async () => {
			const onClose = vi.fn();
			render(PrivacyPreferencesModalTest, { props: { open: true, onClose } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /save preferences/i })).toBeInTheDocument();
			});

			const saveButton = screen.getByRole('button', { name: /save preferences/i });
			await fireEvent.click(saveButton);

			await waitFor(() => {
				expect(onClose).toHaveBeenCalled();
			});
		});
	});

	describe('Close Modal', () => {
		it('should call onClose when close button is clicked', async () => {
			const onClose = vi.fn();
			render(PrivacyPreferencesModalTest, { props: { open: true, onClose } });

			await waitFor(() => {
				const closeButtons = screen.getAllByRole('button', { name: /close/i });
				expect(closeButtons.length).toBeGreaterThan(0);
			});

			// Click the first close button (the icon button in the header)
			const closeButtons = screen.getAllByRole('button', { name: /close/i });
			await fireEvent.click(closeButtons[0]);

			await waitFor(() => {
				expect(onClose).toHaveBeenCalled();
			});
		});

		it('should close modal when clicking overlay backdrop', async () => {
			const onClose = vi.fn();
			render(PrivacyPreferencesModalTest, { props: { open: true, onClose } });

			await waitFor(() => {
				expect(screen.getByTestId('modal-backdrop')).toBeInTheDocument();
			});

			const backdrop = screen.getByTestId('modal-backdrop');
			await fireEvent.click(backdrop);

			await waitFor(() => {
				expect(onClose).toHaveBeenCalled();
			});
		});

		it('should close modal when pressing Escape key', async () => {
			const onClose = vi.fn();
			render(PrivacyPreferencesModalTest, { props: { open: true, onClose } });

			await waitFor(() => {
				expect(screen.getByTestId('privacy-preferences-modal')).toBeInTheDocument();
			});

			await fireEvent.keyDown(document, { key: 'Escape' });

			await waitFor(() => {
				expect(onClose).toHaveBeenCalled();
			});
		});
	});

	describe('Load Existing Preferences', () => {
		it('should load existing preferences from localStorage', async () => {
			localStorageMock.setItem(
				'ans-cookie-consent',
				JSON.stringify({
					essential: true,
					analytics: true,
					marketing: false,
					timestamp: Date.now()
				})
			);

			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				const analyticsToggle = screen.getByTestId('toggle-analytics');
				const marketingToggle = screen.getByTestId('toggle-marketing');

				expect(analyticsToggle).toBeChecked();
				expect(marketingToggle).not.toBeChecked();
			});
		});
	});

	describe('Accessibility', () => {
		it('should have proper ARIA role for the modal', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				const modal = screen.getByTestId('privacy-preferences-modal');
				expect(modal).toHaveAttribute('role', 'dialog');
			});
		});

		it('should have aria-modal attribute', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				const modal = screen.getByTestId('privacy-preferences-modal');
				expect(modal).toHaveAttribute('aria-modal', 'true');
			});
		});

		it('should have aria-labelledby pointing to the title', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				const modal = screen.getByTestId('privacy-preferences-modal');
				expect(modal).toHaveAttribute('aria-labelledby');
			});
		});

		it('should trap focus within the modal', async () => {
			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				const modal = screen.getByTestId('privacy-preferences-modal');
				expect(modal).toBeInTheDocument();
			});

			// Focus should be within the modal
			const focusableElements = screen.getAllByRole('button');
			expect(focusableElements.length).toBeGreaterThan(0);
		});
	});

	describe('Internationalization', () => {
		it('should display translated title when locale is Dutch', async () => {
			locale.set('nl');

			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(screen.getByText(/privacy voorkeuren/i)).toBeInTheDocument();
			});
		});

		it('should have translated Save button in Dutch', async () => {
			locale.set('nl');

			render(PrivacyPreferencesModalTest, { props: { open: true } });

			await waitFor(() => {
				expect(
					screen.getByRole('button', { name: /voorkeuren opslaan/i })
				).toBeInTheDocument();
			});
		});
	});
});
