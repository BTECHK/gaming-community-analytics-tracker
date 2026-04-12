<script lang="ts">
	import type { TopicNavItem } from '$lib/types';
	import { page } from '$app/stores';
	import { trackedTopics } from '$lib/stores/tracking.svelte';

	interface Props {
		topics: TopicNavItem[];
	}

	let { topics }: Props = $props();

	const currentPath = $derived($page.url.pathname);
</script>

<aside class="sidebar">
	<div class="logo">
		<span class="logo-icon">P</span>
		<span class="logo-text">CommunityPulse</span>
	</div>

	<nav class="nav">
		<div class="nav-section">
			<a
				href="/"
				class="nav-item"
				class:active={currentPath === '/'}
			>
				<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
					<polyline points="9 22 9 12 15 12 15 22" />
				</svg>
				<span>Dashboard</span>
			</a>
			<a
				href="/digest"
				class="nav-item"
				class:active={currentPath === '/digest'}
			>
				<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<rect x="3" y="4" width="18" height="18" rx="2" />
					<line x1="16" y1="2" x2="16" y2="6" />
					<line x1="8" y1="2" x2="8" y2="6" />
					<line x1="3" y1="10" x2="21" y2="10" />
				</svg>
				<span>Digest</span>
			</a>
			<a
				href="/patch-pulse"
				class="nav-item"
				class:active={currentPath === '/patch-pulse'}
			>
				<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M22 12h-4l-3 9L9 3l-3 9H2" />
				</svg>
				<span>Patch Pulse</span>
			</a>
			<a
				href="/tracker"
				class="nav-item"
				class:active={currentPath === '/tracker'}
			>
				<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
				</svg>
				<span>My Tracker</span>
				{#if trackedTopics.current.length > 0}
					<span class="badge">{trackedTopics.current.length}</span>
				{/if}
			</a>
		</div>

		<div class="nav-section">
			<div class="nav-header">Topics</div>
			{#each topics as topic (topic.slug)}
				<a
					href="/topics/{topic.slug}"
					class="nav-item"
					class:active={currentPath === `/topics/${topic.slug}`}
				>
					<span class="topic-dot"></span>
					<span class="topic-name truncate">{topic.name}</span>
					<span class="topic-count">{topic.post_count}</span>
				</a>
			{/each}
			{#if topics.length === 0}
				<div class="nav-empty">No topics yet</div>
			{/if}
		</div>
	</nav>

	<div class="sidebar-footer">
		<div class="footer-text">Gaming Sentiment Tracker</div>
	</div>
</aside>

<style>
	.sidebar {
		width: var(--sidebar-width);
		height: 100vh;
		background: var(--color-bg-sidebar);
		border-right: 1px solid var(--color-border);
		display: flex;
		flex-direction: column;
		position: fixed;
		left: 0;
		top: 0;
		z-index: 100;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-lg);
		border-bottom: 1px solid var(--color-border);
	}

	.logo-icon {
		width: 32px;
		height: 32px;
		background: var(--color-accent-gradient);
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: var(--font-weight-bold);
		font-size: var(--font-size-lg);
		color: white;
	}

	.logo-text {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-bold);
		color: var(--color-text-primary);
	}

	.nav {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-md) 0;
	}

	.nav-section {
		margin-bottom: var(--spacing-lg);
	}

	.nav-header {
		padding: var(--spacing-sm) var(--spacing-lg);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-muted);
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm) var(--spacing-lg);
		color: var(--color-text-secondary);
		text-decoration: none;
		transition: all 0.2s ease;
		border-left: 3px solid transparent;
	}

	.nav-item:hover {
		background: rgba(139, 92, 246, 0.1);
		color: #FFFFFF;
	}

	.nav-item.active {
		background: rgba(139, 92, 246, 0.15);
		border-left-color: var(--color-accent);
		color: #FFFFFF;
	}

	.nav-icon {
		width: 20px;
		height: 20px;
		flex-shrink: 0;
	}

	.topic-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--color-accent);
		opacity: 0.5;
		flex-shrink: 0;
	}

	.nav-item.active .topic-dot {
		opacity: 1;
	}

	.topic-name {
		flex: 1;
		font-size: var(--font-size-sm);
	}

	.topic-count {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
		background: var(--color-bg-card);
		padding: 2px 8px;
		border-radius: var(--radius-full);
	}

	.nav-empty {
		padding: var(--spacing-sm) var(--spacing-lg);
		color: var(--color-text-muted);
		font-size: var(--font-size-sm);
		font-style: italic;
	}

	.badge {
		font-size: var(--font-size-xs);
		background: var(--color-accent);
		color: white;
		padding: 2px 8px;
		border-radius: var(--radius-full);
		margin-left: auto;
	}

	.sidebar-footer {
		padding: var(--spacing-md) var(--spacing-lg);
		border-top: 1px solid var(--color-border);
	}

	.footer-text {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
		text-align: center;
	}
</style>
