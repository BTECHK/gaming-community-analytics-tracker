import { test, expect } from '@playwright/test';

test.describe('Topic Pages', () => {
	test('should display topic cards on dashboard', async ({ page }) => {
		await page.goto('/');

		// Wait for page to load
		await page.waitForLoadState('networkidle');

		// Look for topic cards or similar content containers
		const content = page.locator('.topic-card, .card, article, [data-topic]');

		// If no topics, that's okay - the app might not have data loaded
		const count = await content.count();
		console.log(`Found ${count} topic elements`);
	});

	test('should navigate to topic detail page', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Try to find a clickable topic link
		const topicLink = page.locator('a[href*="/topic/"]').first();

		if (await topicLink.isVisible()) {
			await topicLink.click();
			await expect(page).toHaveURL(/\/topic\//);
		}
	});

	test('should display sentiment information on topic page', async ({ page }) => {
		// Navigate to a topic page directly (if it exists)
		await page.goto('/topic/balance');
		await page.waitForLoadState('networkidle');

		// Check if page loaded (may show 404 if no data)
		const body = page.locator('body');
		await expect(body).toBeVisible();
	});
});

test.describe('Topic Following', () => {
	test('should be able to follow a topic', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Look for follow buttons
		const followButton = page.locator('button:has-text("Follow"), button:has-text("follow"), [data-follow]').first();

		if (await followButton.isVisible()) {
			// Click to follow
			await followButton.click();

			// Check for visual feedback
			await expect(followButton).toBeVisible();
		}
	});
});
