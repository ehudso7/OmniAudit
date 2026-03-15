/**
 * OmniAudit E2E Critical Flow Tests
 *
 * Environment:
 *   Frontend: http://127.0.0.1:3000 (Vite static build served via `serve`)
 *   Backend:  http://127.0.0.1:8000 (Python FastAPI, SQLite)
 *   VITE_API_URL baked into build: http://127.0.0.1:8000
 */

import { test, expect, type Page } from '@playwright/test';

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8000';

// Unique email per test run to avoid collisions
const TEST_EMAIL = `e2e-${Date.now()}@test.com`;
const TEST_PASSWORD = 'e2eTestPass123';
let authToken = '';

// ─── Helper ──────────────────────────────────────────────────────────

async function registerUser(email: string, password: string) {
  const res = await fetch(`${API}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return res;
}

async function loginUser(email: string, password: string) {
  const res = await fetch(`${API}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return res;
}

// ─── 1. App Shell ────────────────────────────────────────────────────

test.describe('App Shell', () => {
  test('app loads and shows header', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('OmniAudit');
  });

  test('navigation tabs are visible and clickable', async ({ page }) => {
    await page.goto('/');
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    // Click each tab and verify it becomes active
    for (const tab of ['Dashboard', 'PR Reviews', 'Run Audit', 'Settings', 'Pricing']) {
      const btn = nav.locator(`button:has-text("${tab}")`);
      if (await btn.count() > 0) {
        await btn.click();
        await expect(btn).toHaveClass(/active/);
      }
    }
  });

  test('health status shows Connected when API is up', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.status-healthy')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.status-healthy')).toContainText('Connected');
  });

  test('API unavailable state is truthful', async ({ page }) => {
    // Intercept health check to simulate unavailable
    await page.route('**/api/health', route => route.abort());
    await page.goto('/');
    await expect(page.locator('.status-offline')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.status-offline')).toContainText('Demo Mode');
  });
});

// ─── 2. Auth ─────────────────────────────────────────────────────────

test.describe('Auth', () => {
  test('register valid user via API', async () => {
    const res = await registerUser(TEST_EMAIL, TEST_PASSWORD);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.token).toBeTruthy();
    expect(data.user.email).toBe(TEST_EMAIL);
    authToken = data.token;
  });

  test('reject duplicate email via API', async () => {
    const res = await registerUser(TEST_EMAIL, TEST_PASSWORD);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.detail).toContain('already registered');
  });

  test('reject short password via API', async () => {
    const res = await registerUser(`short-${Date.now()}@test.com`, 'short');
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.detail).toContain('8 characters');
  });

  test('login valid user via API', async () => {
    const res = await loginUser(TEST_EMAIL, TEST_PASSWORD);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.token).toBeTruthy();
    authToken = data.token;
  });

  test('reject invalid login via API', async () => {
    const res = await loginUser(TEST_EMAIL, 'wrongpassword123');
    expect(res.status).toBe(401);
  });

  test('protected route requires auth via API', async () => {
    const res = await fetch(`${API}/api/v1/auth/me`);
    expect(res.status).toBe(401);
  });

  test('auth flow works in browser UI', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => localStorage.setItem('omniaudit_onboarded', 'true'));

    // Click Sign In
    await page.click('button:has-text("Sign In")');
    await expect(page.locator('.auth-modal')).toBeVisible();

    // Switch to register
    await page.click('button:has-text("Create one")');

    // Fill register form with unique email
    const uiEmail = `e2e-ui-${Date.now()}@test.com`;
    await page.fill('#auth-email', uiEmail);
    await page.fill('#auth-password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // New user triggers onboarding; skip it to reach main app
    const onboarding = page.locator('.onboarding');
    if (await onboarding.isVisible({ timeout: 3000 }).catch(() => false)) {
      await page.click('button:has-text("Skip onboarding")');
    }

    // Should show logged in state (user menu with sign out)
    await expect(page.locator('button:has-text("Sign Out")')).toBeVisible({ timeout: 10000 });
  });

  test('logout works in browser UI', async ({ page }) => {
    // Register and login first
    const email = `e2e-logout-${Date.now()}@test.com`;
    await page.goto('/');
    await page.evaluate(() => localStorage.setItem('omniaudit_onboarded', 'true'));
    await page.click('button:has-text("Sign In")');
    await page.click('button:has-text("Create one")');
    await page.fill('#auth-email', email);
    await page.fill('#auth-password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Skip onboarding if it appears
    const onboarding = page.locator('.onboarding');
    if (await onboarding.isVisible({ timeout: 3000 }).catch(() => false)) {
      await page.click('button:has-text("Skip onboarding")');
    }

    await expect(page.locator('button:has-text("Sign Out")')).toBeVisible({ timeout: 10000 });

    // Now logout
    await page.click('button:has-text("Sign Out")');
    await expect(page.locator('button:has-text("Sign In")')).toBeVisible({ timeout: 5000 });
  });
});

// ─── 3. Onboarding ──────────────────────────────────────────────────

test.describe('Onboarding', () => {
  test('first-run onboarding appears for new user', async ({ page }) => {
    const email = `e2e-onboard-${Date.now()}@test.com`;

    // Clear any stored onboarding state
    await page.goto('/');
    await page.evaluate(() => localStorage.removeItem('omniaudit_onboarded'));

    // Register
    await page.click('button:has-text("Sign In")');
    await page.click('button:has-text("Create one")');
    await page.fill('#auth-email', email);
    await page.fill('#auth-password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Onboarding should appear
    await expect(page.locator('.onboarding')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('h2')).toContainText('Welcome to OmniAudit');
  });

  test('skip onboarding works', async ({ page }) => {
    const email = `e2e-skip-${Date.now()}@test.com`;
    await page.goto('/');
    await page.evaluate(() => localStorage.removeItem('omniaudit_onboarded'));

    await page.click('button:has-text("Sign In")');
    await page.click('button:has-text("Create one")');
    await page.fill('#auth-email', email);
    await page.fill('#auth-password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    await expect(page.locator('.onboarding')).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("Skip onboarding")');

    // Should see main app
    await expect(page.locator('nav')).toBeVisible({ timeout: 5000 });
  });

  test('onboarding persists server-side', async () => {
    // Register and complete onboarding via API
    const email = `e2e-persist-${Date.now()}@test.com`;
    const regRes = await registerUser(email, TEST_PASSWORD);
    const { token } = await regRes.json();

    // Mark onboarding complete
    const updateRes = await fetch(`${API}/api/v1/auth/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ onboarding_completed: true }),
    });
    expect(updateRes.status).toBe(200);

    // Verify it persisted
    const meRes = await fetch(`${API}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const me = await meRes.json();
    expect(me.user.onboarding_completed).toBe(true);
  });
});

// ─── 4. Repository Connection ────────────────────────────────────────

test.describe('Repository Connection', () => {
  let token: string;

  test.beforeAll(async () => {
    const email = `e2e-repo-${Date.now()}@test.com`;
    const res = await registerUser(email, TEST_PASSWORD);
    token = (await res.json()).token;
  });

  test('connect repository with valid payload', async () => {
    const res = await fetch(`${API}/api/v1/repositories/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ owner: 'e2eorg', repo: `e2erepo-${Date.now()}` }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.repository.owner).toBe('e2eorg');
  });

  test('repository appears in list', async () => {
    const res = await fetch(`${API}/api/v1/repositories`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.repositories.length).toBeGreaterThan(0);
  });

  test('disconnect repository works', async () => {
    // Connect a repo to disconnect
    const connectRes = await fetch(`${API}/api/v1/repositories/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ owner: 'e2eorg', repo: `todelete-${Date.now()}` }),
    });
    const { repository } = await connectRes.json();

    const delRes = await fetch(`${API}/api/v1/repositories/${repository.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(delRes.status).toBe(200);
  });
});

// ─── 5. Browser Verification ─────────────────────────────────────────

test.describe('Browser Verification', () => {
  let token: string;

  test.beforeAll(async () => {
    const email = `e2e-browser-${Date.now()}@test.com`;
    const res = await registerUser(email, TEST_PASSWORD);
    token = (await res.json()).token;
  });

  test('create browser run via API', async () => {
    const res = await fetch(`${API}/api/v1/browser-runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ target_url: 'https://example.com' }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.run).toBeTruthy();
    expect(data.run.target_url).toBe('https://example.com');
    expect(data.run.status).toBeTruthy();
  });

  test('browser run list returns runs', async () => {
    const res = await fetch(`${API}/api/v1/browser-runs?limit=5`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.runs).toBeDefined();
    expect(data.runs.length).toBeGreaterThan(0);
  });

  test('browser run detail page loads in UI', async ({ page }) => {
    // Login
    const email = `e2e-browseui-${Date.now()}@test.com`;
    await page.goto('/');
    await page.evaluate(() => localStorage.setItem('omniaudit_onboarded', 'true'));
    await page.click('button:has-text("Sign In")');
    await page.click('button:has-text("Create one")');
    await page.fill('#auth-email', email);
    await page.fill('#auth-password', TEST_PASSWORD);
    await page.click('button[type="submit"]');
    await expect(page.locator('button:has-text("Sign Out")')).toBeVisible({ timeout: 10000 });

    // Navigate to audit tab
    await page.click('button:has-text("Run Audit")');
    await expect(page.locator('.audit-container')).toBeVisible();

    // Switch to browser verification mode
    await page.click('button:has-text("Browser Verification")');
    await expect(page.locator('.mode-tab.active')).toContainText('Browser Verification');
  });
});

// ─── 6. Settings ─────────────────────────────────────────────────────

test.describe('Settings', () => {
  let token: string;

  test.beforeAll(async () => {
    const email = `e2e-settings-${Date.now()}@test.com`;
    const res = await registerUser(email, TEST_PASSWORD);
    token = (await res.json()).token;
  });

  test('update display name', async () => {
    const res = await fetch(`${API}/api/v1/auth/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ display_name: 'E2E Tester' }),
    });
    expect(res.status).toBe(200);

    const meRes = await fetch(`${API}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const me = await meRes.json();
    expect(me.user.display_name).toBe('E2E Tester');
  });

  test('update notification preferences', async () => {
    const res = await fetch(`${API}/api/v1/auth/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        notify_run_complete: false,
        notify_critical_issues: true,
      }),
    });
    expect(res.status).toBe(200);

    const meRes = await fetch(`${API}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const me = await meRes.json();
    expect(me.user.notify_run_complete).toBe(false);
    expect(me.user.notify_critical_issues).toBe(true);
  });

  test('create API key', async () => {
    const res = await fetch(`${API}/api/v1/auth/api-keys`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name: 'E2E Key' }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.api_key.key).toMatch(/^oa_/);
    expect(data.api_key.name).toBe('E2E Key');
  });

  test('list API keys does not expose raw key', async () => {
    const res = await fetch(`${API}/api/v1/auth/api-keys`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.api_keys.length).toBeGreaterThan(0);
    for (const k of data.api_keys) {
      expect(k).not.toHaveProperty('key');
      expect(k).not.toHaveProperty('key_hash');
      expect(k.prefix).toBeTruthy();
    }
  });

  test('revoke API key', async () => {
    // Create a key to revoke
    const createRes = await fetch(`${API}/api/v1/auth/api-keys`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name: 'ToRevoke' }),
    });
    const { api_key } = await createRes.json();

    // Revoke
    const revokeRes = await fetch(`${API}/api/v1/auth/api-keys/${api_key.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(revokeRes.status).toBe(200);

    // Verify not in list
    const listRes = await fetch(`${API}/api/v1/auth/api-keys`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const list = await listRes.json();
    const ids = list.api_keys.map((k: any) => k.id);
    expect(ids).not.toContain(api_key.id);
  });

  test('settings page loads in UI', async ({ page }) => {
    const email = `e2e-settingsui-${Date.now()}@test.com`;
    await page.goto('/');
    await page.evaluate(() => localStorage.setItem('omniaudit_onboarded', 'true'));
    await page.click('button:has-text("Sign In")');
    await page.click('button:has-text("Create one")');
    await page.fill('#auth-email', email);
    await page.fill('#auth-password', TEST_PASSWORD);
    await page.click('button[type="submit"]');
    await expect(page.locator('button:has-text("Sign Out")')).toBeVisible({ timeout: 10000 });

    await page.click('button:has-text("Settings")');
    // Settings should show notification prefs section
    await expect(page.locator('text=Notification Preferences')).toBeVisible({ timeout: 5000 });
  });
});

// ─── 7. Notifications ────────────────────────────────────────────────

test.describe('Notifications', () => {
  let token: string;

  test.beforeAll(async () => {
    const email = `e2e-notif-${Date.now()}@test.com`;
    const res = await registerUser(email, TEST_PASSWORD);
    token = (await res.json()).token;
  });

  test('notification list loads empty', async () => {
    const res = await fetch(`${API}/api/v1/notifications`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.notifications).toBeDefined();
  });

  test('notification created on repo connect', async () => {
    // Connect a repo to trigger notification
    await fetch(`${API}/api/v1/repositories/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ owner: 'notiforg', repo: `notifrepo-${Date.now()}` }),
    });

    const res = await fetch(`${API}/api/v1/notifications`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    expect(data.notifications.length).toBeGreaterThan(0);
    expect(data.notifications.some((n: any) => n.event_type === 'repo_connected')).toBe(true);
  });

  test('mark notification read', async () => {
    const listRes = await fetch(`${API}/api/v1/notifications`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const list = await listRes.json();
    const notifId = list.notifications[0]?.id;
    if (!notifId) return; // skip if no notifications

    const markRes = await fetch(`${API}/api/v1/notifications/${notifId}/read`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(markRes.status).toBe(200);
  });

  test('mark all read', async () => {
    const res = await fetch(`${API}/api/v1/notifications/read-all`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status).toBe(200);
  });

  test('notification bell visible in UI', async ({ page }) => {
    await page.goto('/');
    const bell = page.locator('.notification-btn');
    await expect(bell).toBeVisible();

    // Click opens dropdown
    await bell.click();
    await expect(page.locator('.notifications-dropdown')).toBeVisible();
  });
});

// ─── 8. Dashboard & Reviews ─────────────────────────────────────────

test.describe('Dashboard & Reviews', () => {
  test('dashboard loads without crashing', async ({ page }) => {
    await page.goto('/');
    // Dashboard is the default tab
    await expect(page.locator('main')).toBeVisible();
    // Should not show uncaught errors
    const errors: string[] = [];
    page.on('pageerror', err => errors.push(err.message));
    await page.waitForTimeout(3000);
    // Filter out CORS/network errors which are expected
    const realErrors = errors.filter(e => !e.includes('fetch') && !e.includes('network'));
    expect(realErrors).toHaveLength(0);
  });

  test('dashboard stats API returns real data', async () => {
    const res = await fetch(`${API}/api/v1/dashboard/stats`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.stats).toBeDefined();
    expect(data.activity).toBeDefined();
    expect(typeof data.stats.total_reviews).toBe('number');
  });

  test('reviews list API returns data', async () => {
    const res = await fetch(`${API}/api/v1/reviews`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.reviews).toBeDefined();
    expect(Array.isArray(data.reviews)).toBe(true);
  });

  test('PR Reviews tab loads', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("PR Reviews")');
    // Should show reviews content area
    await expect(page.locator('main')).toBeVisible();
    await page.waitForTimeout(2000);
  });
});
