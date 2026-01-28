<script lang="ts">
	interface Props {
		confidence: number | null;
		showLabel?: boolean;
		compact?: boolean;
		postCount?: number;
	}

	let { confidence, showLabel = true, compact = false, postCount }: Props = $props();

	const level = $derived(() => {
		if (confidence === null) return 'unknown';
		if (confidence >= 0.8) return 'high';
		if (confidence >= 0.6) return 'medium';
		return 'low';
	});

	const label = $derived(() => {
		const l = level();
		if (l === 'unknown') return 'Unknown';
		if (l === 'high') return 'High';
		if (l === 'medium') return 'Medium';
		return 'Low';
	});

	const percentage = $derived(confidence !== null ? Math.round(confidence * 100) : null);

	const tooltipText = $derived(() => {
		const l = level();
		const baseText = postCount
			? `Based on sentiment analysis confidence across ${postCount} posts.`
			: 'Based on sentiment analysis confidence across analyzed posts.';

		if (l === 'low') {
			return `${baseText} Low confidence may indicate mixed signals or limited data.`;
		}
		return baseText;
	});
</script>

<div
	class="confidence"
	class:compact
	data-level={level()}
	title={tooltipText()}
>
	<div class="confidence-dots">
		<span class="dot" class:active={confidence !== null && confidence >= 0.33}></span>
		<span class="dot" class:active={confidence !== null && confidence >= 0.66}></span>
		<span class="dot" class:active={confidence !== null && confidence >= 0.85}></span>
	</div>
	{#if showLabel}
		<span class="confidence-label">
			{label()}
			{#if percentage !== null}
				<span class="confidence-value">({percentage}%)</span>
			{/if}
		</span>
	{/if}
</div>

<style>
	.confidence {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-sm);
		cursor: help;
	}

	.confidence.compact {
		gap: var(--spacing-xs);
	}

	.confidence-dots {
		display: flex;
		gap: 3px;
	}

	.compact .confidence-dots {
		gap: 2px;
	}

	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--color-bg-secondary);
		transition: background 0.2s ease;
	}

	.compact .dot {
		width: 6px;
		height: 6px;
	}

	.dot.active {
		background: var(--color-accent);
	}

	.confidence[data-level='high'] .dot.active {
		background: var(--color-positive);
	}

	.confidence[data-level='medium'] .dot.active {
		background: var(--color-warning);
	}

	.confidence[data-level='low'] .dot.active {
		background: var(--color-negative);
	}

	.confidence-label {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
	}

	.confidence[data-level='high'] .confidence-label {
		color: var(--color-positive);
	}

	.confidence[data-level='medium'] .confidence-label {
		color: var(--color-warning);
	}

	.confidence[data-level='low'] .confidence-label {
		color: var(--color-negative);
	}

	.confidence-value {
		opacity: 0.7;
	}
</style>
