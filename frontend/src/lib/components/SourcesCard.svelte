<script lang="ts">
	interface Props {
		sources: Record<string, number>;
		percentages: Record<string, number>;
	}

	let { sources, percentages }: Props = $props();

	const platformColors: Record<string, string> = {
		youtube: 'var(--color-youtube)',
		official-news: 'var(--color-official-news)',
		tier-site: 'var(--color-tier-site)',
		guide-site: 'var(--color-guide-site)',
		reddit: 'var(--color-reddit)',
		google_trends: 'var(--color-google-trends)'
	};

	const platformNames: Record<string, string> = {
		youtube: 'YouTube',
		official-news: 'OfficialNews',
		tier-site: 'TierSite',
		guide-site: 'GuideSite',
		reddit: 'Reddit',
		google_trends: 'Google Trends'
	};

	const sortedSources = $derived(
		Object.entries(sources).sort(([, a], [, b]) => b - a)
	);
</script>

<div class="sources-card">
	<h3 class="card-title">Sources</h3>
	<div class="sources-list">
		{#each sortedSources as [platform, count] (platform)}
			<div class="source-item">
				<div class="source-info">
					<span class="source-name">{platformNames[platform] || platform}</span>
					<span class="source-count">{count}</span>
				</div>
				<div class="source-bar-container">
					<div
						class="source-bar"
						style="width: {percentages[platform] || 0}%; background: {platformColors[platform] || 'var(--color-accent)'};"
					></div>
				</div>
				<span class="source-percent">{(percentages[platform] || 0).toFixed(1)}%</span>
			</div>
		{/each}
		{#if sortedSources.length === 0}
			<div class="sources-empty">No data available</div>
		{/if}
	</div>
</div>

<style>
	.sources-card {
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: var(--spacing-lg);
	}

	.card-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		margin: 0 0 var(--spacing-md) 0;
		color: var(--color-text-primary);
	}

	.sources-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.source-item {
		display: grid;
		grid-template-columns: 100px 1fr 50px;
		gap: var(--spacing-md);
		align-items: center;
	}

	.source-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.source-name {
		font-size: var(--font-size-sm);
		color: var(--color-text-primary);
	}

	.source-count {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.source-bar-container {
		height: 8px;
		background: var(--color-bg-secondary);
		border-radius: var(--radius-full);
		overflow: hidden;
	}

	.source-bar {
		height: 100%;
		border-radius: var(--radius-full);
		transition: width 0.3s ease;
	}

	.source-percent {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		text-align: right;
	}

	.sources-empty {
		padding: var(--spacing-lg);
		text-align: center;
		color: var(--color-text-muted);
		font-style: italic;
	}
</style>
