/**
 * Analytics API client functions for EFCSN Compliance Dashboard.
 *
 * Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
 * EPIC #52: Analytics & Compliance Dashboard
 */

import apiClient from './client';
import type {
	AnalyticsDashboardResponse,
	EFCSNComplianceResponse,
	MonthlyFactCheckCountResponse,
	RatingDistributionResponse,
	SourceQualityMetrics,
	CorrectionRateMetrics
} from './types';

/**
 * Get complete analytics dashboard with all metrics.
 * Admin only.
 */
export async function getAnalyticsDashboard(): Promise<AnalyticsDashboardResponse> {
	const response = await apiClient.get<AnalyticsDashboardResponse>('/api/v1/analytics/dashboard');
	return response.data;
}

/**
 * Get EFCSN compliance checklist with real-time status.
 * Admin only.
 */
export async function getEFCSNCompliance(): Promise<EFCSNComplianceResponse> {
	const response = await apiClient.get<EFCSNComplianceResponse>('/api/v1/analytics/compliance');
	return response.data;
}

/**
 * Get monthly fact-check publication counts.
 * EFCSN requires minimum 4 fact-checks published per month.
 * Admin only.
 *
 * @param months - Number of months to include (default: 12, max: 36)
 */
export async function getMonthlyFactChecks(
	months: number = 12
): Promise<MonthlyFactCheckCountResponse> {
	const response = await apiClient.get<MonthlyFactCheckCountResponse>(
		'/api/v1/analytics/monthly-fact-checks',
		{ params: { months } }
	);
	return response.data;
}

/**
 * Get rating distribution statistics.
 * Optionally filter by date range.
 * Admin only.
 */
export async function getRatingDistribution(
	startDate?: Date,
	endDate?: Date
): Promise<RatingDistributionResponse> {
	const params: Record<string, string> = {};
	if (startDate) {
		params.start_date = startDate.toISOString();
	}
	if (endDate) {
		params.end_date = endDate.toISOString();
	}

	const response = await apiClient.get<RatingDistributionResponse>(
		'/api/v1/analytics/rating-distribution',
		{ params }
	);
	return response.data;
}

/**
 * Get source quality metrics for EFCSN compliance.
 * Admin only.
 */
export async function getSourceQuality(): Promise<SourceQualityMetrics> {
	const response = await apiClient.get<SourceQualityMetrics>('/api/v1/analytics/source-quality');
	return response.data;
}

/**
 * Get correction rate metrics for quality tracking.
 * Admin only.
 */
export async function getCorrectionRate(): Promise<CorrectionRateMetrics> {
	const response = await apiClient.get<CorrectionRateMetrics>('/api/v1/analytics/correction-rate');
	return response.data;
}
