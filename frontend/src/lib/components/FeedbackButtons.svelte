<script lang="ts">
	import {
		feedbackVotes,
		getVote,
		hasVoted,
		recordVote,
		getAnonymousSessionId,
		type VoteType
	} from '$lib/stores/feedback.svelte';
	import api from '$lib/api';

	interface Props {
		slug: string;
		onReport?: () => void;
	}

	let { slug, onReport }: Props = $props();

	let submitting = $state(false);
	let error = $state<string | null>(null);

	// Subscribe to store changes to get current vote
	const currentVote = $derived(() => getVote(slug));
	const alreadyVoted = $derived(() => hasVoted(slug));

	async function submitVote(voteType: VoteType) {
		if (submitting || alreadyVoted()) return;

		submitting = true;
		error = null;

		try {
			await api.submitVote({
				topic_slug: slug,
				vote_type: voteType,
				session_id: getAnonymousSessionId()
			});
			recordVote(slug, voteType);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to submit vote';
			console.error('Vote submission failed:', e);
		} finally {
			submitting = false;
		}
	}
</script>

<div class="feedback-buttons">
	<div class="vote-buttons">
		<button
			class="vote-btn"
			class:active={currentVote() === 'thumbs_up'}
			class:disabled={alreadyVoted() && currentVote() !== 'thumbs_up'}
			onclick={() => submitVote('thumbs_up')}
			disabled={submitting || (alreadyVoted() && currentVote() !== 'thumbs_up')}
			title={alreadyVoted() ? 'You already voted' : 'Helpful summary'}
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
			</svg>
		</button>
		<button
			class="vote-btn"
			class:active={currentVote() === 'thumbs_down'}
			class:disabled={alreadyVoted() && currentVote() !== 'thumbs_down'}
			onclick={() => submitVote('thumbs_down')}
			disabled={submitting || (alreadyVoted() && currentVote() !== 'thumbs_down')}
			title={alreadyVoted() ? 'You already voted' : 'Not helpful'}
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
			</svg>
		</button>
	</div>

	{#if onReport}
		<button class="report-link" onclick={onReport}>
			Report issue
		</button>
	{/if}

	{#if error}
		<span class="error-text">{error}</span>
	{/if}
</div>

<style>
	.feedback-buttons {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.vote-buttons {
		display: flex;
		gap: var(--spacing-xs);
	}

	.vote-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		background: var(--color-bg-card);
		color: var(--color-text-muted);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.vote-btn:hover:not(:disabled) {
		border-color: var(--color-accent);
		color: var(--color-accent);
		background: rgba(139, 92, 246, 0.1);
	}

	.vote-btn.active {
		border-color: var(--color-accent);
		background: var(--color-accent);
		color: white;
	}

	.vote-btn.disabled,
	.vote-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.vote-btn svg {
		width: 16px;
		height: 16px;
	}

	.report-link {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		text-decoration: underline;
		transition: color 0.2s ease;
	}

	.report-link:hover {
		color: var(--color-negative);
	}

	.error-text {
		font-size: var(--font-size-xs);
		color: var(--color-negative);
	}
</style>
