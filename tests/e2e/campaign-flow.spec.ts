import { test, expect } from '@playwright/test';

/**
 * End-to-end test for the campaign creation and sending flow.
 * Tests the complete user journey from login to campaign creation to sending.
 */
test('campaign creation and sending flow', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'testpassword');
  await page.click('button[type="submit"]');

  // Verify successful login
  await expect(page).toHaveURL(/\/dashboard/);

  // Navigate to campaign creation
  await page.click('a[href="/campaigns/new"]');

  // Verify on campaign creation page
  await expect(page).toHaveURL(/\/campaigns\/new/);

  // Fill campaign details
  await page.fill('input[name="name"]', 'E2E Test Campaign');
  await page.fill('input[name="subject"]', 'E2E Test Subject');

  // Choose template
  await page.click('button:text("Choose Template")');
  await page.waitForSelector('div[data-testid="template-list"]');
  await page.click('div[data-template-id="announcement"]');

  // Wait for editor to load with template
  await page.waitForSelector('div[data-testid="email-editor"]');

  // Customize content in editor
  await page.click('div[data-element="headline"]');
  await page.waitForSelector('div[contenteditable="true"]');
  await page.fill('div[contenteditable="true"]', 'Automated E2E Test Headline');

  // Add more content to body
  await page.click('div[data-element="body"]');
  await page.keyboard.type('This is an automated test of the email campaign system. Please ignore this message.');

  // Upload an image (if the feature exists)
  try {
    // Only try this if the feature exists
    await page.click('button[data-testid="add-image"]');
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('button:text("Upload Image")');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles('./tests/fixtures/test-image.png');
    await page.waitForSelector('img[alt="Uploaded image"]');
  } catch (e) {
    // Log but continue if the image upload section doesn't exist
    console.log('Image upload section not found, continuing test...');
  }

  // Select recipients
  await page.click('button:text("Select Recipients")');
  await page.waitForSelector('div[data-testid="recipient-selector"]');

  // Select a test segment
  await page.click('input[type="checkbox"][name="segment-1"]');
  await page.click('button:text("Confirm")');

  // Verify recipients are selected
  await expect(page.locator('div[data-testid="selected-recipients"]')).toBeVisible();

  // Save campaign
  await page.click('button:text("Save Campaign")');

  // Verify campaign was created
  await expect(page.locator('div.alert-success')).toContainText('Campaign created successfully');

  // Verify we're on the campaign detail page
  await expect(page).toHaveURL(/\/campaigns\/[\w-]+$/);

  // Preview the campaign
  await page.click('button:text("Preview")');
  await page.waitForSelector('iframe[data-testid="preview-frame"]');

  // Close preview
  await page.click('button:has-text("Close Preview")');

  // Start campaign
  await page.click('button:text("Start Campaign")');

  // Confirm sending
  await page.waitForSelector('div[role="dialog"]');
  await page.click('button:text("Confirm")');

  // Verify campaign started
  await expect(page.locator('div.campaign-status')).toContainText('Sending');

  // Wait for campaign to complete (or use test hooks to accelerate)
  await page.waitForSelector('div.campaign-status:text("Completed")', { timeout: 30000 });

  // Navigate to analytics
  await page.click('a:text("Analytics")');

  // Verify analytics are being collected
  await page.waitForSelector('div.analytics-summary');
  await expect(page.locator('div.analytics-summary')).toBeVisible();
  await expect(page.locator('div.sent-count')).not.toContainText('0');

  // Test email preview in analytics
  await page.click('button:text("View Email")');
  await page.waitForSelector('iframe[data-testid="email-preview"]');

  // Verify our custom content is visible in the preview
  const frameContent = await page.frameLocator('iframe[data-testid="email-preview"]').locator('body').textContent();
  expect(frameContent).toContain('Automated E2E Test Headline');

  // Close preview
  await page.click('button:has-text("Close")');

  // Navigate back to dashboard
  await page.click('a:text("Dashboard")');
  await expect(page).toHaveURL(/\/dashboard/);

  // Verify campaign appears in recent campaigns list
  await expect(page.locator('table.recent-campaigns')).toContainText('E2E Test Campaign');
});
