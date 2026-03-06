<script lang="ts">
	import type { StatsResponse } from '$lib/types';
	import PulseScore from './PulseScore.svelte';

	interface Props {
		stats: StatsResponse;
	}

	let { stats }: Props = $props();
</script>

<div class="stats-banner">
	<div class="stat-item">
		<span class="stat-value">{stats.posts_analyzed.toLocaleString()}</span>
		<span class="stat-label">Posts Analyzed</span>
	</div>
	<div class="stat-item">
		<span class="stat-value">{stats.active_topics}</span>
		<span class="stat-label">Active Topics</span>
	</div>
	<div class="stat-item">
		<span class="stat-value">{stats.sources_active}</span>
		<span class="stat-label">Sources</span>
	</div>
	<div class="stat-item pulse-item">
		<PulseScore score={stats.pulse_score} label={stats.pulse_label} />
	</div>
</div>

<style>
	.stats-banner {
		display: flex;
		align-items: center;
		justify-content: space-around;
		gap: var(--spacing-lg);
		padding: var(--spacing-lg) var(--spacing-xl);
		background: rgba(18, 18, 26, 0.8);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.stat-value {
		font-size: var(--font-size-2xl, 1.5rem);
		font-weight: var(--font-weight-bold, 700);
		color: var(--color-text-primary);
	}

	.stat-label {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.pulse-item {
		gap: 0;
	}

	@media (max-width: 768px) {
		.stats-banner {
			flex-wrap: wrap;
			gap: var(--spacing-md);
		}

		.stat-item {
			flex: 1 1 40%;
		}
	}
</style>
