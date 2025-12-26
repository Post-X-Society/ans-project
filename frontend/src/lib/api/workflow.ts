import { apiClient } from './client';
import type {
	WorkflowHistoryResponse,
	WorkflowCurrentStateResponse,
	WorkflowTransitionRequest,
	WorkflowHistoryItem
} from './types';

/**
 * Fetch workflow history for a submission
 */
export async function getWorkflowHistory(submissionId: string): Promise<WorkflowHistoryResponse> {
	const response = await apiClient.get<WorkflowHistoryResponse>(
		`/api/v1/workflow/${submissionId}/history`
	);
	return response.data;
}

/**
 * Get current workflow state and valid transitions
 */
export async function getWorkflowCurrentState(
	submissionId: string
): Promise<WorkflowCurrentStateResponse> {
	const response = await apiClient.get<WorkflowCurrentStateResponse>(
		`/api/v1/workflow/${submissionId}/current`
	);
	return response.data;
}

/**
 * Perform a workflow state transition
 */
export async function transitionWorkflowState(
	submissionId: string,
	request: WorkflowTransitionRequest
): Promise<WorkflowHistoryItem> {
	const response = await apiClient.post<WorkflowHistoryItem>(
		`/api/v1/workflow/${submissionId}/transition`,
		request
	);
	return response.data;
}
