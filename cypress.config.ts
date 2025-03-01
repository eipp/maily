import { defineConfig } from 'cypress';

export default defineConfig({
  projectId: 'maily-e2e',

  e2e: {
    baseUrl: 'http://localhost:3000',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/e2e.ts',
    videosFolder: 'cypress/videos',
    screenshotsFolder: 'cypress/screenshots',
    viewportWidth: 1280,
    viewportHeight: 720,
    chromeWebSecurity: false,
    experimentalRunAllSpecs: true,
    experimentalMemoryManagement: true,

    setupNodeEvents(on, config) {
      // Register event listeners for test events
      on('before:browser:launch', (browser, launchOptions) => {
        // Optimize Chrome performance for CI environments
        if (browser.name === 'chrome' && browser.isHeadless) {
          launchOptions.args.push('--disable-gpu');
          launchOptions.args.push('--disable-dev-shm-usage');
          launchOptions.args.push('--disable-extensions');
          launchOptions.args.push('--no-sandbox');
          launchOptions.args.push('--disable-background-timer-throttling');
          launchOptions.args.push('--disable-backgrounding-occluded-windows');
          launchOptions.args.push('--disable-renderer-backgrounding');
        }

        return launchOptions;
      });

      // Implement custom logging
      on('task', {
        log(message) {
          console.log(message);
          return null;
        },
      });

      // Import environment variables
      const envPath = process.env.CYPRESS_ENV_FILE || '.env.test';
      try {
        const dotenv = require('dotenv');
        const fs = require('fs');

        if (fs.existsSync(envPath)) {
          const envConfig = dotenv.parse(fs.readFileSync(envPath));
          config.env = { ...config.env, ...envConfig };
        }
      } catch (error) {
        console.error('Error loading environment variables:', error);
      }

      // Set environment-specific configuration
      if (process.env.CI) {
        config.baseUrl = process.env.CYPRESS_BASE_URL || 'http://localhost:3000';
        config.video = true;
        config.screenshotOnRunFailure = true;
      }

      return config;
    },
  },

  component: {
    specPattern: 'cypress/component/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/component.ts',
    indexHtmlFile: 'cypress/support/component-index.html',
    devServer: {
      framework: 'next',
      bundler: 'webpack',
    },
  },

  retries: {
    runMode: 2,
    openMode: 0,
  },

  defaultCommandTimeout: 10000,
  requestTimeout: 10000,
  responseTimeout: 30000,
  pageLoadTimeout: 60000,
});
