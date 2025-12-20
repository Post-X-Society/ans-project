<script lang="ts">
	type SubmissionStatus = 'pending' | 'processing' | 'completed';

	interface Props {
		status: SubmissionStatus;
	}

	let { status }: Props = $props();

	/**
	 * Get color-coded Tailwind classes based on submission status
	 */
	function getStatusClasses(status: SubmissionStatus): string {
		const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';

		switch (status) {
			case 'pending':
				return `${baseClasses} bg-yellow-100 text-yellow-800`;
			case 'processing':
				return `${baseClasses} bg-blue-100 text-blue-800`;
			case 'completed':
				return `${baseClasses} bg-green-100 text-green-800`;
			default:
				return `${baseClasses} bg-gray-100 text-gray-800`;
		}
	}

	/**
	 * Get display text for status
	 */
	function getStatusText(status: SubmissionStatus): string {
		return status.charAt(0).toUpperCase() + status.slice(1);
	}
</script>

<span class={getStatusClasses(status)}>
	{getStatusText(status)}
</span>
