<script lang="ts">
	interface Props {
		patch: string;
		lastUpdated?: string;
	}

	let { patch, lastUpdated }: Props = $props();

	const formattedDate = $derived(lastUpdated ? new Date(lastUpdated).toLocaleString() : null);
</script>

<div class="patch-badge">
	<span class="patch-label">Patch</span>
	<span class="patch-version">{patch}</span>
	{#if formattedDate}
		<span class="last-updated">Updated {formattedDate}</span>
	{/if}
</div>

<style>
	.patch-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm) var(--spacing-md);
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
	}

	.patch-label {
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-tertiary);
	}

	.patch-version {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-accent);
	}

	.last-updated {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		margin-left: var(--spacing-sm);
	}
</style>
