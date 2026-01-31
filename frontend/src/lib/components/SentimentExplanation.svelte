<script lang="ts">
	import type { SentimentExplanation } from '$lib/types';

	interface Props {
		explanation: SentimentExplanation | null;
	}

	let { explanation }: Props = $props();
	let expanded = $state(false);

	const strengthColors = {
		strong: 'var(--color-positive)',
		moderate: 'var(--color-warning)',
		mixed: 'var(--color-text-muted)'
	};

	const impactIcons = {
		positive: '+',
		negative: '-',
		neutral: '~'
	};

	const impactColors = {
		positive: 'var(--color-positive)',
		negative: 'var(--color-negative)',
		neutral: 'var(--color-text-muted)'
	};
</script>

{#if explanation}
	<div class="explanation-card">
		<button
			class="explanation-header"
			onclick={() => (expanded = !expanded)}
			aria-expanded={expanded}
		>
			<div class="header-content">
				<span class="header-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<circle cx="12" cy="12" r="10" />
						<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
						<line x1="12" y1="17" x2="12.01" y2="17" />
					</svg>
				</span>
				<span class="header-title">Why {explanation.dominant_sentiment}?</span>
				<span
					class="strength-badge"
					style:background-color={strengthColors[explanation.strength]}
				>
					{explanation.strength}
				</span>
			</div>
			<span class="expand-icon" class:expanded>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="6 9 12 15 18 9" />
				</svg>
			</span>
		</button>

		<div class="primary-reason">
			{explanation.primary_reason}
		</div>

		{#if expanded}
			<div class="expanded-content">
				<div class="factors-list">
					{#each explanation.factors as factor}
						<div class="factor-item">
							<span
								class="factor-icon"
								style:color={impactColors[factor.impact]}
							>
								{impactIcons[factor.impact]}
							</span>
							<span class="factor-description">{factor.description}</span>
						</div>
					{/each}
				</div>

				<p class="distribution-note">
					{explanation.sentiment_distribution_note}
				</p>
			</div>
		{/if}
	</div>
{/if}

<style>
	.explanation-card {
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		overflow: hidden;
		margin-top: var(--spacing-md);
	}

	.explanation-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: var(--spacing-sm) var(--spacing-md);
		background: transparent;
		border: none;
		cursor: pointer;
		color: var(--color-text-primary);
		text-align: left;
		transition: background 0.2s ease;
	}

	.explanation-header:hover {
		background: var(--color-bg-secondary);
	}

	.header-content {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.header-icon {
		width: 18px;
		height: 18px;
		color: var(--color-accent);
		display: flex;
		align-items: center;
	}

	.header-icon svg {
		width: 100%;
		height: 100%;
	}

	.header-title {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		text-transform: capitalize;
	}

	.strength-badge {
		font-size: var(--font-size-xs);
		padding: 2px 8px;
		border-radius: var(--radius-sm);
		color: white;
		text-transform: capitalize;
	}

	.expand-icon {
		width: 18px;
		height: 18px;
		color: var(--color-text-muted);
		transition: transform 0.2s ease;
	}

	.expand-icon.expanded {
		transform: rotate(180deg);
	}

	.expand-icon svg {
		width: 100%;
		height: 100%;
	}

	.primary-reason {
		padding: 0 var(--spacing-md) var(--spacing-md);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		line-height: 1.5;
	}

	.expanded-content {
		padding: 0 var(--spacing-md) var(--spacing-md);
		border-top: 1px solid var(--color-border);
		padding-top: var(--spacing-md);
	}

	.factors-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-md);
	}

	.factor-item {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-sm);
		font-size: var(--font-size-sm);
	}

	.factor-icon {
		font-weight: var(--font-weight-bold);
		font-size: var(--font-size-base);
		width: 16px;
		text-align: center;
		flex-shrink: 0;
	}

	.factor-description {
		color: var(--color-text-secondary);
		line-height: 1.4;
	}

	.distribution-note {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
		font-style: italic;
		margin: 0;
		padding-top: var(--spacing-sm);
		border-top: 1px dashed var(--color-border);
	}
</style>
