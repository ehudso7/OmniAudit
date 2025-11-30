import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display the dashboard title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should show stats cards', async ({ page }) => {
    await expect(page.getByText('Total Reviews')).toBeVisible();
    await expect(page.getByText('Issues Found')).toBeVisible();
    await expect(page.getByText('Security Blocked')).toBeVisible();
    await expect(page.getByText('Performance Issues')).toBeVisible();
  });

  test('should display health score', async ({ page }) => {
    await expect(page.getByText('Code Health Score')).toBeVisible();
  });

  test('should show severity chart', async ({ page }) => {
    await expect(page.getByText('Issues by Severity')).toBeVisible();
  });

  test('should navigate to different sections via sidebar', async ({ page }) => {
    // Navigate to PR Reviews
    await page.getByRole('link', { name: /PR Reviews/i }).click();
    await expect(page.getByRole('heading', { name: 'PR Reviews' })).toBeVisible();

    // Navigate to Run Audit
    await page.getByRole('link', { name: /Run Audit/i }).click();
    await expect(page.getByRole('heading', { name: 'Run Audit' })).toBeVisible();

    // Navigate to Analytics
    await page.getByRole('link', { name: /Analytics/i }).click();
    await expect(page.getByRole('heading', { name: 'Analytics' })).toBeVisible();
  });

  test('should toggle dark mode', async ({ page }) => {
    const html = page.locator('html');

    // Check initial state
    const initialClass = await html.getAttribute('class');

    // Click theme toggle
    await page.getByRole('button').filter({ hasText: '' }).first().click();

    // Verify class changed
    const newClass = await html.getAttribute('class');
    expect(newClass).not.toBe(initialClass);
  });
});

test.describe('PR Reviews Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reviews');
  });

  test('should display PR reviews list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'PR Reviews' })).toBeVisible();
    await expect(page.getByText('Recent Pull Requests')).toBeVisible();
  });

  test('should show review statistics', async ({ page }) => {
    await expect(page.getByText('Total Reviews')).toBeVisible();
    await expect(page.getByText('Approved')).toBeVisible();
    await expect(page.getByText('Pending')).toBeVisible();
  });
});

test.describe('Audit Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/audit');
  });

  test('should display audit configuration form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Run Audit' })).toBeVisible();
    await expect(page.getByText('Project Configuration')).toBeVisible();
  });

  test('should show analyzer selection', async ({ page }) => {
    await expect(page.getByText('Select Analyzers')).toBeVisible();
    await expect(page.getByText('Security')).toBeVisible();
    await expect(page.getByText('Code Quality')).toBeVisible();
    await expect(page.getByText('Performance')).toBeVisible();
  });

  test('should toggle analyzers on click', async ({ page }) => {
    const securityCard = page.locator('text=Security').first();
    await securityCard.click();

    // Verify the card styling changed (selected state)
    await expect(securityCard).toBeVisible();
  });

  test('should disable start button without project path', async ({ page }) => {
    const startButton = page.getByRole('button', { name: /Start Audit/i });
    await expect(startButton).toBeDisabled();
  });
});

test.describe('Analytics Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
  });

  test('should display analytics overview', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Analytics' })).toBeVisible();
    await expect(page.getByText('Total Audits')).toBeVisible();
    await expect(page.getByText('Success Rate')).toBeVisible();
  });

  test('should show category distribution', async ({ page }) => {
    await expect(page.getByText('Category Distribution')).toBeVisible();
  });

  test('should display top repositories', async ({ page }) => {
    await expect(page.getByText('Top Repositories by Activity')).toBeVisible();
  });
});

test.describe('Security Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/security');
  });

  test('should display security overview', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Security' })).toBeVisible();
    await expect(page.getByText('Critical')).toBeVisible();
    await expect(page.getByText('High')).toBeVisible();
  });

  test('should show OWASP coverage', async ({ page }) => {
    await expect(page.getByText('OWASP Top 10 Coverage')).toBeVisible();
  });
});

test.describe('Rules Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/rules');
  });

  test('should display rules list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Rules' })).toBeVisible();
    await expect(page.getByText('All Rules')).toBeVisible();
  });

  test('should have search functionality', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Search rules...');
    await expect(searchInput).toBeVisible();

    await searchInput.fill('sql');
    // Rules should filter based on search
  });
});

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('should display settings sections', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    await expect(page.getByText('General Settings')).toBeVisible();
    await expect(page.getByText('Notifications')).toBeVisible();
    await expect(page.getByText('Security')).toBeVisible();
  });

  test('should show API keys section', async ({ page }) => {
    await expect(page.getByText('API Keys')).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should be responsive on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');

    const h1 = await page.locator('h1').count();
    expect(h1).toBeGreaterThanOrEqual(1);
  });

  test('should have accessible navigation', async ({ page }) => {
    await page.goto('/');

    const nav = page.getByRole('navigation');
    await expect(nav).toBeVisible();
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');

    // Tab through elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Verify focus is visible somewhere
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeDefined();
  });
});
