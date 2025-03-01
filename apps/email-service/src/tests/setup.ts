/**
 * Jest Test Setup File
 *
 * This file runs before each test file and can be used to set up the
 * global test environment, add custom matchers, or mock external services.
 */

// Import jest-extended for additional matchers
import 'jest-extended';

// Mock environment variables
process.env.NODE_ENV = 'test';
process.env.PORT = '8081';
process.env.DB_HOST = 'localhost';
process.env.DB_PORT = '5432';
process.env.DB_USERNAME = 'test';
process.env.DB_PASSWORD = 'test';
process.env.DB_DATABASE = 'email_service_test';
process.env.REDIS_HOST = 'localhost';
process.env.REDIS_PORT = '6379';
process.env.EMAIL_PROVIDER_TYPE = 'resend';
process.env.EMAIL_PROVIDER_API_KEY = 'test_api_key';
process.env.RATE_LIMIT_RESEND = '1000';

// Global setup
beforeAll(() => {
  // Add any one-time setup for all tests here
  console.log('Starting test suite');
});

// Global teardown
afterAll(() => {
  // Add any one-time teardown for all tests here
  console.log('Test suite completed');
});

// Per-test setup
beforeEach(() => {
  // Reset any shared state before each test
  jest.clearAllMocks();
});

// Add custom matchers
expect.extend({
  toBeEmailSuccess(received) {
    const pass = received &&
                 received.success === true &&
                 typeof received.messageId === 'string';

    if (pass) {
      return {
        message: () => `expected ${received} not to be a successful email result`,
        pass: true
      };
    } else {
      return {
        message: () => `expected ${received} to be a successful email result`,
        pass: false
      };
    }
  }
});

// Extend global Jest types for custom matchers
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeEmailSuccess(): R;
    }
  }
}
