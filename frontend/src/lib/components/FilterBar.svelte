<script lang="ts">
	import type { Platform, FilterState } from '$lib/types';

	interface Props {
		filters: FilterState;
		onFiltersChange: (filters: FilterState) => void;
	}

	let { filters, onFiltersChange }: Props = $props();

	const platforms: { id: Platform; name: string; color: string }[] = [
		{ id: 'youtube', name: 'YouTube', color: 'var(--color-youtube)' },
		{ id: 'official-news', name: 'OfficialNews', color: 'var(--color-official-news)' },
		{ id: 'tier-site', name: 'TierSite', color: 'var(--color-tier-site)' },
		{ id: 'guide-site', name: 'GuideSite', color: 'var(--color-guide-site)' },
		{ id: 'news-source-a', name: 'NewsSourceA', color: 'var(--color-news-source-a)' },
		{ id: 'news-source-b', name: 'NewsSourceB', color: 'var(--color-news-source-b)' },
		{ id: 'reddit', name: 'Reddit', color: 'var(--color-reddit)' }
	];

	const dateRanges: { value: FilterState['dateRange']; label: string }[] = [
		{ value: '7d', label: 'Last 7 days' },
		{ value: '14d', label: 'Last 14 days' },
		{ value: '30d', label: 'Last 30 days' }
	];

	function removeTheme(theme: string) {
		const newThemes = filters.themes.filter((t) => t !== theme);
		onFiltersChange({ ...filters, themes: newThemes });
	}

	function togglePlatform(platform: Platform) {
		const newPlatforms = filters.platforms.includes(platform)
			? filters.platforms.filter((p) => p !== platform)
			: [...filters.platforms, platform];
		onFiltersChange({ ...filters, platforms: newPlatforms });
	}

	function setDateRange(range: FilterState['dateRange']) {
		onFiltersChange({ ...filters, dateRange: range });
	}
</script>

<div class="filter-bar">
	<div class="filter-section">
		{#if filters.themes.length > 0}
			<div class="theme-chips">
				{#each filters.themes as theme (theme)}
					<button class="chip" onclick={() => removeTheme(theme)}>
						<span>{theme}</span>
						<svg class="chip-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="18" y1="6" x2="6" y2="18" />
							<line x1="6" y1="6" x2="18" y2="18" />
						</svg>
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<div class="filter-section">
		<div class="platform-toggles">
			{#each platforms as platform (platform.id)}
				<button
					class="platform-toggle"
					class:active={filters.platforms.includes(platform.id)}
					style="--platform-color: {platform.color}"
					onclick={() => togglePlatform(platform.id)}
					title={platform.name}
				>
					{platform.name.charAt(0)}
				</button>
			{/each}
		</div>
	</div>

	<div class="filter-section">
		<select
			class="date-select"
			value={filters.dateRange}
			onchange={(e) => setDateRange((e.target as HTMLSelectElement).value as FilterState['dateRange'])}
		>
			{#each dateRanges as range (range.value)}
				<option value={range.value}>{range.label}</option>
			{/each}
		</select>
	</div>
</div>

<style>
	.filter-bar {
		display: flex;
		align-items: center;
		gap: var(--spacing-lg);
		padding: var(--spacing-md) var(--spacing-lg);
		background: var(--color-bg-secondary);
		border-bottom: 1px solid var(--color-border);
		flex-wrap: wrap;
	}

	.filter-section {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.theme-chips {
		display: flex;
		gap: var(--spacing-sm);
		flex-wrap: wrap;
	}

	.chip {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: rgba(139, 92, 246, 0.2);
		border: 1px solid var(--color-accent);
		border-radius: var(--radius-full);
		color: var(--color-accent-secondary);
		font-size: var(--font-size-sm);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.chip:hover {
		background: rgba(139, 92, 246, 0.3);
	}

	.chip-close {
		width: 14px;
		height: 14px;
		opacity: 0.7;
	}

	.chip:hover .chip-close {
		opacity: 1;
	}

	.platform-toggles {
		display: flex;
		gap: var(--spacing-xs);
	}

	.platform-toggle {
		width: 32px;
		height: 32px;
		border-radius: var(--radius-md);
		border: 1px solid var(--color-border);
		background: transparent;
		color: var(--color-text-muted);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.platform-toggle:hover {
		border-color: var(--platform-color);
		color: var(--platform-color);
	}

	.platform-toggle.active {
		background: var(--platform-color);
		border-color: var(--platform-color);
		color: white;
	}

	.date-select {
		padding: var(--spacing-sm) var(--spacing-md);
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		color: var(--color-text-primary);
		font-size: var(--font-size-sm);
		cursor: pointer;
		outline: none;
	}

	.date-select:focus {
		border-color: var(--color-accent);
	}

	.date-select option {
		background: var(--color-bg-card);
		color: var(--color-text-primary);
	}
</style>
