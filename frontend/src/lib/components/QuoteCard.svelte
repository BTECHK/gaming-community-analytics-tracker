<script lang="ts">
	import type { Quote } from '$lib/types';
	import SourceBadge from './SourceBadge.svelte';

	interface Props {
		quote: Quote;
	}

	let { quote }: Props = $props();
</script>

<div class="quote-card" data-sentiment={quote.sentiment}>
	<blockquote class="quote-content">
		<p class="quote-text">"{quote.text}"</p>
	</blockquote>

	<div class="quote-footer">
		<div class="quote-meta">
			<SourceBadge platform={quote.platform} size="sm" />
			<span class="quote-sentiment" data-sentiment={quote.sentiment}>
				{quote.sentiment}
			</span>
		</div>

		<a
			href={quote.source_url}
			target="_blank"
			rel="noopener noreferrer"
			class="quote-link"
		>
			View source
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
				<polyline points="15 3 21 3 21 9" />
				<line x1="10" y1="14" x2="21" y2="3" />
			</svg>
		</a>
	</div>
</div>

<style>
	.quote-card {
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: var(--spacing-lg);
		transition: all 0.2s ease;
	}

	.quote-card:hover {
		border-color: var(--color-border-hover);
	}

	.quote-card[data-sentiment='positive'] {
		border-left: 3px solid var(--color-positive);
	}

	.quote-card[data-sentiment='neutral'] {
		border-left: 3px solid var(--color-neutral);
	}

	.quote-card[data-sentiment='negative'] {
		border-left: 3px solid var(--color-negative);
	}

	.quote-content {
		margin: 0 0 var(--spacing-md) 0;
	}

	.quote-text {
		font-size: var(--font-size-base);
		color: var(--color-text-secondary);
		line-height: 1.6;
		margin: 0;
	}

	.quote-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: var(--spacing-sm);
	}

	.quote-meta {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.quote-sentiment {
		font-size: var(--font-size-xs);
		text-transform: capitalize;
	}

	.quote-sentiment[data-sentiment='positive'] {
		color: var(--color-positive);
	}

	.quote-sentiment[data-sentiment='neutral'] {
		color: var(--color-neutral);
	}

	.quote-sentiment[data-sentiment='negative'] {
		color: var(--color-negative);
	}

	.quote-link {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-xs);
		font-size: var(--font-size-sm);
		color: var(--color-accent);
		text-decoration: none;
		transition: color 0.2s ease;
	}

	.quote-link:hover {
		color: var(--color-accent-secondary);
	}

	.quote-link svg {
		width: 14px;
		height: 14px;
	}
</style>
