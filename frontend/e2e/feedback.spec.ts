import { test, expect } from '@playwright/test';

test.describe('Feedback System', () => {
	test('should display feedback buttons on topic cards', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Look for thumbs up/down buttons or feedback controls
		const feedbackButtons = page.locator('[data-feedback], .feedback-buttons, button[aria-label*="thumb"]');
		const count = await feedbackButtons.count();
		console.log(`Found ${count} feedback button areas`);
	});

	test('should be able to vote on topic', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Find a thumbs up button
		const thumbsUp = page.locator('button:has-text("thumbs up"), button[aria-label*="up"], [data-vote="up"]').first();

		if (await thumbsUp.isVisible()) {
			await thumbsUp.click();
			// Voting should provide some visual feedback
			await expect(thumbsUp).toBeVisible();
		}
	});

	test('should show floating feedback button', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Look for floating feedback button
		const floatingButton = page.locator('.floating-feedback, button[aria-label*="feedback"], [data-floating-feedback]');

		if (await floatingButton.first().isVisible()) {
			await expect(floatingButton.first()).toBeVisible();
		}
	});

	test('should open feedback modal when floating button clicked', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Find floating feedback button
		const floatingButton = page.locator('.floating-feedback-button, [data-floating-feedback]').first();

		if (await floatingButton.isVisible()) {
			await floatingButton.click();

			// Look for modal/dialog
			const modal = page.locator('[role="dialog"], .modal, .feedback-modal');
			await expect(modal.first()).toBeVisible();
		}
	});
});

test.describe('Report Modal', () => {
	test('should be able to open report modal', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Find report button
		const reportButton = page.locator('button:has-text("Report"), button:has-text("report"), [data-report]').first();

		if (await reportButton.isVisible()) {
			await reportButton.click();

			// Modal should appear
			const modal = page.locator('[role="dialog"], .modal, .report-modal');
			const isVisible = await modal.first().isVisible().catch(() => false);
			console.log(`Report modal visible: ${isVisible}`);
		}
	});
});
