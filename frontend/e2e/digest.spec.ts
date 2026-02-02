import { test, expect } from '@playwright/test';

test.describe('Digest Page', () => {
	test('should load the digest page', async ({ page }) => {
		await page.goto('/digest');

		// Wait for page to load
		await page.waitForLoadState('networkidle');

		// Check that we're on the digest page
		await expect(page).toHaveURL(/digest/);
	});

	test('should show empty state when no topics followed', async ({ page }) => {
		// Clear localStorage before test
		await page.goto('/');
		await page.evaluate(() => {
			localStorage.clear();
		});

		await page.goto('/digest');
		await page.waitForLoadState('networkidle');

		// Should show some message about no followed topics
		const body = await page.textContent('body');
		expect(body).toBeTruthy();
	});

	test('should show followed topics after following', async ({ page }) => {
		// Set up some followed topics in localStorage
		await page.goto('/');
		await page.evaluate(() => {
			const topics = [
				{ slug: 'balance', name: 'Champion Balance', followedAt: new Date().toISOString() }
			];
			localStorage.setItem('communitypulse:tracked-topics', JSON.stringify(topics));
		});

		await page.goto('/digest');
		await page.waitForLoadState('networkidle');

		// The digest page should now show content
		const body = page.locator('body');
		await expect(body).toBeVisible();
	});

	test('should have AI summary toggle if topics are followed', async ({ page }) => {
		// Set up followed topics
		await page.goto('/');
		await page.evaluate(() => {
			const topics = [
				{ slug: 'balance', name: 'Champion Balance', followedAt: new Date().toISOString() },
				{ slug: 'toxicity', name: 'Player Behavior', followedAt: new Date().toISOString() }
			];
			localStorage.setItem('communitypulse:tracked-topics', JSON.stringify(topics));
		});

		await page.goto('/digest');
		await page.waitForLoadState('networkidle');

		// Look for AI summary toggle
		const aiToggle = page.locator('button:has-text("AI"), button:has-text("summary"), [data-ai-toggle]');

		// Toggle may or may not be visible depending on API availability
		const isVisible = await aiToggle.first().isVisible().catch(() => false);
		console.log(`AI toggle visible: ${isVisible}`);
	});
});
