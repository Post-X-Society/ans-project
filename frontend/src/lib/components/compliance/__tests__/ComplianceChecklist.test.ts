/**
 * Tests for ComplianceChecklist component.
 *
 * Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import ComplianceChecklist from '../ComplianceChecklist.svelte';
import type { EFCSNComplianceResponse } from '$lib/api/types';

// Mock svelte-i18n
vi.mock('svelte-i18n', () => ({
	t: {
		subscribe: (fn: (value: (key: string) => string) => void) => {
			fn((key: string) => key);
			return () => {};
		}
	}
}));

describe('ComplianceChecklist', () => {
	const mockComplianceData: EFCSNComplianceResponse = {
		overall_status: 'compliant',
		checklist: [
			{
				requirement: 'Monthly Fact-Check Minimum',
				status: 'compliant',
				details: '5 fact-checks published this month',
				value: '5',
				threshold: '4'
			},
			{
				requirement: 'Source Documentation',
				status: 'compliant',
				details: 'Average 3 sources per fact-check',
				value: '3.0',
				threshold: '2'
			},
			{
				requirement: 'Corrections Policy',
				status: 'warning',
				details: 'Policy review due in 10 days'
			}
		],
		last_checked: '2026-01-08T12:00:00Z',
		compliance_score: 85.5
	};

	it('should render the compliance score', () => {
		render(ComplianceChecklist, { props: { compliance: mockComplianceData } });
		expect(screen.getByText('85.5%')).toBeInTheDocument();
	});

	it('should render all checklist items', () => {
		render(ComplianceChecklist, { props: { compliance: mockComplianceData } });
		expect(screen.getByText('Monthly Fact-Check Minimum')).toBeInTheDocument();
		expect(screen.getByText('Source Documentation')).toBeInTheDocument();
		expect(screen.getByText('Corrections Policy')).toBeInTheDocument();
	});

	it('should show compliant status indicators', () => {
		render(ComplianceChecklist, { props: { compliance: mockComplianceData } });
		const compliantItems = screen.getAllByTestId('status-compliant');
		expect(compliantItems.length).toBe(2); // 2 checklist items are compliant
	});

	it('should show warning status indicator', () => {
		render(ComplianceChecklist, { props: { compliance: mockComplianceData } });
		const warningItems = screen.getAllByTestId('status-warning');
		expect(warningItems.length).toBe(1);
	});

	it('should display checklist item details', () => {
		render(ComplianceChecklist, { props: { compliance: mockComplianceData } });
		expect(screen.getByText('5 fact-checks published this month')).toBeInTheDocument();
	});

	it('should display value and threshold when available', () => {
		render(ComplianceChecklist, { props: { compliance: mockComplianceData } });
		expect(screen.getByText('5 / 4')).toBeInTheDocument();
	});

	it('should show loading state when loading prop is true', () => {
		render(ComplianceChecklist, { props: { compliance: null, loading: true } });
		expect(screen.getByText('common.loading')).toBeInTheDocument();
	});

	it('should show error state when error prop is provided', () => {
		render(ComplianceChecklist, {
			props: { compliance: null, error: 'Failed to load compliance data' }
		});
		expect(screen.getByText('Failed to load compliance data')).toBeInTheDocument();
	});

	it('should have proper accessibility attributes', () => {
		render(ComplianceChecklist, { props: { compliance: mockComplianceData } });
		const checklist = screen.getByRole('list');
		expect(checklist).toBeInTheDocument();
	});
});
