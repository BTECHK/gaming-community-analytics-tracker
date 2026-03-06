<script lang="ts">
	import type { Platform } from '$lib/types';

	interface Props {
		platform: Platform;
		size?: 'sm' | 'md' | 'lg';
	}

	let { platform, size = 'md' }: Props = $props();

	const platformNames: Record<Platform, string> = {
		youtube: 'YouTube',
		official-news: 'OfficialNews',
		tier-site: 'TierSite',
		guide-site: 'GuideSite',
		google_trends: 'Google Trends',
		news-source-a: 'NewsSourceA',
		news-source-b: 'News Source B',
		reddit: 'Reddit'
	};
</script>

<span class="source-badge {size}" data-platform={platform}>
	{platformNames[platform] || platform}
</span>

<style>
	.source-badge {
		display: inline-flex;
		align-items: center;
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-sm);
		text-transform: capitalize;
	}

	.source-badge.sm {
		padding: 2px 6px;
		font-size: var(--font-size-xs);
	}

	.source-badge.md {
		padding: 4px 8px;
		font-size: var(--font-size-sm);
	}

	.source-badge.lg {
		padding: 6px 12px;
		font-size: var(--font-size-base);
	}

	.source-badge[data-platform='youtube'] {
		background: rgba(255, 0, 0, 0.15);
		color: var(--color-youtube);
	}

	.source-badge[data-platform='official-news'] {
		background: rgba(211, 41, 54, 0.15);
		color: var(--color-official-news);
	}

	.source-badge[data-platform='tier-site'] {
		background: rgba(83, 131, 232, 0.15);
		color: var(--color-tier-site);
	}

	.source-badge[data-platform='guide-site'] {
		background: rgba(255, 107, 53, 0.15);
		color: var(--color-guide-site);
	}

	.source-badge[data-platform='google_trends'] {
		background: rgba(66, 133, 244, 0.15);
		color: var(--color-google-trends);
	}

	.source-badge[data-platform='news-source-a'] {
		background: rgba(230, 57, 70, 0.15);
		color: var(--color-news-source-a);
	}

	.source-badge[data-platform='news-source-b'] {
		background: rgba(0, 180, 216, 0.15);
		color: var(--color-news-source-b);
	}

	.source-badge[data-platform='reddit'] {
		background: rgba(255, 69, 0, 0.15);
		color: var(--color-reddit);
	}
</style>
