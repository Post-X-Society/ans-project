<script lang="ts">
	import SubmissionForm from '$lib/components/SubmissionForm.svelte';
</script>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-2xl mx-auto">
		<h1 class="text-3xl font-bold text-gray-900 mb-4">Submit a Claim for Fact-Checking</h1>

		<p class="text-gray-600 mb-8">
			Submit any claim, statement, or piece of information you'd like us to fact-check. Our AI
			will analyze it and provide you with verified results.
		</p>

		<SubmissionForm />
	</div>
</div>
