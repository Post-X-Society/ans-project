import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import RatingBadge from '../RatingBadge.svelte';
import type { FactCheckRatingValue } from '$lib/api/types';

describe('RatingBadge', () => {
	beforeEach(() => {
		locale.set('en');
	});

	describe('rendering', () => {
		it('should render the badge with correct role and accessible name', () => {
			render(RatingBadge, { props: { rating: 'true' } });

			const badge = screen.getByRole('status');
			expect(badge).toBeInTheDocument();
			expect(badge).toHaveAccessibleName(/true/i);
		});

		it('should display the rating icon', () => {
			render(RatingBadge, { props: { rating: 'true' } });

			// TRUE rating should show checkmark icon
			expect(screen.getByText('✓')).toBeInTheDocument();
		});

		it('should display the rating label text', () => {
			render(RatingBadge, { props: { rating: 'true' } });

			expect(screen.getByText(/true/i)).toBeInTheDocument();
		});
	});

	describe('color coding per rating type', () => {
		const ratingColors: Array<{
			rating: FactCheckRatingValue;
			expectedBgClass: string;
			icon: string;
		}> = [
			{ rating: 'true', expectedBgClass: 'bg-emerald-100', icon: '✓' },
			{ rating: 'partly_false', expectedBgClass: 'bg-orange-100', icon: '⚠' },
			{ rating: 'false', expectedBgClass: 'bg-red-100', icon: '✗' },
			{ rating: 'missing_context', expectedBgClass: 'bg-yellow-100', icon: 'ℹ' },
			{ rating: 'altered', expectedBgClass: 'bg-purple-100', icon: '🖼' },
			{ rating: 'satire', expectedBgClass: 'bg-blue-100', icon: '😄' },
			{ rating: 'unverifiable', expectedBgClass: 'bg-gray-100', icon: '?' }
		];

		ratingColors.forEach(({ rating, expectedBgClass, icon }) => {
			it(`should render ${rating} rating with correct background color class`, () => {
				render(RatingBadge, { props: { rating } });

				const badge = screen.getByRole('status');
				expect(badge.className).toContain(expectedBgClass);
			});

			it(`should render ${rating} rating with icon ${icon}`, () => {
				render(RatingBadge, { props: { rating } });

				expect(screen.getByText(icon)).toBeInTheDocument();
			});
		});
	});

	describe('size variants', () => {
		it('should render small size by default', () => {
			render(RatingBadge, { props: { rating: 'true' } });

			const badge = screen.getByRole('status');
			expect(badge.className).toContain('text-xs');
		});

		it('should render medium size when specified', () => {
			render(RatingBadge, { props: { rating: 'true', size: 'md' } });

			const badge = screen.getByRole('status');
			expect(badge.className).toContain('text-sm');
		});

		it('should render large size when specified', () => {
			render(RatingBadge, { props: { rating: 'true', size: 'lg' } });

			const badge = screen.getByRole('status');
			expect(badge.className).toContain('text-base');
		});
	});

	describe('multilingual support', () => {
		it('should display English label for true rating', () => {
			locale.set('en');
			render(RatingBadge, { props: { rating: 'true' } });

			expect(screen.getByText(/true/i)).toBeInTheDocument();
		});

		it('should display English label for false rating', () => {
			locale.set('en');
			render(RatingBadge, { props: { rating: 'false' } });

			expect(screen.getByText(/false/i)).toBeInTheDocument();
		});

		it('should display English label for partly_false rating', () => {
			locale.set('en');
			render(RatingBadge, { props: { rating: 'partly_false' } });

			expect(screen.getByText(/partly false/i)).toBeInTheDocument();
		});

		it('should display English label for missing_context rating', () => {
			locale.set('en');
			render(RatingBadge, { props: { rating: 'missing_context' } });

			expect(screen.getByText(/missing context/i)).toBeInTheDocument();
		});
	});

	describe('accessibility', () => {
		it('should have role="status" for screen readers', () => {
			render(RatingBadge, { props: { rating: 'true' } });

			expect(screen.getByRole('status')).toBeInTheDocument();
		});

		it('should have aria-label describing the rating', () => {
			render(RatingBadge, { props: { rating: 'false' } });

			const badge = screen.getByRole('status');
			expect(badge).toHaveAttribute('aria-label');
			// Check case-insensitive since the translated name is capitalized
			expect(badge.getAttribute('aria-label')?.toLowerCase()).toContain('false');
		});

		it('should be focusable when interactive prop is true', () => {
			render(RatingBadge, { props: { rating: 'true', interactive: true } });

			const badge = screen.getByRole('status');
			expect(badge).toHaveAttribute('tabindex', '0');
		});

		it('should not be focusable by default', () => {
			render(RatingBadge, { props: { rating: 'true' } });

			const badge = screen.getByRole('status');
			expect(badge).not.toHaveAttribute('tabindex');
		});
	});

	describe('compact mode', () => {
		it('should show only icon when compact is true', () => {
			render(RatingBadge, { props: { rating: 'true', compact: true } });

			// Should have the icon
			expect(screen.getByText('✓')).toBeInTheDocument();

			// Should still have aria-label for accessibility
			const badge = screen.getByRole('status');
			expect(badge).toHaveAttribute('aria-label');
		});
	});
});
