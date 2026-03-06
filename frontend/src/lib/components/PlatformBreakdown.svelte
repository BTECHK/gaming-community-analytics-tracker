<script lang="ts">
	interface Props {
		sources: Record<string, number>;
		percentages: Record<string, number>;
	}

	let { sources, percentages }: Props = $props();

	const platformColors: Record<string, string> = {
		youtube: 'var(--color-youtube, #FF0000)',
		official-news: 'var(--color-official-news, #D32936)',
		tier-site: 'var(--color-tier-site, #5383E8)',
		guide-site: 'var(--color-guide-site, #E25822)',
		google_trends: 'var(--color-google-trends, #4285F4)',
		news-source-a: 'var(--color-news-source-a, #0066FF)',
		news-source-b: 'var(--color-news-source-b, #FF6B35)',
		reddit: 'var(--color-reddit, #FF4500)',
	};

	const sorted = $derived(
		Object.entries(sources)
			.sort(([, a], [, b]) => b - a)
			.map(([platform, count]) => ({
				platform,
				count,
				pct: percentages[platform] || 0,
				color: platformColors[platform] || 'var(--color-accent)',
			}))
	);

	const maxCount = $derived(Math.max(...Object.values(sources), 1));
</script>

<div class="platform-card glass-card">
	<h3 class="card-title">Sources</h3>
	<div class="bars">
		{#each sorted as item}
			<div class="bar-row">
				<span class="bar-label" style="color: {item.color}">{item.platform}</span>
				<div class="bar-track">
					<div
						class="bar-fill"
						style="width: {(item.count / maxCount) * 100}%; background: {item.color}"
					></div>
				</div>
				<span class="bar-value">{item.count} ({item.pct}%)</span>
			</div>
		{/each}
	</div>
</div>

<style>
	.platform-card {
		padding: var(--spacing-lg);
	}

	.card-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		margin: 0 0 var(--spacing-md) 0;
	}

	.bars {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.bar-row {
		display: grid;
		grid-template-columns: 80px 1fr auto;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.bar-label {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium, 500);
		text-transform: capitalize;
	}

	.bar-track {
		height: 8px;
		background: var(--color-bg-secondary);
		border-radius: 4px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 0.4s ease;
		opacity: 0.8;
	}

	.bar-value {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
		white-space: nowrap;
	}
</style>
