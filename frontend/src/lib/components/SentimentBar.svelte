<script lang="ts">
	import type { Sentiment } from '$lib/types';

	interface Props {
		sentiment: Sentiment;
		height?: number;
		showLabels?: boolean;
	}

	let { sentiment, height = 32, showLabels = true }: Props = $props();

	const total = $derived(sentiment.positive + sentiment.neutral + sentiment.negative);
	const positiveWidth = $derived(total > 0 ? (sentiment.positive / total) * 100 : 0);
	const neutralWidth = $derived(total > 0 ? (sentiment.neutral / total) * 100 : 0);
	const negativeWidth = $derived(total > 0 ? (sentiment.negative / total) * 100 : 0);
</script>

<div class="sentiment-bar" style="height: {height}px;">
	{#if positiveWidth > 0}
		<div
			class="segment positive"
			style="width: {positiveWidth}%;"
			title="{sentiment.positive.toFixed(1)}% Positive"
		>
			{#if showLabels && positiveWidth >= 10}
				<span class="label">{sentiment.positive.toFixed(0)}%</span>
			{/if}
		</div>
	{/if}
	{#if neutralWidth > 0}
		<div
			class="segment neutral"
			style="width: {neutralWidth}%;"
			title="{sentiment.neutral.toFixed(1)}% Neutral"
		>
			{#if showLabels && neutralWidth >= 10}
				<span class="label">{sentiment.neutral.toFixed(0)}%</span>
			{/if}
		</div>
	{/if}
	{#if negativeWidth > 0}
		<div
			class="segment negative"
			style="width: {negativeWidth}%;"
			title="{sentiment.negative.toFixed(1)}% Negative"
		>
			{#if showLabels && negativeWidth >= 10}
				<span class="label">{sentiment.negative.toFixed(0)}%</span>
			{/if}
		</div>
	{/if}
</div>

<style>
	.sentiment-bar {
		display: flex;
		width: 100%;
		border-radius: var(--radius-sm);
		overflow: hidden;
		background: var(--color-bg-secondary);
	}

	.segment {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 0;
		transition: width 0.3s ease;
	}

	.positive {
		background: var(--color-positive);
	}

	.neutral {
		background: var(--color-neutral);
	}

	.negative {
		background: var(--color-negative);
	}

	.label {
		color: white;
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
	}
</style>
