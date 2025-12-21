<script lang="ts">
	import { t } from '$lib/i18n';
</script>

<div class="flex-1 flex items-center justify-center py-12">
	<div class="text-center">
		<h1 class="text-4xl font-bold text-primary-600 mb-4">{$t('home.title')}</h1>
		<p class="text-gray-600 mb-8">{$t('home.description')}</p>
		<a
			href="/submit"
			class="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition"
		>
			{$t('home.submitClaim')}
		</a>
	</div>
</div>
