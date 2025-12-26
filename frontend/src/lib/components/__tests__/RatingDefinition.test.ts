import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import RatingDefinition from '../RatingDefinition.svelte';
import type { FactCheckRatingValue } from '$lib/api/types';

describe('RatingDefinition', () => {
	beforeEach(() => {
		locale.set('en');
	});

	describe('rendering', () => {
		it('should render the rating badge', () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const badge = screen.getByRole('status');
			expect(badge).toBeInTheDocument();
		});

		it('should not show definition by default', () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			// Definition should not be visible initially
			expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
		});

		it('should render with custom class', () => {
			const { container } = render(RatingDefinition, {
				props: { rating: 'true', class: 'custom-class' }
			});

			expect(container.firstChild).toHaveClass('custom-class');
		});
	});

	describe('hover interaction', () => {
		it('should show definition on mouse enter', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.mouseEnter(trigger);

			const tooltip = screen.getByRole('tooltip');
			expect(tooltip).toBeInTheDocument();
		});

		it('should hide definition on mouse leave', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.mouseEnter(trigger);

			expect(screen.getByRole('tooltip')).toBeInTheDocument();

			await fireEvent.mouseLeave(trigger);

			expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
		});

		it('should display rating name in definition tooltip', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.mouseEnter(trigger);

			const tooltip = screen.getByRole('tooltip');
			// The tooltip should contain the rating name
			expect(tooltip.textContent).toContain('True');
		});

		it('should display rating description in definition', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.mouseEnter(trigger);

			// Check for part of the description
			expect(screen.getByText(/completely accurate/i)).toBeInTheDocument();
		});
	});

	describe('keyboard accessibility', () => {
		it('should be focusable', () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			expect(trigger).toHaveAttribute('tabindex', '0');
		});

		it('should show definition on focus', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.focus(trigger);

			expect(screen.getByRole('tooltip')).toBeInTheDocument();
		});

		it('should hide definition on blur', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.focus(trigger);

			expect(screen.getByRole('tooltip')).toBeInTheDocument();

			await fireEvent.blur(trigger);

			expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
		});

		it('should toggle definition on Enter key', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.keyDown(trigger, { key: 'Enter' });

			expect(screen.getByRole('tooltip')).toBeInTheDocument();

			await fireEvent.keyDown(trigger, { key: 'Enter' });

			expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
		});

		it('should close definition on Escape key', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.focus(trigger);

			expect(screen.getByRole('tooltip')).toBeInTheDocument();

			await fireEvent.keyDown(trigger, { key: 'Escape' });

			expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
		});
	});

	describe('rating definitions', () => {
		const ratings: FactCheckRatingValue[] = [
			'true',
			'partly_false',
			'false',
			'missing_context',
			'altered',
			'satire',
			'unverifiable'
		];

		ratings.forEach((rating) => {
			it(`should show definition for ${rating} rating`, async () => {
				render(RatingDefinition, { props: { rating } });

				const trigger = screen.getByRole('status');
				await fireEvent.mouseEnter(trigger);

				const tooltip = screen.getByRole('tooltip');
				expect(tooltip).toBeInTheDocument();
				// Should contain some text content
				expect(tooltip.textContent?.length).toBeGreaterThan(0);
			});
		});
	});

	describe('styling and positioning', () => {
		it('should have proper tooltip styling', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.mouseEnter(trigger);

			const tooltip = screen.getByRole('tooltip');
			expect(tooltip.className).toContain('absolute');
		});

		it('should position tooltip below badge by default', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.mouseEnter(trigger);

			const tooltip = screen.getByRole('tooltip');
			expect(tooltip.className).toContain('top-full');
		});

		it('should position tooltip above when position is top', async () => {
			render(RatingDefinition, { props: { rating: 'true', position: 'top' } });

			const trigger = screen.getByRole('status');
			await fireEvent.mouseEnter(trigger);

			const tooltip = screen.getByRole('tooltip');
			expect(tooltip.className).toContain('bottom-full');
		});
	});

	describe('accessibility attributes', () => {
		it('should have aria-describedby linking to tooltip', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			await fireEvent.mouseEnter(trigger);

			const tooltip = screen.getByRole('tooltip');
			const tooltipId = tooltip.getAttribute('id');

			expect(trigger).toHaveAttribute('aria-describedby', tooltipId);
		});

		it('should have aria-expanded attribute', () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			expect(trigger).toHaveAttribute('aria-expanded', 'false');
		});

		it('should update aria-expanded when tooltip is shown', async () => {
			render(RatingDefinition, { props: { rating: 'true' } });

			const trigger = screen.getByRole('status');
			expect(trigger).toHaveAttribute('aria-expanded', 'false');

			await fireEvent.mouseEnter(trigger);

			expect(trigger).toHaveAttribute('aria-expanded', 'true');
		});
	});

	describe('compact mode', () => {
		it('should support compact badge display', async () => {
			render(RatingDefinition, { props: { rating: 'true', compact: true } });

			// Badge should still be present
			const badge = screen.getByRole('status');
			expect(badge).toBeInTheDocument();

			// Tooltip should still work
			await fireEvent.mouseEnter(badge);
			expect(screen.getByRole('tooltip')).toBeInTheDocument();
		});
	});

	describe('size variants', () => {
		it('should pass size to badge component', () => {
			render(RatingDefinition, { props: { rating: 'true', size: 'lg' } });

			const badge = screen.getByRole('status');
			expect(badge.className).toContain('text-base');
		});
	});
});
