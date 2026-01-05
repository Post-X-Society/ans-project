/**
 * Corrections Log RSS Feed Endpoint
 * Issue #81: Frontend Public Corrections Log Page (TDD)
 *
 * Generates an RSS 2.0 feed of substantial corrections.
 * This allows users to subscribe and receive updates when corrections are published.
 */

import type { RequestHandler } from './$types';
import { getPublicCorrectionsLog } from '$lib/api/corrections';

// Site configuration
const SITE_URL = 'https://ans.amsterdam';
const SITE_TITLE = 'Ans Fact-Checking Corrections Log';
const SITE_DESCRIPTION =
	'RSS feed of substantial corrections made to fact-checks on Ans Fact-Checking platform. Per EFCSN transparency requirements.';

/**
 * Escape special XML characters
 */
function escapeXml(text: string): string {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&apos;');
}

/**
 * Format date as RFC 822 for RSS
 */
function formatRfc822Date(dateString: string): string {
	const date = new Date(dateString);
	return date.toUTCString();
}

/**
 * Get correction type display name
 */
function getCorrectionTypeLabel(type: string): string {
	switch (type) {
		case 'substantial':
			return 'Substantial Correction';
		case 'update':
			return 'Update';
		case 'minor':
			return 'Minor Correction';
		default:
			return 'Correction';
	}
}

export const GET: RequestHandler = async ({ url }) => {
	try {
		// Fetch recent corrections (limit to 50 for RSS feed)
		const response = await getPublicCorrectionsLog({ limit: 50, offset: 0 });
		const corrections = response.corrections;

		// Build RSS XML
		const rssItems = corrections
			.map((correction) => {
				const pubDate = formatRfc822Date(correction.reviewed_at || correction.created_at);
				const title = escapeXml(
					`${getCorrectionTypeLabel(correction.correction_type)}: Fact-Check Updated`
				);
				const link = `${SITE_URL}/submissions/${correction.fact_check_id}`;
				const description = escapeXml(
					correction.resolution_notes || correction.request_details || 'Correction applied.'
				);
				const guid = `${SITE_URL}/corrections/${correction.id}`;

				return `
    <item>
      <title>${title}</title>
      <link>${link}</link>
      <description>${description}</description>
      <pubDate>${pubDate}</pubDate>
      <guid isPermaLink="false">${guid}</guid>
      <category>${escapeXml(getCorrectionTypeLabel(correction.correction_type))}</category>
    </item>`;
			})
			.join('\n');

		const rssXml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escapeXml(SITE_TITLE)}</title>
    <link>${SITE_URL}/corrections-log</link>
    <description>${escapeXml(SITE_DESCRIPTION)}</description>
    <language>en</language>
    <lastBuildDate>${formatRfc822Date(new Date().toISOString())}</lastBuildDate>
    <atom:link href="${url.href}" rel="self" type="application/rss+xml"/>
    <ttl>60</ttl>
    <image>
      <url>${SITE_URL}/favicon.png</url>
      <title>${escapeXml(SITE_TITLE)}</title>
      <link>${SITE_URL}/corrections-log</link>
    </image>
${rssItems}
  </channel>
</rss>`;

		return new Response(rssXml, {
			headers: {
				'Content-Type': 'application/rss+xml; charset=utf-8',
				'Cache-Control': 'max-age=300, s-maxage=600' // Cache for 5-10 minutes
			}
		});
	} catch (error) {
		console.error('Error generating RSS feed:', error);

		// Return an error RSS with a message
		const errorXml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>${escapeXml(SITE_TITLE)}</title>
    <link>${SITE_URL}/corrections-log</link>
    <description>Error loading corrections feed. Please try again later.</description>
    <lastBuildDate>${formatRfc822Date(new Date().toISOString())}</lastBuildDate>
  </channel>
</rss>`;

		return new Response(errorXml, {
			status: 500,
			headers: {
				'Content-Type': 'application/rss+xml; charset=utf-8'
			}
		});
	}
};
