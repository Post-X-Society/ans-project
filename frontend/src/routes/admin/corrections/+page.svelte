<!--
  Admin Corrections Page
  Issue #162: Frontend Integration of Correction Components

  This page integrates the CorrectionReviewDashboard component for admin
  users to review, accept/reject, and apply corrections to fact-checks.
-->
<script lang="ts">
	import CorrectionReviewDashboard from '$lib/components/CorrectionReviewDashboard.svelte';
	import { t } from '$lib/i18n';
</script>

<svelte:head>
	<title>{$t('corrections.adminTitle')} - ANS</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-7xl mx-auto">
		<CorrectionReviewDashboard />
	</div>
</div>
