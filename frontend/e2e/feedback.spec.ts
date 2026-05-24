import { test, expect } from '@playwright/test';

/**
 * FEEDBACK WIRING (UI -> API -> DB).
 *
 * Converted from a render-only spec full of `if (await el.isVisible())` guards
 * and console.log "assertions". Each test now drives the real control, awaits
 * the real POST it triggers, and asserts the API accepted it.
 *
 * Endpoints exercised: POST /api/feedback/general, /vote, /report.
 */

/** Load the homepage and return the first real topic slug from the DB. */
async function firstRealSlug(page: import('@playwright/test').Page): Promise<string> {
	const topicsPromise = page.waitForResponse(
		(resp) =>
			new URL(resp.url()).pathname.endsWith('/api/dashboard/topics') &&
			resp.request().method() === 'GET',
		{ timeout: 30_000 }
	);
	await page.goto('/');
	const body = await (await topicsPromise).json();
	expect(body.topics.length, 'expected at least one topic in the DB').toBeGreaterThan(0);
	return body.topics[0].slug as string;
}

test.describe('General feedback wiring', () => {
	test('floating feedback button submits to the real backend', async ({ page }) => {
		// Wait for a mount-time API call so the page has hydrated before we click
		// (the floating button's onclick isn't wired until hydration completes).
		const hydrated = page.waitForResponse(
			(resp) =>
				new URL(resp.url()).pathname.endsWith('/api/dashboard/stats') &&
				resp.request().method() === 'GET',
			{ timeout: 30_000 }
		);
		await page.goto('/');
		await hydrated;

		await page.locator('button.floating-btn').click();
		const dialog = page.getByRole('dialog', { name: /send feedback/i });
		await expect(dialog).toBeVisible();

		await dialog.locator('#feedback-message').fill('e2e wiring check: general feedback');

		const postPromise = page.waitForResponse(
			(resp) =>
				new URL(resp.url()).pathname.endsWith('/api/feedback/general') &&
				resp.request().method() === 'POST',
			{ timeout: 30_000 }
		);
		await dialog.getByRole('button', { name: /^send feedback$/i }).click();

		const resp = await postPromise;
		expect(resp.ok(), `general feedback POST failed: ${resp.status()}`).toBeTruthy();

		// The real success state rendered (not the still-open form or an error).
		await expect(dialog.getByText(/thank you for your feedback/i)).toBeVisible();
	});
});

test.describe('Topic feedback wiring', () => {
	test('voting on a topic submits to the real backend', async ({ page }) => {
		const slug = await firstRealSlug(page);
		await page.goto(`/topics/${slug}`);
		await expect(page.locator('h1.topic-name')).toBeVisible();

		const postPromise = page.waitForResponse(
			(resp) =>
				new URL(resp.url()).pathname.endsWith('/api/feedback/vote') &&
				resp.request().method() === 'POST',
			{ timeout: 30_000 }
		);
		await page.locator('.vote-btn').first().click();

		const resp = await postPromise;
		expect(resp.ok(), `vote POST failed: ${resp.status()}`).toBeTruthy();

		// The voted button reflects the recorded vote.
		await expect(page.locator('.vote-btn').first()).toHaveClass(/active/);
	});

	test('reporting a topic submits to the real backend', async ({ page }) => {
		const slug = await firstRealSlug(page);
		await page.goto(`/topics/${slug}`);
		await expect(page.locator('h1.topic-name')).toBeVisible();

		await page.getByRole('button', { name: /report issue/i }).click();
		const dialog = page.getByRole('dialog', { name: /report issue/i });
		await expect(dialog).toBeVisible();

		// Pick a reason (Submit is disabled until one is selected).
		await dialog.getByText('Misleading summary').click();

		const postPromise = page.waitForResponse(
			(resp) =>
				new URL(resp.url()).pathname.endsWith('/api/feedback/report') &&
				resp.request().method() === 'POST',
			{ timeout: 30_000 }
		);
		await dialog.getByRole('button', { name: /submit report/i }).click();

		const resp = await postPromise;
		expect(resp.ok(), `report POST failed: ${resp.status()}`).toBeTruthy();

		await expect(dialog.getByText(/thank you for your feedback/i)).toBeVisible();
	});
});
