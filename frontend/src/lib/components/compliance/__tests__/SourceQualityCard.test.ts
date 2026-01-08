/**
 * Tests for SourceQualityCard component.
 *
 * Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import SourceQualityCard from '../SourceQualityCard.svelte';
import type { SourceQualityMetrics } from '$lib/api/types';

// Mock svelte-i18n
vi.mock('svelte-i18n', () => ({
	t: {
		subscribe: (fn: (value: (key: string) => string) => void) => {
			fn((key: string) => key);
			return () => {};
		}
	}
}));

describe('SourceQualityCard', () => {
	const mockMetrics: SourceQualityMetrics = {
		average_sources_per_fact_check: 3.5,
		average_credibility_score: 4.2,
		total_sources: 175,
		sources_by_type: {
			official: 50,
			news: 60,
			research: 40,
			social_media: 15,
			other: 10
		},
		sources_by_relevance: {
			supports: 100,
			contradicts: 35,
			contextualizes: 40
		},
		fact_checks_meeting_minimum: 45,
		fact_checks_below_minimum: 5
	};

	it('should render the card title', () => {
		render(SourceQualityCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('compliance.sourceQuality.title')).toBeInTheDocument();
	});

	it('should display average sources per fact-check', () => {
		render(SourceQualityCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('3.5')).toBeInTheDocument();
	});

	it('should display average credibility score', () => {
		render(SourceQualityCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('4.2')).toBeInTheDocument();
	});

	it('should display total sources count', () => {
		render(SourceQualityCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('175')).toBeInTheDocument();
	});

	it('should display fact-checks meeting minimum', () => {
		render(SourceQualityCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('45')).toBeInTheDocument();
	});

	it('should display fact-checks below minimum', () => {
		render(SourceQualityCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('5')).toBeInTheDocument();
	});

	it('should show EFCSN compliance indicator as compliant when above minimum', () => {
		render(SourceQualityCard, { props: { metrics: mockMetrics } });
		const complianceIndicator = screen.getByTestId('source-compliance-indicator');
		expect(complianceIndicator).toHaveClass('text-green-600');
	});

	it('should show warning when below EFCSN minimum', () => {
		const lowMetrics: SourceQualityMetrics = {
			...mockMetrics,
			average_sources_per_fact_check: 1.5
		};

		render(SourceQualityCard, { props: { metrics: lowMetrics } });
		const complianceIndicator = screen.getByTestId('source-compliance-indicator');
		expect(complianceIndicator).toHaveClass('text-red-600');
	});

	it('should show loading state when loading prop is true', () => {
		render(SourceQualityCard, { props: { metrics: null, loading: true } });
		expect(screen.getByText('common.loading')).toBeInTheDocument();
	});

	it('should show error state when error prop is provided', () => {
		render(SourceQualityCard, {
			props: { metrics: null, error: 'Failed to load source metrics' }
		});
		expect(screen.getByText('Failed to load source metrics')).toBeInTheDocument();
	});

	it('should have proper semantic structure', () => {
		render(SourceQualityCard, { props: { metrics: mockMetrics } });
		const card = screen.getByRole('region');
		expect(card).toBeInTheDocument();
	});
});
