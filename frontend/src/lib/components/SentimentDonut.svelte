<script lang="ts">
	import { pie, arc } from 'd3-shape';

	interface Props {
		positive: number;
		neutral: number;
		negative: number;
	}

	let { positive, neutral, negative }: Props = $props();

	const total = $derived(positive + neutral + negative);

	const segments = $derived([
		{ label: 'Positive', value: positive, color: 'var(--color-positive)' },
		{ label: 'Neutral', value: neutral, color: 'var(--color-neutral, #6B7280)' },
		{ label: 'Negative', value: negative, color: 'var(--color-negative)' }
	].filter(s => s.value > 0));

	const pieGen = pie<{ label: string; value: number; color: string }>()
		.value(d => d.value)
		.sort(null);

	const arcGen = arc<any>().innerRadius(60).outerRadius(85);

	const arcs = $derived(pieGen(segments));

	const dominant = $derived(
		positive >= neutral && positive >= negative ? 'Positive' :
		negative >= positive && negative >= neutral ? 'Negative' : 'Neutral'
	);
</script>

<div class="donut-card glass-card">
	<h3 class="card-title">Sentiment Overview</h3>
	<div class="donut-wrapper">
		{#if total > 0}
			<svg viewBox="-100 -100 200 200" class="donut-svg">
				{#each arcs as a}
					<path d={arcGen(a) ?? ''} fill={a.data.color} opacity="0.85" />
				{/each}
				<text text-anchor="middle" dy="-0.2em" class="center-label">{dominant}</text>
				<text text-anchor="middle" dy="1.2em" class="center-pct">
					{Math.round(positive)}% pos
				</text>
			</svg>
		{:else}
			<div class="no-data">No data</div>
		{/if}
	</div>
	<div class="legend">
		{#each segments as seg}
			<div class="legend-item">
				<span class="legend-dot" style="background: {seg.color}"></span>
				<span class="legend-label">{seg.label}</span>
				<span class="legend-value">{Math.round(seg.value)}%</span>
			</div>
		{/each}
	</div>
</div>

<style>
	.donut-card {
		padding: var(--spacing-lg);
	}

	.card-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		margin: 0 0 var(--spacing-md) 0;
	}

	.donut-wrapper {
		display: flex;
		justify-content: center;
		padding: var(--spacing-sm) 0;
	}

	.donut-svg {
		width: 180px;
		height: 180px;
	}

	.center-label {
		font-size: 14px;
		fill: var(--color-text-primary);
		font-weight: 600;
	}

	.center-pct {
		font-size: 11px;
		fill: var(--color-text-muted);
	}

	.legend {
		display: flex;
		justify-content: center;
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

	.legend-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.legend-value {
		font-weight: var(--font-weight-medium, 500);
		color: var(--color-text-secondary);
	}

	.no-data {
		color: var(--color-text-muted);
		padding: var(--spacing-xl);
	}
</style>
