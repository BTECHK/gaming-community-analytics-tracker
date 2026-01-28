<script lang="ts">
	import api from '$lib/api';
	import { getAnonymousSessionId } from '$lib/stores/feedback.svelte';

	interface Props {
		slug: string;
		topicName: string;
		open: boolean;
		onClose: () => void;
	}

	let { slug, topicName, open, onClose }: Props = $props();

	type ReportReason = 'misleading' | 'inaccurate_quotes' | 'wrong_sentiment' | 'other';

	let selectedReason = $state<ReportReason | null>(null);
	let details = $state('');
	let submitting = $state(false);
	let submitted = $state(false);
	let error = $state<string | null>(null);

	const reasons: { value: ReportReason; label: string }[] = [
		{ value: 'misleading', label: 'Misleading summary' },
		{ value: 'inaccurate_quotes', label: 'Inaccurate quotes' },
		{ value: 'wrong_sentiment', label: 'Wrong sentiment' },
		{ value: 'other', label: 'Other' }
	];

	function handleClose() {
		// Reset state when closing
		selectedReason = null;
		details = '';
		submitted = false;
		error = null;
		onClose();
	}

	async function handleSubmit() {
		if (!selectedReason || submitting) return;

		submitting = true;
		error = null;

		try {
			await api.submitReport({
				topic_slug: slug,
				reason: selectedReason,
				details: details.trim() || undefined,
				session_id: getAnonymousSessionId()
			});
			submitted = true;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to submit report';
			console.error('Report submission failed:', e);
		} finally {
			submitting = false;
		}
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			handleClose();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			handleClose();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div class="modal-backdrop" role="presentation" onclick={handleBackdropClick}>
		<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
			<div class="modal-header">
				<h2 id="modal-title">Report Issue</h2>
				<button class="close-btn" onclick={handleClose} aria-label="Close">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<line x1="18" y1="6" x2="6" y2="18" />
						<line x1="6" y1="6" x2="18" y2="18" />
					</svg>
				</button>
			</div>

			{#if submitted}
				<div class="modal-body success">
					<div class="success-icon">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<polyline points="20 6 9 17 4 12" />
						</svg>
					</div>
					<h3>Thank you for your feedback</h3>
					<p>Your report has been submitted and will be reviewed.</p>
					<button class="btn btn-primary" onclick={handleClose}>Close</button>
				</div>
			{:else}
				<div class="modal-body">
					<p class="topic-info">Reporting: <strong>{topicName}</strong></p>

					<div class="form-group">
						<fieldset class="form-fieldset">
							<legend class="form-label">What's the issue?</legend>
							<div class="reason-options">
							{#each reasons as reason}
								<label class="reason-option">
									<input
										type="radio"
										name="reason"
										value={reason.value}
										bind:group={selectedReason}
									/>
									<span class="reason-label">{reason.label}</span>
								</label>
							{/each}
							</div>
						</fieldset>
					</div>

					<div class="form-group">
						<label class="form-label" for="details">Additional details (optional)</label>
						<textarea
							id="details"
							bind:value={details}
							placeholder="Please describe the issue..."
							rows="3"
							maxlength="1000"
						></textarea>
					</div>

					{#if error}
						<p class="error-message">{error}</p>
					{/if}
				</div>

				<div class="modal-footer">
					<button class="btn btn-secondary" onclick={handleClose}>Cancel</button>
					<button
						class="btn btn-primary"
						onclick={handleSubmit}
						disabled={!selectedReason || submitting}
					>
						{submitting ? 'Submitting...' : 'Submit Report'}
					</button>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-lg);
	}

	.modal {
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		width: 100%;
		max-width: 480px;
		max-height: 90vh;
		overflow-y: auto;
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
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		border: none;
		background: none;
		color: var(--color-text-muted);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: all 0.2s ease;
	}

	.close-btn:hover {
		background: var(--color-bg-secondary);
		color: var(--color-text-primary);
	}

	.close-btn svg {
		width: 20px;
		height: 20px;
	}

	.modal-body {
		padding: var(--spacing-lg);
	}

	.modal-body.success {
		text-align: center;
		padding: var(--spacing-xl);
	}

	.success-icon {
		width: 48px;
		height: 48px;
		margin: 0 auto var(--spacing-md);
		color: var(--color-positive);
	}

	.success-icon svg {
		width: 100%;
		height: 100%;
	}

	.modal-body.success h3 {
		margin: 0 0 var(--spacing-sm) 0;
		font-size: var(--font-size-lg);
	}

	.modal-body.success p {
		color: var(--color-text-secondary);
		margin: 0 0 var(--spacing-lg) 0;
	}

	.topic-info {
		color: var(--color-text-secondary);
		font-size: var(--font-size-sm);
		margin: 0 0 var(--spacing-lg) 0;
	}

	.form-group {
		margin-bottom: var(--spacing-lg);
	}

	.form-label {
		display: block;
		font-weight: var(--font-weight-medium);
		margin-bottom: var(--spacing-sm);
	}

	.form-fieldset {
		border: none;
		padding: 0;
		margin: 0;
	}

	.reason-options {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.reason-option {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		cursor: pointer;
	}

	.reason-option input {
		accent-color: var(--color-accent);
	}

	.reason-label {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
	}

	textarea {
		width: 100%;
		padding: var(--spacing-sm);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		background: var(--color-bg-secondary);
		color: var(--color-text-primary);
		font-family: inherit;
		font-size: var(--font-size-sm);
		resize: vertical;
	}

	textarea:focus {
		outline: none;
		border-color: var(--color-accent);
	}

	.error-message {
		color: var(--color-negative);
		font-size: var(--font-size-sm);
		margin: 0;
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-sm);
		padding: var(--spacing-lg);
		border-top: 1px solid var(--color-border);
	}

	.btn {
		padding: var(--spacing-sm) var(--spacing-lg);
		border-radius: var(--radius-md);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		border: none;
		font-size: var(--font-size-sm);
		transition: opacity 0.2s ease;
	}

	.btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-primary {
		background: var(--color-accent);
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		opacity: 0.9;
	}

	.btn-secondary {
		background: var(--color-bg-secondary);
		color: var(--color-text-secondary);
	}

	.btn-secondary:hover:not(:disabled) {
		background: var(--color-bg-card-hover);
	}
</style>
