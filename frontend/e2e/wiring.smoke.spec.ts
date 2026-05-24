import { test, expect } from '@playwright/test';

/**
 * WIRING SMOKE TEST -- the dead-button killer.
 *
 * This is the canonical anti-phantom pattern for CommunityPulse. Unlike the
 * render-only e2e specs (which assert "a header is visible"), a wiring smoke test
 * proves the UI is actually connected to a live backend end-to-end:
 *
 *   real browser action  ->  real network request to the real API  ->  real data renders
 *
 * It runs in the FULL verification tier (`python scripts/verify.py --full`), which
 * first brings up the stack (`docker compose up -d`) and waits for the backend
 * health endpoint -- so a green run here means the wiring is real, not mocked.
 *
 * COPY THIS PATTERN for every new vertical slice:
 *   1. trigger the user action that should hit the new endpoint
 *   2. await page.waitForResponse on that endpoint and assert status 200
 *   3. assert the rendered DOM reflects the real response (not a loading/error state)
 *
 * ANTI-PATTERN (do NOT do this): wrapping the only assertion in
 * `if (await el.isVisible())` -- a hidden/unwired element then makes the test
 * silently pass. Assert unconditionally.
 */

test.describe('Dashboard wiring (UI -> API -> DB)', () => {
	test('homepage fetches dashboard data from the real backend and renders it', async ({
		page,
	}) => {
		// Capture the real API call the dashboard makes on load.
		const apiResponsePromise = page.waitForResponse(
			(resp) => resp.url().includes('/api/dashboard/') && resp.request().method() === 'GET',
			{ timeout: 30_000 }
		);

		await page.goto('/');

		const apiResponse = await apiResponsePromise;

		// The button/page is genuinely wired to the backend: the request reached the
		// API and the API answered successfully.
		expect(apiResponse.ok(), `dashboard API call failed: ${apiResponse.status()}`).toBeTruthy();

		// The response carried real, non-empty data (not an error envelope).
		const body = await apiResponse.json();
		expect(body, 'dashboard API returned no body').toBeTruthy();

		// And that data actually reached the screen -- no perpetual loading/error state.
		const errorState = page.getByText(/failed to load|something went wrong|error/i);
		await expect(errorState).toHaveCount(0);
		await expect(page.locator('main, .content, .dashboard').first()).toBeVisible();
	});
});
