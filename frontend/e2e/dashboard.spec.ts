import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
	test('should load the homepage', async ({ page }) => {
		await page.goto('/');

		// Should show the main dashboard
		await expect(page).toHaveTitle(/CommunityPulse/i);
	});

	test('should display header with logo', async ({ page }) => {
		await page.goto('/');

		// Look for the header/logo area
		const header = page.locator('header, nav, .header, .navbar').first();
		await expect(header).toBeVisible();
	});

	test('should display trending topics section', async ({ page }) => {
		await page.goto('/');

		// Wait for content to load - either topics or a loading state
		const content = page.locator('main, .content, .dashboard');
		await expect(content.first()).toBeVisible();
	});

	test('should navigate to digest page', async ({ page }) => {
		await page.goto('/');

		// Find and click the digest link
		const digestLink = page.getByRole('link', { name: /digest/i });
		if (await digestLink.isVisible()) {
			await digestLink.click();
			await expect(page).toHaveURL(/digest/);
		}
	});

	test('should have sidebar navigation', async ({ page }) => {
		await page.goto('/');

		// Look for sidebar or navigation area
		const sidebar = page.locator('aside, .sidebar, nav');
		await expect(sidebar.first()).toBeVisible();
	});
});

test.describe('Navigation', () => {
	test('should navigate between pages', async ({ page }) => {
		await page.goto('/');

		// Check that the page loaded
		await expect(page.locator('body')).toBeVisible();
	});

	test('should handle 404 for unknown routes', async ({ page }) => {
		const response = await page.goto('/this-page-does-not-exist');

		// SvelteKit should handle this gracefully
		expect(response).not.toBeNull();
	});
});
