<script lang="ts">
	interface Props {
		heatmap: number[][];
	}

	let { heatmap }: Props = $props();

	const dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
	const hourLabels = [0, 3, 6, 9, 12, 15, 18, 21];

	const maxVal = $derived(Math.max(...heatmap.flat(), 1));

	function cellColor(value: number): string {
		const intensity = value / maxVal;
		return `rgba(139, 92, 246, ${0.1 + intensity * 0.85})`;
	}

	let tooltipText = $state('');
	let tooltipVisible = $state(false);

	function showTooltip(day: number, hour: number, count: number) {
		const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
		tooltipText = `${dayNames[day]} ${hour}:00 — ${count} post${count !== 1 ? 's' : ''}`;
		tooltipVisible = true;
	}

	function hideTooltip() {
		tooltipVisible = false;
	}
</script>

<div class="heatmap-card glass-card">
	<h3 class="card-title">Community Activity</h3>
	{#if tooltipVisible}
		<div class="tooltip">{tooltipText}</div>
	{/if}
	<div class="heatmap-grid">
		<!-- Hour labels row -->
		<div class="corner-cell"></div>
		{#each Array(24) as _, h}
			{#if hourLabels.includes(h)}
				<div class="hour-label">{h}</div>
			{:else}
				<div class="hour-label"></div>
			{/if}
		{/each}

		<!-- Data rows -->
		{#each heatmap as row, d}
			<div class="day-label">{dayLabels[d]}</div>
			{#each row as value, h}
				<div
					class="cell"
					style="background: {cellColor(value)}"
					role="gridcell"
					onmouseenter={() => showTooltip(d, h, value)}
					onmouseleave={hideTooltip}
				></div>
			{/each}
		{/each}
	</div>
</div>

<style>
	.heatmap-card {
		padding: var(--spacing-lg);
	}

	.card-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		margin: 0 0 var(--spacing-md) 0;
	}

	.tooltip {
		font-size: var(--font-size-xs);
		color: var(--color-text-secondary);
		padding: var(--spacing-xs) 0;
		text-align: center;
	}

	.heatmap-grid {
		display: grid;
		grid-template-columns: 20px repeat(24, 1fr);
		gap: 2px;
	}

	.corner-cell {
		display: block;
	}

	.hour-label {
		font-size: 9px;
		color: var(--color-text-muted);
		text-align: center;
	}

	.day-label {
		font-size: 10px;
		color: var(--color-text-muted);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.cell {
		aspect-ratio: 1;
		border-radius: 2px;
		min-height: 10px;
		transition: opacity 0.15s ease;
	}

	.cell:hover {
		opacity: 0.7;
		outline: 1px solid var(--color-accent, #8B5CF6);
	}
</style>
