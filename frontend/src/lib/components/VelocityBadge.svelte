<script lang="ts">
	interface Props {
		velocityLabel: 'rising' | 'steady' | 'cooling' | null;
		velocityPct: number;
	}

	let { velocityLabel, velocityPct }: Props = $props();

	const arrow = $derived(
		velocityLabel === 'rising' ? '\u2191' :
		velocityLabel === 'cooling' ? '\u2193' :
		velocityLabel === 'steady' ? '\u2192' : ''
	);

	const displayPct = $derived(
		velocityPct >= 0 ? `+${velocityPct}%` : `${velocityPct}%`
	);
</script>

{#if velocityLabel}
	<span class="velocity-badge" class:rising={velocityLabel === 'rising'} class:cooling={velocityLabel === 'cooling'} class:steady={velocityLabel === 'steady'}>
		{arrow} {displayPct}
	</span>
{/if}

<style>
	.velocity-badge {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium, 500);
		padding: 2px 6px;
		border-radius: var(--radius-sm);
	}

	.rising {
		color: #22C55E;
	}

	.cooling {
		color: #EF4444;
	}

	.steady {
		color: var(--color-text-muted);
	}
</style>
