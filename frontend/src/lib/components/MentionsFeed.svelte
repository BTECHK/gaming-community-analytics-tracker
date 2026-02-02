<script lang="ts">
	import type { Quote, Platform } from '$lib/types';

	interface Props {
		quotes: Quote[];
		maxItems?: number;
	}

	let { quotes, maxItems = 10 }: Props = $props();

	const displayQuotes = $derived(quotes.slice(0, maxItems));

	function getPlatformIcon(platform: Platform): string {
		const icons: Record<Platform, string> = {
			youtube: 'Y',
			official-news: 'R',
			tier-site: 'O',
			guide-site: 'M',
			google_trends: 'G'
		};
		return icons[platform] || '?';
	}

	function highlightKeywords(text: string): string {
		// Highlight common game keywords
		const keywords = ['matchmaking', 'balance', 'nerf', 'buff', 'patch', 'broken', 'OP', 'meta', 'ranked'];
		let result = text;
		for (const keyword of keywords) {
			const regex = new RegExp(`\\b(${keyword})\\b`, 'gi');
			result = result.replace(regex, '<mark>$1</mark>');
		}
		return result;
	}
</script>

<div class="mentions-feed">
	<h3 class="feed-title">Top Mentions</h3>
	<div class="feed-list">
		{#each displayQuotes as quote (quote.source_url)}
			<a
				href={quote.source_url}
				target="_blank"
				rel="noopener noreferrer"
				class="mention-item"
			>
				<div
					class="mention-icon"
					data-platform={quote.platform}
					title={quote.platform}
				>
					{getPlatformIcon(quote.platform)}
				</div>
				<div class="mention-content">
					<p class="mention-text">
						{@html highlightKeywords(quote.text)}
					</p>
					<div class="mention-meta">
						<span class="mention-platform">{quote.platform}</span>
						<span class="mention-sentiment" data-sentiment={quote.sentiment}>
							{quote.sentiment}
						</span>
					</div>
				</div>
				<svg class="mention-link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
					<polyline points="15 3 21 3 21 9" />
					<line x1="10" y1="14" x2="21" y2="3" />
				</svg>
			</a>
		{/each}
		{#if quotes.length === 0}
			<div class="feed-empty">No mentions yet</div>
		{/if}
	</div>
</div>

<style>
	.mentions-feed {
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.feed-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		padding: var(--spacing-md) var(--spacing-lg);
		margin: 0;
		border-bottom: 1px solid var(--color-border);
		color: var(--color-text-primary);
	}

	.feed-list {
		max-height: 400px;
		overflow-y: auto;
	}

	.mention-item {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-md);
		padding: var(--spacing-md) var(--spacing-lg);
		text-decoration: none;
		color: inherit;
		border-bottom: 1px solid var(--color-border-subtle);
		transition: background 0.2s ease;
	}

	.mention-item:last-child {
		border-bottom: none;
	}

	.mention-item:hover {
		background: var(--color-bg-card-hover);
	}

	.mention-icon {
		width: 36px;
		height: 36px;
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: var(--font-weight-bold);
		font-size: var(--font-size-sm);
		color: white;
		flex-shrink: 0;
	}

	.mention-icon[data-platform='youtube'] {
		background: var(--color-youtube);
	}

	.mention-icon[data-platform='official-news'] {
		background: var(--color-official-news);
	}

	.mention-icon[data-platform='tier-site'] {
		background: var(--color-tier-site);
	}

	.mention-icon[data-platform='guide-site'] {
		background: var(--color-guide-site);
	}

	.mention-icon[data-platform='google_trends'] {
		background: var(--color-google-trends);
	}

	.mention-content {
		flex: 1;
		min-width: 0;
	}

	.mention-text {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		margin: 0 0 var(--spacing-sm) 0;
		line-height: 1.4;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.mention-text :global(mark) {
		background: rgba(245, 158, 11, 0.3);
		color: var(--color-warning);
		padding: 0 2px;
		border-radius: 2px;
	}

	.mention-meta {
		display: flex;
		gap: var(--spacing-sm);
		font-size: var(--font-size-xs);
	}

	.mention-platform {
		color: var(--color-text-muted);
		text-transform: capitalize;
	}

	.mention-sentiment {
		text-transform: capitalize;
	}

	.mention-sentiment[data-sentiment='positive'] {
		color: var(--color-positive);
	}

	.mention-sentiment[data-sentiment='neutral'] {
		color: var(--color-neutral);
	}

	.mention-sentiment[data-sentiment='negative'] {
		color: var(--color-negative);
	}

	.mention-link-icon {
		width: 16px;
		height: 16px;
		color: var(--color-text-muted);
		opacity: 0;
		transition: opacity 0.2s ease;
		flex-shrink: 0;
	}

	.mention-item:hover .mention-link-icon {
		opacity: 1;
	}

	.feed-empty {
		padding: var(--spacing-xl);
		text-align: center;
		color: var(--color-text-muted);
		font-style: italic;
	}
</style>
