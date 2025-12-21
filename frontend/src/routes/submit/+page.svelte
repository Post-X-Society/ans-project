<script lang="ts">
	import SubmissionForm from '$lib/components/SubmissionForm.svelte';
	import { t } from '$lib/i18n';
</script>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-2xl mx-auto">
		<h1 class="text-3xl font-bold text-gray-900 mb-4">
			{$t('submissions.submitTitle')}
		</h1>

		<p class="text-gray-600 mb-8">
			{$t('submissions.submitDescription')}
		</p>

		<SubmissionForm />
	</div>
</div>
