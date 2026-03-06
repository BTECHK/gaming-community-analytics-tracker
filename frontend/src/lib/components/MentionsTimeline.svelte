<script lang="ts">
	import { scaleTime, scaleLinear } from 'd3-scale';
	import { area, line, curveMonotoneX } from 'd3-shape';
	import { extent, max } from 'd3-array';

	interface DataPoint {
		date: string;
		post_count: number;
	}

	interface Props {
		data: DataPoint[];
	}

	let { data }: Props = $props();

	const width = 500;
	const height = 160;
	const margin = { top: 10, right: 10, bottom: 25, left: 35 };

	const innerW = width - margin.left - margin.right;
	const innerH = height - margin.top - margin.bottom;

	const parsed = $derived(data.map(d => ({ ...d, dateObj: new Date(d.date) })));

	const xScale = $derived(
		scaleTime()
			.domain(extent(parsed, d => d.dateObj) as [Date, Date])
			.range([0, innerW])
	);

	const yScale = $derived(
		scaleLinear()
			.domain([0, max(parsed, d => d.post_count) || 1])
			.nice()
			.range([innerH, 0])
	);

	const areaGen = $derived(
		area<typeof parsed[0]>()
			.x(d => xScale(d.dateObj))
			.y0(innerH)
			.y1(d => yScale(d.post_count))
			.curve(curveMonotoneX)
	);

	const lineGen = $derived(
		line<typeof parsed[0]>()
			.x(d => xScale(d.dateObj))
			.y(d => yScale(d.post_count))
			.curve(curveMonotoneX)
	);

	const areaPath = $derived(areaGen(parsed) ?? '');
	const linePath = $derived(lineGen(parsed) ?? '');

	const yTicks = $derived(yScale.ticks(4));
	const xTicks = $derived(xScale.ticks(5));
</script>

<div class="timeline-card glass-card">
	<h3 class="card-title">Activity Over Time</h3>
	{#if data.length > 0}
		<svg viewBox="0 0 {width} {height}" class="chart-svg">
			<defs>
				<linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stop-color="var(--color-accent, #8B5CF6)" stop-opacity="0.3" />
					<stop offset="100%" stop-color="var(--color-accent, #8B5CF6)" stop-opacity="0.02" />
				</linearGradient>
			</defs>
			<g transform="translate({margin.left},{margin.top})">
				<!-- Y gridlines -->
				{#each yTicks as tick}
					<line x1="0" x2={innerW} y1={yScale(tick)} y2={yScale(tick)} stroke="var(--color-border)" stroke-opacity="0.3" />
					<text x="-5" y={yScale(tick)} dy="0.35em" text-anchor="end" class="tick-label">{tick}</text>
				{/each}
				<!-- Area + line -->
				<path d={areaPath} fill="url(#areaGrad)" />
				<path d={linePath} fill="none" stroke="var(--color-accent, #8B5CF6)" stroke-width="2" />
				<!-- X labels -->
				{#each xTicks as tick}
					<text x={xScale(tick)} y={innerH + 18} text-anchor="middle" class="tick-label">
						{tick.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
					</text>
				{/each}
			</g>
		</svg>
	{:else}
		<div class="no-data">No activity data yet</div>
	{/if}
</div>

<style>
	.timeline-card {
		padding: var(--spacing-lg);
	}

	.card-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		margin: 0 0 var(--spacing-md) 0;
	}

	.chart-svg {
		width: 100%;
		height: auto;
	}

	.tick-label {
		font-size: 10px;
		fill: var(--color-text-muted);
	}

	.no-data {
		color: var(--color-text-muted);
		text-align: center;
		padding: var(--spacing-xl);
	}
</style>
