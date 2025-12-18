<script lang="ts">
	import SubmissionForm from '$lib/components/SubmissionForm.svelte';
</script>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-2xl mx-auto">
		<h1 class="text-3xl font-bold text-gray-900 mb-4">
			Submit Snapchat Spotlight for Fact-Checking
		</h1>

		<p class="text-gray-600 mb-8">
			Submit a Snapchat Spotlight link for fact-checking. We'll automatically fetch the video,
			metadata, and creator information to verify the content.
		</p>

		<SubmissionForm />
	</div>
</div>
