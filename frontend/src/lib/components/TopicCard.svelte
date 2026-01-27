<script lang="ts">
	import type { Topic } from '$lib/types';
	import SentimentBar from './SentimentBar.svelte';

	interface Props {
		topic: Topic;
	}

	let { topic }: Props = $props();

	const dominantSentiment = $derived(() => {
		const { positive, neutral, negative } = topic.sentiment;
		if (positive >= neutral && positive >= negative) return 'positive';
		if (negative >= positive && negative >= neutral) return 'negative';
		return 'neutral';
	});

	const topQuotes = $derived(topic.quotes.slice(0, 2));
</script>

<a href="/topics/{topic.slug}" class="topic-card">
	<div class="card-header">
		<h3 class="topic-name">{topic.name}</h3>
		<span class="post-count">{topic.post_count} posts</span>
	</div>

	<div class="sentiment-section">
		<SentimentBar sentiment={topic.sentiment} height={28} />
		<div class="sentiment-legend">
			<span class="legend-item positive">
				<span class="dot"></span>
				Positive
			</span>
			<span class="legend-item neutral">
				<span class="dot"></span>
				Neutral
			</span>
			<span class="legend-item negative">
				<span class="dot"></span>
				Negative
			</span>
		</div>
	</div>

	{#if topQuotes.length > 0}
		<div class="quotes-section">
			{#each topQuotes as quote (quote.source_url)}
				<blockquote class="quote">
					<p class="quote-text">"{quote.text}"</p>
					<cite class="quote-source">
						<span class="platform-badge" data-platform={quote.platform}>
							{quote.platform}
						</span>
					</cite>
				</blockquote>
			{/each}
		</div>
	{/if}
</a>

<style>
	.topic-card {
		display: block;
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: var(--spacing-lg);
		text-decoration: none;
		color: inherit;
		transition: all 0.2s ease;
	}

	.topic-card:hover {
		border-color: var(--color-border-hover);
		background: var(--color-bg-card-hover);
		box-shadow: 0 0 20px rgba(139, 92, 246, 0.1);
		transform: translateY(-2px);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-md);
	}

	.topic-name {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		margin: 0;
	}

	.post-count {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		background: var(--color-bg-secondary);
		padding: var(--spacing-xs) var(--spacing-sm);
		border-radius: var(--radius-full);
	}

	.sentiment-section {
		margin-bottom: var(--spacing-md);
	}

	.sentiment-legend {
		display: flex;
		gap: var(--spacing-md);
		margin-top: var(--spacing-sm);
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.legend-item .dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.legend-item.positive .dot {
		background: var(--color-positive);
	}

	.legend-item.neutral .dot {
		background: var(--color-neutral);
	}

	.legend-item.negative .dot {
		background: var(--color-negative);
	}

	.quotes-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.quote {
		margin: 0;
		padding: var(--spacing-sm);
		background: var(--color-bg-secondary);
		border-radius: var(--radius-md);
		border-left: 3px solid var(--color-accent);
	}

	.quote-text {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		margin: 0 0 var(--spacing-xs) 0;
		line-height: 1.4;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.quote-source {
		display: flex;
		align-items: center;
		font-style: normal;
	}

	.platform-badge {
		font-size: var(--font-size-xs);
		text-transform: capitalize;
		padding: 2px 6px;
		border-radius: var(--radius-sm);
		background: var(--color-bg-card);
	}

	.platform-badge[data-platform='youtube'] {
		color: var(--color-youtube);
	}

	.platform-badge[data-platform='official-news'] {
		color: var(--color-official-news);
	}

	.platform-badge[data-platform='tier-site'] {
		color: var(--color-tier-site);
	}

	.platform-badge[data-platform='guide-site'] {
		color: var(--color-guide-site);
	}
</style>
