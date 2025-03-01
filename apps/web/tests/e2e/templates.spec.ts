import { test, expect } from '@playwright/test';

test.describe('Templates Page', () => {
  test('should navigate to the templates page', async ({ page }) => {
    // Navigate to the templates page
    await page.goto('/templates');

    // Check if the page title is correct
    await expect(page).toHaveTitle(/Templates | Maily/);

    // Check if the page heading is rendered
    const heading = page.locator('h1:has-text("Templates")');
    await expect(heading).toBeVisible();

    // Check if the page description is rendered
    const description = page.locator('p:has-text("Create and manage your email templates")');
    await expect(description).toBeVisible();

    // Check if the "Create New Template" button is rendered
    const createButton = page.locator('a:has-text("Create New Template")');
    await expect(createButton).toBeVisible();
  });

  test('should navigate to template details when clicking on a template', async ({ page }) => {
    // Navigate to the templates page
    await page.goto('/templates');

    // Wait for the templates to load
    await page.waitForSelector('.bg-white.dark\\:bg-gray-800');

    // Click on the first template (if available)
    const firstTemplate = page.locator('.bg-white.dark\\:bg-gray-800 a').first();

    // If there are templates, click on the first one and check navigation
    if (await firstTemplate.count() > 0) {
      // Get the template ID from the href attribute
      const href = await firstTemplate.getAttribute('href');
      const templateId = href?.split('/').pop();

      await firstTemplate.click();

      // Check if we navigated to the template details page
      await expect(page).toHaveURL(new RegExp(`/templates/${templateId}`));
    }
  });
});
