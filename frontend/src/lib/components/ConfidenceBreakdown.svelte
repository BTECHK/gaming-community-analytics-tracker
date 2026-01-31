<script lang="ts">
	import type { ConfidenceBreakdown } from '$lib/types';

	interface Props {
		breakdown: ConfidenceBreakdown | null;
		compact?: boolean;
	}

	let { breakdown, compact = false }: Props = $props();
	let expanded = $state(false);

	const levelColors = {
		high: 'var(--color-positive)',
		medium: 'var(--color-warning)',
		low: 'var(--color-negative)'
	};

	const levelLabels = {
		high: 'High Confidence',
		medium: 'Medium Confidence',
		low: 'Low Confidence'
	};

	function getBarColor(score: number): string {
		if (score >= 0.7) return 'var(--color-positive)';
		if (score >= 0.4) return 'var(--color-warning)';
		return 'var(--color-negative)';
	}
</script>

{#if breakdown}
	<div class="confidence-breakdown" class:compact>
		<button
			class="breakdown-header"
			onclick={() => (expanded = !expanded)}
			aria-expanded={expanded}
		>
			<div class="header-left">
				<span
					class="overall-score"
					style:color={levelColors[breakdown.level]}
				>
					{Math.round(breakdown.overall_score * 100)}%
				</span>
				<span
					class="level-label"
					style:color={levelColors[breakdown.level]}
				>
					{levelLabels[breakdown.level]}
				</span>
			</div>

			{#if !compact}
				<div class="mini-bars">
					{#each breakdown.factors as factor}
						<div
							class="mini-bar"
							title="{factor.name}: {Math.round(factor.score * 100)}%"
						>
							<div
								class="mini-bar-fill"
								style:width="{factor.score * 100}%"
								style:background-color={getBarColor(factor.score)}
							></div>
						</div>
					{/each}
				</div>
			{/if}

			<span class="expand-icon" class:expanded>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="6 9 12 15 18 9" />
				</svg>
			</span>
		</button>

		{#if expanded}
			<div class="expanded-content">
				<div class="factors-grid">
					{#each breakdown.factors as factor}
						<div class="factor-row">
							<div class="factor-info">
								<span class="factor-name">{factor.name}</span>
								<span class="factor-weight">({Math.round(factor.weight * 100)}% weight)</span>
							</div>
							<div class="factor-bar-wrapper">
								<div class="factor-bar">
									<div
										class="factor-bar-fill"
										style:width="{factor.score * 100}%"
										style:background-color={getBarColor(factor.score)}
									></div>
								</div>
								<span class="factor-score">{Math.round(factor.score * 100)}%</span>
							</div>
							<p class="factor-explanation">{factor.explanation}</p>
						</div>
					{/each}
				</div>

				{#if breakdown.limitations && breakdown.limitations.length > 0}
					<div class="limitations-box">
						<span class="limitations-icon">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
								<line x1="12" y1="9" x2="12" y2="13" />
								<line x1="12" y1="17" x2="12.01" y2="17" />
							</svg>
						</span>
						<div class="limitations-content">
							<span class="limitations-title">Limitations</span>
							<ul class="limitations-list">
								{#each breakdown.limitations as limitation}
									<li>{limitation}</li>
								{/each}
							</ul>
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>
{/if}

<style>
	.confidence-breakdown {
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		overflow: hidden;
	}

	.confidence-breakdown.compact {
		background: transparent;
		border: none;
	}

	.breakdown-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: var(--spacing-md);
		background: transparent;
		border: none;
		cursor: pointer;
		color: var(--color-text-primary);
		gap: var(--spacing-md);
	}

	.compact .breakdown-header {
		padding: var(--spacing-sm);
	}

	.breakdown-header:hover {
		background: var(--color-bg-secondary);
	}

	.header-left {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 2px;
	}

	.overall-score {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-bold);
	}

	.compact .overall-score {
		font-size: var(--font-size-lg);
	}

	.level-label {
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.mini-bars {
		display: flex;
		gap: 4px;
		flex: 1;
		max-width: 120px;
	}

	.mini-bar {
		flex: 1;
		height: 6px;
		background: var(--color-bg-secondary);
		border-radius: 3px;
		overflow: hidden;
	}

	.mini-bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 0.3s ease;
	}

	.expand-icon {
		width: 18px;
		height: 18px;
		color: var(--color-text-muted);
		transition: transform 0.2s ease;
		flex-shrink: 0;
	}

	.expand-icon.expanded {
		transform: rotate(180deg);
	}

	.expand-icon svg {
		width: 100%;
		height: 100%;
	}

	.expanded-content {
		padding: var(--spacing-md);
		border-top: 1px solid var(--color-border);
	}

	.factors-grid {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.factor-row {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.factor-info {
		display: flex;
		align-items: baseline;
		gap: var(--spacing-xs);
	}

	.factor-name {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-primary);
	}

	.factor-weight {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.factor-bar-wrapper {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.factor-bar {
		flex: 1;
		height: 8px;
		background: var(--color-bg-secondary);
		border-radius: 4px;
		overflow: hidden;
	}

	.factor-bar-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 0.3s ease;
	}

	.factor-score {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		min-width: 40px;
		text-align: right;
	}

	.factor-explanation {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
		margin: 0;
		line-height: 1.4;
	}

	.limitations-box {
		display: flex;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-md);
		padding: var(--spacing-sm) var(--spacing-md);
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.3);
		border-radius: var(--radius-md);
	}

	.limitations-icon {
		width: 18px;
		height: 18px;
		color: var(--color-negative);
		flex-shrink: 0;
		margin-top: 2px;
	}

	.limitations-icon svg {
		width: 100%;
		height: 100%;
	}

	.limitations-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.limitations-title {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-negative);
	}

	.limitations-list {
		margin: 0;
		padding-left: var(--spacing-md);
		font-size: var(--font-size-xs);
		color: var(--color-text-secondary);
	}

	.limitations-list li {
		margin-bottom: 2px;
	}

	.limitations-list li:last-child {
		margin-bottom: 0;
	}
</style>
