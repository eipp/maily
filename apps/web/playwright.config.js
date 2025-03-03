// @ts-check

/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  testDir: './components/ui/__tests__',
  timeout: 30000,
  expect: {
    toMatchSnapshot: { threshold: 0.2 }, // 0.2% pixel difference tolerance
  },
  use: {
    browserName: 'chromium',
    viewport: { width: 1280, height: 720 },
    screenshot: 'on',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    port: 3000,
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
  },
  retries: process.env.CI ? 2 : 0,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'playwright-report/results.json' }]
  ],
  // Run all tests in parallel
  fullyParallel: true,
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
};

module.exports = config;