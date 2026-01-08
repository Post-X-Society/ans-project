/**
 * Tests for TimeToPublicationCard component.
 *
 * Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import TimeToPublicationCard from '../TimeToPublicationCard.svelte';
import type { TimeToPublicationMetrics } from '$lib/api/types';

// Mock svelte-i18n
vi.mock('svelte-i18n', () => ({
	t: {
		subscribe: (fn: (value: (key: string) => string) => void) => {
			fn((key: string) => key);
			return () => {};
		}
	}
}));

describe('TimeToPublicationCard', () => {
	const mockMetrics: TimeToPublicationMetrics = {
		average_hours: 48.5,
		median_hours: 36.0,
		min_hours: 12.0,
		max_hours: 120.0,
		total_published: 42
	};

	it('should render the card title', () => {
		render(TimeToPublicationCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('compliance.timeToPublication.title')).toBeInTheDocument();
	});

	it('should display average hours', () => {
		render(TimeToPublicationCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('48.5')).toBeInTheDocument();
	});

	it('should display median hours', () => {
		render(TimeToPublicationCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('36')).toBeInTheDocument();
	});

	it('should display minimum hours', () => {
		render(TimeToPublicationCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('12')).toBeInTheDocument();
	});

	it('should display maximum hours', () => {
		render(TimeToPublicationCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('120')).toBeInTheDocument();
	});

	it('should display total published count', () => {
		render(TimeToPublicationCard, { props: { metrics: mockMetrics } });
		expect(screen.getByText('42')).toBeInTheDocument();
	});

	it('should show loading state when loading prop is true', () => {
		render(TimeToPublicationCard, { props: { metrics: null, loading: true } });
		expect(screen.getByText('common.loading')).toBeInTheDocument();
	});

	it('should show error state when error prop is provided', () => {
		render(TimeToPublicationCard, {
			props: { metrics: null, error: 'Failed to load metrics' }
		});
		expect(screen.getByText('Failed to load metrics')).toBeInTheDocument();
	});

	it('should have max-hours test id', () => {
		render(TimeToPublicationCard, { props: { metrics: mockMetrics } });
		const maxElement = screen.getByTestId('max-hours');
		expect(maxElement).toBeInTheDocument();
	});

	it('should have proper semantic structure', () => {
		render(TimeToPublicationCard, { props: { metrics: mockMetrics } });
		const card = screen.getByRole('region');
		expect(card).toBeInTheDocument();
	});
});
