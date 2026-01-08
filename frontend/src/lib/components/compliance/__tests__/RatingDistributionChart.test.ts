/**
 * Tests for RatingDistributionChart component.
 *
 * Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import RatingDistributionChart from '../RatingDistributionChart.svelte';
import type { RatingDistributionResponse } from '$lib/api/types';

// Mock Chart.js dynamic import
vi.mock('chart.js', () => ({
	Chart: class MockChart {
		static register = vi.fn();
		destroy = vi.fn();
		update = vi.fn();
		constructor() {}
	},
	registerables: []
}));

// Mock svelte-i18n
vi.mock('svelte-i18n', () => ({
	t: {
		subscribe: (fn: (value: (key: string) => string) => void) => {
			fn((key: string) => key);
			return () => {};
		}
	}
}));

describe('RatingDistributionChart', () => {
	const mockDistribution: RatingDistributionResponse = {
		ratings: [
			{ rating: 'true', count: 15, percentage: 30.0 },
			{ rating: 'false', count: 10, percentage: 20.0 },
			{ rating: 'partly_false', count: 12, percentage: 24.0 },
			{ rating: 'missing_context', count: 8, percentage: 16.0 },
			{ rating: 'unverifiable', count: 5, percentage: 10.0 }
		],
		total_count: 50,
		period_start: '2025-01-01T00:00:00Z',
		period_end: '2026-01-08T00:00:00Z'
	};

	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should render the chart title', () => {
		render(RatingDistributionChart, { props: { data: mockDistribution } });
		expect(screen.getByText('compliance.ratingDistribution.title')).toBeInTheDocument();
	});

	it('should display total fact-check count', () => {
		render(RatingDistributionChart, { props: { data: mockDistribution } });
		expect(screen.getByText('50')).toBeInTheDocument();
	});

	it('should render a canvas element for the chart', () => {
		render(RatingDistributionChart, { props: { data: mockDistribution } });
		const canvas = document.querySelector('canvas');
		expect(canvas).toBeInTheDocument();
	});

	it('should display percentages for each rating', () => {
		render(RatingDistributionChart, { props: { data: mockDistribution } });
		expect(screen.getByText('30%')).toBeInTheDocument();
		expect(screen.getByText('20%')).toBeInTheDocument();
		expect(screen.getByText('24%')).toBeInTheDocument();
	});

	it('should show loading state when loading prop is true', () => {
		render(RatingDistributionChart, { props: { data: null, loading: true } });
		expect(screen.getByText('common.loading')).toBeInTheDocument();
	});

	it('should show error state when error prop is provided', () => {
		render(RatingDistributionChart, {
			props: { data: null, error: 'Failed to load rating distribution' }
		});
		expect(screen.getByText('Failed to load rating distribution')).toBeInTheDocument();
	});

	it('should have proper aria-label for accessibility', () => {
		render(RatingDistributionChart, { props: { data: mockDistribution } });
		const chartContainer = screen.getByRole('img');
		expect(chartContainer).toBeInTheDocument();
	});

	it('should show empty state when no ratings data', () => {
		const emptyData: RatingDistributionResponse = {
			ratings: [],
			total_count: 0
		};

		render(RatingDistributionChart, { props: { data: emptyData } });
		expect(screen.getByText('common.noData')).toBeInTheDocument();
	});
});
