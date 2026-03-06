<script lang="ts">
	interface Props {
		score: number;
		label: string;
	}

	let { score, label }: Props = $props();

	const color = $derived(
		score <= 33 ? 'var(--color-negative)' :
		score <= 66 ? 'var(--color-warning)' :
		'var(--color-positive)'
	);

	const gradient = $derived(
		`conic-gradient(${color} ${score * 3.6}deg, var(--color-bg-secondary) ${score * 3.6}deg)`
	);
</script>

<div class="pulse-score">
	<div class="ring" style="background: {gradient}">
		<div class="ring-inner">
			<span class="score" style="color: {color}">{score}</span>
		</div>
	</div>
	<span class="label" style="color: {color}">{label}</span>
</div>

<style>
	.pulse-score {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.ring {
		width: 56px;
		height: 56px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.ring-inner {
		width: 42px;
		height: 42px;
		border-radius: 50%;
		background: var(--color-bg-card);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.score {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-bold, 700);
	}

	.label {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium, 500);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
</style>
