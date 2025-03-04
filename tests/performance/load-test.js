import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const errorRate = new Rate('error_rate');
const apiLatency = new Trend('api_latency');
const frontendLatency = new Trend('frontend_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp up to 50 users over 1 minute
    { duration: '3m', target: 50 },   // Stay at 50 users for 3 minutes
    { duration: '1m', target: 100 },  // Ramp up to 100 users over 1 minute
    { duration: '5m', target: 100 },  // Stay at 100 users for 5 minutes
    { duration: '1m', target: 0 },    // Ramp down to 0 users over 1 minute
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'], // 95% of requests should be below 500ms
    'error_rate': ['rate<0.1'],         // Error rate should be less than 10%
    'api_latency': ['p(95)<300'],       // 95% of API requests should be below 300ms
    'frontend_latency': ['p(95)<800'],  // 95% of frontend requests should be below 800ms
  },
};

// Shared parameters
const BASE_URL = __ENV.BASE_URL || 'https://staging.justmaily.com';
const API_URL = `${BASE_URL}/api`;

// Helper function to generate test data
function generateTestData() {
  return {
    email: `test-${randomString(8)}@example.com`,
    subject: `Test Subject ${randomString(5)}`,
    content: `This is a test email content with some random text: ${randomString(20)}`,
    campaignName: `Test Campaign ${randomString(8)}`,
  };
}

// Main test function
export default function() {
  const testData = generateTestData();

  // Test frontend load time
  const frontendResponse = http.get(BASE_URL);
  check(frontendResponse, {
    'frontend status is 200': (r) => r.status === 200,
    'frontend has correct title': (r) => r.body.includes('<title>Maily</title>'),
  });
  frontendLatency.add(frontendResponse.timings.duration);
  errorRate.add(frontendResponse.status !== 200);

  // Test API health endpoint
  const healthResponse = http.get(`${API_URL}/health`);
  check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
    'health check is ok': (r) => r.json('status') === 'ok',
  });
  apiLatency.add(healthResponse.timings.duration);
  errorRate.add(healthResponse.status !== 200);

  // Test authentication (simulated)
  const authResponse = http.post(`${API_URL}/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'password123',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  check(authResponse, {
    'auth status is 200': (r) => r.status === 200,
    'auth returns token': (r) => r.json('token') !== undefined,
  });
  apiLatency.add(authResponse.timings.duration);
  errorRate.add(authResponse.status !== 200);

  // Extract token for subsequent requests
  const token = authResponse.json('token');
  const authHeaders = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  // Test campaign creation
  const createCampaignResponse = http.post(`${API_URL}/campaigns`, JSON.stringify({
    name: testData.campaignName,
    subject: testData.subject,
    content: testData.content,
    sendAt: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
  }), {
    headers: authHeaders,
  });
  check(createCampaignResponse, {
    'create campaign status is 201': (r) => r.status === 201,
    'campaign has id': (r) => r.json('id') !== undefined,
  });
  apiLatency.add(createCampaignResponse.timings.duration);
  errorRate.add(createCampaignResponse.status !== 201);

  // Extract campaign ID
  const campaignId = createCampaignResponse.json('id');

  // Test campaign retrieval
  const getCampaignResponse = http.get(`${API_URL}/campaigns/${campaignId}`, {
    headers: authHeaders,
  });
  check(getCampaignResponse, {
    'get campaign status is 200': (r) => r.status === 200,
    'campaign has correct name': (r) => r.json('name') === testData.campaignName,
  });
  apiLatency.add(getCampaignResponse.timings.duration);
  errorRate.add(getCampaignResponse.status !== 200);

  // Test AI subject line optimization
  const optimizeSubjectResponse = http.post(`${API_URL}/ai/optimize-subject`, JSON.stringify({
    subject: testData.subject,
    audience: 'general',
  }), {
    headers: authHeaders,
  });
  check(optimizeSubjectResponse, {
    'optimize subject status is 200': (r) => r.status === 200,
    'optimized subject exists': (r) => r.json('optimizedSubject') !== undefined,
  });
  apiLatency.add(optimizeSubjectResponse.timings.duration);
  errorRate.add(optimizeSubjectResponse.status !== 200);

  // Test campaign list retrieval
  const listCampaignsResponse = http.get(`${API_URL}/campaigns`, {
    headers: authHeaders,
  });
  check(listCampaignsResponse, {
    'list campaigns status is 200': (r) => r.status === 200,
    'campaigns is an array': (r) => Array.isArray(r.json('campaigns')),
  });
  apiLatency.add(listCampaignsResponse.timings.duration);
  errorRate.add(listCampaignsResponse.status !== 200);

  // Pause between iterations
  sleep(1);
}
