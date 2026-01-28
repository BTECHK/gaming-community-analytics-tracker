<script lang="ts">
	import { trackedTopics, followTopic, unfollowTopic, type TrackedTopic } from '$lib/stores/tracking.svelte';

	interface Props {
		slug: string;
		name: string;
		compact?: boolean;
	}

	let { slug, name, compact = false }: Props = $props();

	// Derive following state from store
	const following = $derived(trackedTopics.current.some((t: TrackedTopic) => t.slug === slug));

	function toggle() {
		if (following) {
			unfollowTopic(slug);
		} else {
			followTopic(slug, name);
		}
	}
</script>

<button
	class="follow-btn"
	class:following
	class:compact
	onclick={toggle}
	aria-pressed={following}
	title={following ? `Unfollow ${name}` : `Follow ${name}`}
>
	{#if following}
		<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
			<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
		</svg>
		{#if !compact}
			<span>Following</span>
		{/if}
	{:else}
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
			<path d="M12 5v14M5 12h14" />
		</svg>
		{#if !compact}
			<span>Follow</span>
		{/if}
	{/if}
</button>

<style>
	.follow-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm) var(--spacing-md);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-md);
		border: 1px solid var(--color-border);
		background: transparent;
		color: var(--color-text-secondary);
		cursor: pointer;
		transition: all 0.2s ease;
		white-space: nowrap;
	}

	.follow-btn:hover {
		border-color: var(--color-accent);
		color: var(--color-accent);
	}

	.follow-btn:focus-visible {
		outline: 2px solid var(--color-accent);
		outline-offset: 2px;
	}

	.follow-btn.following {
		background: var(--color-accent);
		border-color: var(--color-accent);
		color: white;
	}

	.follow-btn.following:hover {
		background: var(--color-negative);
		border-color: var(--color-negative);
	}

	.follow-btn.compact {
		padding: var(--spacing-xs) var(--spacing-sm);
	}

	.follow-btn svg {
		width: 16px;
		height: 16px;
		flex-shrink: 0;
	}
</style>
