/**
 * Tests for CorrectionRateCard component.
 *
 * Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import CorrectionRateCard from '../CorrectionRateCard.svelte';
import type { CorrectionRateMetrics } from '$lib/api/types';

// Mock svelte-i18n
vi.mock('svelte-i18n', () => ({
	t: {
		subscribe: (fn: (value: (key: string) => string) => void) => {
			fn((key: string) => key);
			return () => {};
		}
	}
}));

describe('CorrectionRateCard', () => {
	const mockMetrics: CorrectionRateMetrics = {
		total_fact_checks: 50,
		total_corrections: 12,
		corrections_accepted: 8,
		corrections_rejected: 2,
		corrections_pending: 2,
		correction_rate: 0.24,
		corrections_by_type: {
			minor: 5,
			update: 4,
			substantial: 3
		}
	};

	it('should render the card title', () => {
		render(CorrectionRateCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('compliance.correctionRate.title')).toBeInTheDocument();
	});

	it('should display total fact-checks', () => {
		render(CorrectionRateCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('50')).toBeInTheDocument();
	});

	it('should display total corrections', () => {
		render(CorrectionRateCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('12')).toBeInTheDocument();
	});

	it('should display corrections breakdown', () => {
		render(CorrectionRateCard, { props: { metrics: mockMetrics } });

		const acceptedElement = screen.getByTestId('corrections-accepted');
		expect(acceptedElement).toHaveTextContent('8');

		const rejectedElement = screen.getByTestId('corrections-rejected');
		expect(rejectedElement).toHaveTextContent('2');

		const pendingElement = screen.getByTestId('corrections-pending');
		expect(pendingElement).toHaveTextContent('2');
	});

	it('should display correction rate as percentage', () => {
		render(CorrectionRateCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('24%')).toBeInTheDocument();
	});

	it('should show loading state when loading prop is true', () => {
		render(CorrectionRateCard, { props: { metrics: null, loading: true } });
		expect(screen.getByText('common.loading')).toBeInTheDocument();
	});

	it('should show error state when error prop is provided', () => {
		render(CorrectionRateCard, {
			props: { metrics: null, error: 'Failed to load correction metrics' }
		});
		expect(screen.getByText('Failed to load correction metrics')).toBeInTheDocument();
	});

	it('should handle zero corrections gracefully', () => {
		const zeroMetrics: CorrectionRateMetrics = {
			total_fact_checks: 30,
			total_corrections: 0,
			corrections_accepted: 0,
			corrections_rejected: 0,
			corrections_pending: 0,
			correction_rate: 0,
			corrections_by_type: {}
		};

		render(CorrectionRateCard, { props: { metrics: zeroMetrics } });
		expect(screen.getByText('0%')).toBeInTheDocument();
	});

	it('should have proper semantic structure', () => {
		render(CorrectionRateCard, { props: { metrics: mockMetrics } });
		const card = screen.getByRole('region');
		expect(card).toBeInTheDocument();
	});

	it('should show health indicator', () => {
		render(CorrectionRateCard, { props: { metrics: mockMetrics } });
		const healthIndicator = screen.getByTestId('correction-rate-health');
		expect(healthIndicator).toBeInTheDocument();
	});
});
