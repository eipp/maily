/**
 * DEPRECATED: Jest configuration
 * 
 * This file is deprecated. Please use Vitest instead.
 * See vitest.config.ts for the current test configuration.
 */

console.warn('\x1b[33m%s\x1b[0m', 
  'WARNING: Jest is deprecated in this project. Please use Vitest instead.\n' +
  'Run tests with "npm test" which uses Vitest, or update your command to use Vitest directly.\n' +
  'See CLAUDE.md for more information on standardized testing approaches.'
);

// Export a minimal configuration to prevent errors but encourage migration
module.exports = {
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
};