<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import FloatingFeedbackButton from '$lib/components/FloatingFeedbackButton.svelte';
	import api from '$lib/api';
	import type { TopicNavItem } from '$lib/types';

	interface Props {
		children: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	let topics: TopicNavItem[] = $state([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			const response = await api.getTopics();
			topics = response.topics;
		} catch (e) {
			console.error('Failed to load topics:', e);
			error = e instanceof Error ? e.message : 'Failed to load topics';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</svelte:head>

<div class="app-layout">
	<Sidebar {topics} />

	<FloatingFeedbackButton />

	<div class="main-area">
		<header class="header">
			<div class="header-content">
				<h1 class="page-title">Dashboard</h1>
				<div class="header-actions">
					<ThemeToggle />
				</div>
			</div>
		</header>

		<main class="content">
			{@render children()}
		</main>
	</div>
</div>

<style>
	.app-layout {
		display: flex;
		min-height: 100vh;
	}

	.main-area {
		flex: 1;
		margin-left: var(--sidebar-width);
		display: flex;
		flex-direction: column;
	}

	.header {
		position: sticky;
		top: 0;
		background: var(--color-bg-primary);
		border-bottom: 1px solid var(--color-border);
		z-index: 50;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-md) var(--spacing-xl);
		max-width: 1600px;
		margin: 0 auto;
	}

	.page-title {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		margin: 0;
	}

	.header-actions {
		display: flex;
		gap: var(--spacing-md);
	}

	.content {
		flex: 1;
		padding: var(--spacing-xl);
		max-width: 1600px;
		margin: 0 auto;
		width: 100%;
	}
</style>
