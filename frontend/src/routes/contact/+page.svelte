<script lang="ts">
	import { t } from '$lib/i18n';
</script>

<svelte:head>
	<title>{$t('contact.title')} - ANS</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-4xl mx-auto">
		<h1 class="text-4xl font-bold text-gray-900 mb-6">
			{$t('contact.title')}
		</h1>

		<div class="prose prose-lg max-w-none">
			<p class="text-xl text-gray-600 mb-8">
				{$t('contact.description')}
			</p>

			<div class="bg-white rounded-lg shadow-md p-8 mb-8">
				<h2 class="text-2xl font-semibold mb-4">{$t('contact.general.title')}</h2>
				<div class="space-y-4">
					<div>
						<h3 class="font-medium text-gray-900">{$t('contact.general.email')}</h3>
						<p class="text-gray-600">
							<a href="mailto:info@ans-factcheck.org" class="text-primary-600 hover:text-primary-700">
								info@ans-factcheck.org
							</a>
						</p>
					</div>
				</div>
			</div>

			<div class="bg-white rounded-lg shadow-md p-8 mb-8">
				<h2 class="text-2xl font-semibold mb-4">{$t('contact.corrections.title')}</h2>
				<p class="text-gray-600 mb-4">
					{$t('contact.corrections.description')}
				</p>
				<a
					href="/corrections-log"
					class="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
				>
					{$t('contact.corrections.button')}
				</a>
			</div>

			<div class="bg-white rounded-lg shadow-md p-8 mb-8">
				<h2 class="text-2xl font-semibold mb-4">{$t('contact.privacy.title')}</h2>
				<p class="text-gray-600 mb-4">
					{$t('contact.privacy.description')}
				</p>
				<a
					href="/account/delete"
					class="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
				>
					{$t('contact.privacy.button')}
				</a>
			</div>

			<div class="bg-gray-50 rounded-lg p-8">
				<h2 class="text-2xl font-semibold mb-4">{$t('contact.responseTimes.title')}</h2>
				<ul class="list-disc list-inside space-y-2 text-gray-700">
					<li>{$t('contact.responseTimes.general')}</li>
					<li>{$t('contact.responseTimes.corrections')}</li>
					<li>{$t('contact.responseTimes.privacy')}</li>
				</ul>
			</div>
		</div>
	</div>
</div>
