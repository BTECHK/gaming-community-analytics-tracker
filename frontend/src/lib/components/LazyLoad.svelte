<script lang="ts">
	import { onMount } from 'svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		/** Minimum height for the placeholder to prevent layout shift */
		minHeight?: string;
		/** Root margin for intersection observer (load before visible) */
		rootMargin?: string;
		/** Content to render once visible */
		children: Snippet;
		/** Optional loading placeholder */
		placeholder?: Snippet;
	}

	let {
		minHeight = '100px',
		rootMargin = '100px',
		children,
		placeholder
	}: Props = $props();

	let container: HTMLDivElement;
	let isVisible = $state(false);

	onMount(() => {
		const observer = new IntersectionObserver(
			(entries) => {
				if (entries[0].isIntersecting) {
					isVisible = true;
					observer.disconnect();
				}
			},
			{
				rootMargin,
				threshold: 0
			}
		);

		observer.observe(container);

		return () => observer.disconnect();
	});
</script>

<div bind:this={container} style:min-height={isVisible ? 'auto' : minHeight}>
	{#if isVisible}
		{@render children()}
	{:else if placeholder}
		{@render placeholder()}
	{:else}
		<div class="lazy-placeholder" style:min-height={minHeight}>
			<div class="lazy-skeleton"></div>
		</div>
	{/if}
</div>

<style>
	.lazy-placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
	}

	.lazy-skeleton {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-border);
		border-top-color: var(--color-accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
