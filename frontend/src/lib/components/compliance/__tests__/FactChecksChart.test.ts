/**
 * Tests for FactChecksChart component.
 *
 * Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import FactChecksChart from '../FactChecksChart.svelte';
import type { MonthlyFactCheckCountResponse } from '$lib/api/types';

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

describe('FactChecksChart', () => {
	const mockMonthlyData: MonthlyFactCheckCountResponse = {
		months: [
			{ year: 2025, month: 10, count: 5, meets_efcsn_minimum: true },
			{ year: 2025, month: 11, count: 6, meets_efcsn_minimum: true },
			{ year: 2025, month: 12, count: 3, meets_efcsn_minimum: false },
			{ year: 2026, month: 1, count: 7, meets_efcsn_minimum: true }
		],
		total_count: 21,
		average_per_month: 5.25
	};

	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should render the chart title', () => {
		render(FactChecksChart, { props: { data: mockMonthlyData } });
		expect(screen.getByText('compliance.factChecksChart.title')).toBeInTheDocument();
	});

	it('should display total fact-check count', () => {
		render(FactChecksChart, { props: { data: mockMonthlyData } });
		expect(screen.getByText('21')).toBeInTheDocument();
	});

	it('should display average per month', () => {
		render(FactChecksChart, { props: { data: mockMonthlyData } });
		expect(screen.getByText('5.25')).toBeInTheDocument();
	});

	it('should render a canvas element for the chart', () => {
		render(FactChecksChart, { props: { data: mockMonthlyData } });
		const canvas = document.querySelector('canvas');
		expect(canvas).toBeInTheDocument();
	});

	it('should show EFCSN minimum indicator', () => {
		render(FactChecksChart, { props: { data: mockMonthlyData } });
		expect(screen.getByText('compliance.factChecksChart.efcsnMinimum')).toBeInTheDocument();
	});

	it('should show loading state when loading prop is true', () => {
		render(FactChecksChart, { props: { data: null, loading: true } });
		expect(screen.getByText('common.loading')).toBeInTheDocument();
	});

	it('should show error state when error prop is provided', () => {
		render(FactChecksChart, {
			props: { data: null, error: 'Failed to load chart data' }
		});
		expect(screen.getByText('Failed to load chart data')).toBeInTheDocument();
	});

	it('should highlight months below EFCSN minimum', () => {
		render(FactChecksChart, { props: { data: mockMonthlyData } });
		const belowMinimumIndicator = screen.getByTestId('months-below-minimum');
		expect(belowMinimumIndicator).toHaveTextContent('1');
	});

	it('should have proper aria-label for accessibility', () => {
		render(FactChecksChart, { props: { data: mockMonthlyData } });
		const chartContainer = screen.getByRole('img');
		expect(chartContainer).toBeInTheDocument();
	});
});
