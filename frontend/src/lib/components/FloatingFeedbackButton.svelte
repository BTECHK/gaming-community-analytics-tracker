<script lang="ts">
	import { getAnonymousSessionId } from '$lib/stores/feedback.svelte';
	import api from '$lib/api';

	let isOpen = $state(false);
	let message = $state('');
	let email = $state('');
	let submitting = $state(false);
	let submitted = $state(false);
	let error = $state<string | null>(null);

	function openModal() {
		isOpen = true;
		submitted = false;
		error = null;
	}

	function closeModal() {
		isOpen = false;
		message = '';
		email = '';
		error = null;
	}

	async function submitFeedback() {
		if (!message.trim() || submitting) return;

		submitting = true;
		error = null;

		try {
			await api.submitGeneralFeedback({
				message: message.trim(),
				email: email.trim() || undefined,
				session_id: getAnonymousSessionId()
			});
			submitted = true;
			message = '';
			email = '';
			// Auto-close after 2 seconds
			setTimeout(() => {
				closeModal();
			}, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to submit feedback';
		} finally {
			submitting = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && isOpen) {
			closeModal();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<button class="floating-btn" onclick={openModal} title="Send feedback">
	<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
		<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
	</svg>
</button>

{#if isOpen}
	<div class="modal-overlay" onclick={closeModal} role="presentation">
		<div class="modal" onclick={(e) => e.stopPropagation()} onkeydown={handleKeydown} role="dialog" aria-modal="true" aria-labelledby="feedback-title" tabindex="-1">
			<div class="modal-header">
				<h2 id="feedback-title">Send Feedback</h2>
				<button class="close-btn" onclick={closeModal} aria-label="Close">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M18 6L6 18M6 6l12 12" />
					</svg>
				</button>
			</div>

			{#if submitted}
				<div class="success-message">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
						<polyline points="22 4 12 14.01 9 11.01" />
					</svg>
					<p>Thank you for your feedback!</p>
				</div>
			{:else}
				<form onsubmit={(e) => { e.preventDefault(); submitFeedback(); }}>
					<div class="form-group">
						<label for="feedback-message">Your feedback</label>
						<textarea
							id="feedback-message"
							bind:value={message}
							placeholder="Tell us what you think, report bugs, or suggest improvements..."
							rows="4"
							maxlength="2000"
							required
						></textarea>
						<span class="char-count">{message.length}/2000</span>
					</div>

					<div class="form-group">
						<label for="feedback-email">Email (optional)</label>
						<input
							type="email"
							id="feedback-email"
							bind:value={email}
							placeholder="your@email.com"
						/>
						<span class="hint">For follow-up if needed</span>
					</div>

					{#if error}
						<div class="error-message">{error}</div>
					{/if}

					<div class="modal-actions">
						<button type="button" class="btn-secondary" onclick={closeModal}>
							Cancel
						</button>
						<button type="submit" class="btn-primary" disabled={!message.trim() || submitting}>
							{submitting ? 'Sending...' : 'Send Feedback'}
						</button>
					</div>
				</form>
			{/if}
		</div>
	</div>
{/if}

<style>
	.floating-btn {
		position: fixed;
		bottom: var(--spacing-xl);
		right: var(--spacing-xl);
		width: 56px;
		height: 56px;
		border-radius: 50%;
		background: var(--color-accent);
		color: white;
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
		transition: all 0.2s ease;
		z-index: 100;
	}

	.floating-btn:hover {
		transform: scale(1.05);
		box-shadow: 0 6px 16px rgba(139, 92, 246, 0.5);
	}

	.floating-btn svg {
		width: 24px;
		height: 24px;
	}

	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 200;
		padding: var(--spacing-lg);
	}

	.modal {
		background: var(--color-bg-card);
		border-radius: var(--radius-lg);
		width: 100%;
		max-width: 480px;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-lg);
		border-bottom: 1px solid var(--color-border);
	}

	.modal-header h2 {
		margin: 0;
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
	}

	.close-btn {
		width: 32px;
		height: 32px;
		padding: 0;
		border: none;
		background: none;
		color: var(--color-text-muted);
		cursor: pointer;
		border-radius: var(--radius-sm);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-btn:hover {
		background: var(--color-bg-secondary);
		color: var(--color-text-primary);
	}

	.close-btn svg {
		width: 20px;
		height: 20px;
	}

	form {
		padding: var(--spacing-lg);
	}

	.form-group {
		margin-bottom: var(--spacing-md);
	}

	.form-group label {
		display: block;
		margin-bottom: var(--spacing-xs);
		font-weight: var(--font-weight-medium);
		font-size: var(--font-size-sm);
	}

	textarea,
	input[type='email'] {
		width: 100%;
		padding: var(--spacing-sm);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		background: var(--color-bg-primary);
		color: var(--color-text-primary);
		font-size: var(--font-size-sm);
		font-family: inherit;
		resize: vertical;
	}

	textarea:focus,
	input[type='email']:focus {
		outline: none;
		border-color: var(--color-accent);
		box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
	}

	.char-count {
		display: block;
		text-align: right;
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
		margin-top: var(--spacing-xs);
	}

	.hint {
		display: block;
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
		margin-top: var(--spacing-xs);
	}

	.error-message {
		padding: var(--spacing-sm);
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid var(--color-negative);
		border-radius: var(--radius-md);
		color: var(--color-negative);
		font-size: var(--font-size-sm);
		margin-bottom: var(--spacing-md);
	}

	.modal-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-lg);
	}

	.btn-primary,
	.btn-secondary {
		padding: var(--spacing-sm) var(--spacing-lg);
		border-radius: var(--radius-md);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.btn-primary {
		background: var(--color-accent);
		color: white;
		border: none;
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-accent-hover);
	}

	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-secondary {
		background: transparent;
		color: var(--color-text-secondary);
		border: 1px solid var(--color-border);
	}

	.btn-secondary:hover {
		background: var(--color-bg-secondary);
	}

	.success-message {
		padding: var(--spacing-xl);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		color: var(--color-positive);
	}

	.success-message svg {
		width: 48px;
		height: 48px;
	}

	.success-message p {
		margin: 0;
		font-size: var(--font-size-md);
		font-weight: var(--font-weight-medium);
	}
</style>
