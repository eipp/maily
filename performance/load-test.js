import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 20 },   // Ramp up to 20 users
    { duration: '3m', target: 20 },   // Stay at 20 users
    { duration: '1m', target: 50 },   // Ramp up to 50 users
    { duration: '3m', target: 50 },   // Stay at 50 users
    { duration: '1m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% of requests must complete below 200ms
    'http_req_duration{type:staticAsset}': ['p(95)<100'],  // Static assets should be faster
    errors: ['rate<0.1'],  // Error rate must be less than 10%
  },
};

const BASE_URL = 'http://localhost:8000';

export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Health check
  const healthCheck = http.get(`${BASE_URL}/health`);
  check(healthCheck, {
    'health check status is 200': (r) => r.status === 200,
  });

  // API endpoints test
  const endpoints = [
    { method: 'GET', path: '/api/campaigns', tag: { type: 'api' } },
    { method: 'GET', path: '/api/analytics', tag: { type: 'api' } },
    { method: 'GET', path: '/static/main.js', tag: { type: 'staticAsset' } },
    { method: 'GET', path: '/static/style.css', tag: { type: 'staticAsset' } },
  ];

  endpoints.forEach(({ method, path, tag }) => {
    const response = http.request(method, `${BASE_URL}${path}`, null, {
      ...params,
      tags: tag,
    });

    check(response, {
      'status is 200': (r) => r.status === 200,
      'response time OK': (r) => r.timings.duration < 200,
    }) || errorRate.add(1);
  });

  // Simulate user think time
  sleep(Math.random() * 3 + 2); // Random sleep between 2-5 seconds
}

// Custom metrics setup
const customMetrics = {
  cpu_usage: new Rate('cpu_usage'),
  memory_usage: new Rate('memory_usage'),
  db_connections: new Rate('db_connections'),
};

// Lifecycle hooks
export function setup() {
  // Perform setup tasks (e.g., data preparation)
  const response = http.get(`${BASE_URL}/health`);
  if (response.status !== 200) {
    throw new Error('Service is not healthy before starting the test');
  }
}

export function teardown(data) {
  // Cleanup after tests
  console.log('Test completed. Cleaning up...');
} 