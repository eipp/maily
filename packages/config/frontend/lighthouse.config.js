module.exports = {
  ci: {
    collect: {
      numberOfRuns: 3,
      startServerCommand: 'cd maily-frontend && npm run start',
      url: ['http://localhost:3000'],
      settings: {
        preset: 'desktop',
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
        },
      },
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        'first-contentful-paint': ['error', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['error', { maxNumericValue: 200 }],
        'speed-index': ['error', { maxNumericValue: 3000 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
    budgets: [
      {
        path: '/*',
        timings: [
          {
            metric: 'interactive',
            budget: 3000,
          },
          {
            metric: 'first-contentful-paint',
            budget: 2000,
          },
        ],
        resourceSizes: [
          {
            resourceType: 'script',
            budget: 300,
          },
          {
            resourceType: 'total',
            budget: 1000,
          },
        ],
        resourceCounts: [
          {
            resourceType: 'third-party',
            budget: 10,
          },
        ],
      },
    ],
  },
};
