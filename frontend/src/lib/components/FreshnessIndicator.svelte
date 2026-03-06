<script lang="ts">
	interface Props {
		lastUpdated: string | null;
	}

	let { lastUpdated }: Props = $props();

	function getRelativeTime(isoString: string): { text: string; isStale: boolean } {
		const updated = new Date(isoString);
		const now = new Date();
		const diffMs = now.getTime() - updated.getTime();
		const diffMin = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMs / 3600000);
		const diffDays = Math.floor(diffMs / 86400000);

		const isStale = diffHours >= 12;

		if (diffMin < 1) return { text: 'Updated just now', isStale };
		if (diffMin < 60) return { text: `Updated ${diffMin} min ago`, isStale };
		if (diffHours < 24) return { text: `Updated ${diffHours} hour${diffHours === 1 ? '' : 's'} ago`, isStale };
		return { text: `Updated ${diffDays} day${diffDays === 1 ? '' : 's'} ago`, isStale };
	}

	const display = $derived(
		lastUpdated ? getRelativeTime(lastUpdated) : { text: 'No data yet', isStale: false }
	);
</script>

<span class="freshness" class:stale={display.isStale} class:no-data={!lastUpdated}>
	{display.text}
</span>

<style>
	.freshness {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.stale {
		color: var(--color-warning);
	}

	.no-data {
		color: var(--color-text-muted);
		opacity: 0.6;
	}
</style>
