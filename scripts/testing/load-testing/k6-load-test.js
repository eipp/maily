import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.1.0/index.js';

// Custom metrics
const successRate = new Rate('success_rate');
const apiCallDuration = new Trend('api_call_duration');
const failedRequests = new Counter('failed_requests');

// Test configuration
export const options = {
  // Defines the shape of the load test
  scenarios: {
    // Simulates normal workload
    average_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },  // Ramp up to 50 users
        { duration: '5m', target: 50 },  // Stay at 50 users for 5 minutes
        { duration: '2m', target: 0 },   // Ramp down to 0 users
      ],
      gracefulRampDown: '30s',
    },
    // Simulates peak traffic
    peak_load: {
      executor: 'ramping-vus',
      startTime: '10m',  // Starts after the average load scenario
      startVUs: 0,
      stages: [
        { duration: '3m', target: 200 },  // Ramp up to 200 users
        { duration: '5m', target: 200 },  // Stay at 200 users for 5 minutes
        { duration: '2m', target: 0 },    // Ramp down to 0 users
      ],
      gracefulRampDown: '30s',
    },
    // Simulates spike traffic
    spike_test: {
      executor: 'ramping-vus',
      startTime: '20m',  // Starts after the peak load scenario
      startVUs: 0,
      stages: [
        { duration: '30s', target: 300 },  // Quickly ramp up to 300 users
        { duration: '1m', target: 300 },   // Stay at 300 users for 1 minute
        { duration: '30s', target: 0 },    // Quickly ramp down to 0 users
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    // Define performance thresholds
    http_req_duration: ['p(95)<500', 'p(99)<1500'],  // 95% of requests should complete within 500ms, 99% within 1.5s
    http_req_failed: ['rate<0.01'],                  // Less than 1% of requests should fail
    'success_rate': ['rate>0.95'],                   // Success rate should be above 95%
    'api_call_duration{name:login}': ['p(95)<700'],  // 95% of login requests should complete within 700ms
    'api_call_duration{name:get_campaigns}': ['p(95)<600'],  // 95% of campaign list requests should complete within 600ms
    'api_call_duration{name:send_email}': ['p(95)<800'],     // 95% of email sending requests should complete within 800ms
  },
};

// Execution context variables
const BASE_URL = __ENV.TARGET_URL || 'https://api.mailyapp.com';
const API_VERSION = 'v1';
const API_URL = `${BASE_URL}/${API_VERSION}`;

// User pool for authentication
const users = [
  { email: 'loadtest1@example.com', password: 'Password123!' },
  { email: 'loadtest2@example.com', password: 'Password123!' },
  { email: 'loadtest3@example.com', password: 'Password123!' },
  { email: 'loadtest4@example.com', password: 'Password123!' },
  { email: 'loadtest5@example.com', password: 'Password123!' },
];

// Main test function
export default function () {
  // Select a random user
  const user = users[Math.floor(Math.random() * users.length)];
  let token = null;
  let userCampaigns = [];
  
  // Common headers
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  
  group('Authentication', function () {
    // Login request
    const loginStart = new Date();
    const loginRes = http.post(`${API_URL}/auth/login`, JSON.stringify({
      email: user.email,
      password: user.password,
    }), { headers });
    
    apiCallDuration.add(new Date() - loginStart, { name: 'login' });
    
    // Check if login was successful
    const loginSuccess = check(loginRes, {
      'login status is 200': (r) => r.status === 200,
      'has access token': (r) => r.json('data.token') !== undefined,
    });
    
    successRate.add(loginSuccess);
    
    if (loginSuccess) {
      token = loginRes.json('data.token');
      headers['Authorization'] = `Bearer ${token}`;
    } else {
      failedRequests.add(1);
      console.log(`Login failed: ${loginRes.status} ${loginRes.body}`);
      return;
    }
    
    sleep(1);
  });
  
  group('View Campaigns', function () {
    if (!token) {
      failedRequests.add(1);
      return;
    }
    
    // Get user's campaigns
    const campaignsStart = new Date();
    const campaignsRes = http.get(`${API_URL}/campaigns`, { headers });
    
    apiCallDuration.add(new Date() - campaignsStart, { name: 'get_campaigns' });
    
    // Check campaigns response
    const campaignsSuccess = check(campaignsRes, {
      'campaigns status is 200': (r) => r.status === 200,
      'campaigns data is array': (r) => Array.isArray(r.json('data.campaigns')),
    });
    
    successRate.add(campaignsSuccess);
    
    if (campaignsSuccess) {
      userCampaigns = campaignsRes.json('data.campaigns');
    } else {
      failedRequests.add(1);
    }
    
    sleep(2);
  });
  
  group('Email Operations', function () {
    if (!token) {
      failedRequests.add(1);
      return;
    }
    
    // Create a draft email
    const emailData = {
      subject: `Load Test Email ${randomString(8)}`,
      body: `This is a load test email created at ${new Date().toISOString()}.\n\nThis is just a test, please ignore.`,
      recipients: ['loadtest-recipient@example.com'],
      type: 'regular',
    };
    
    const createEmailStart = new Date();
    const createEmailRes = http.post(`${API_URL}/emails/draft`, JSON.stringify(emailData), { headers });
    
    apiCallDuration.add(new Date() - createEmailStart, { name: 'create_email' });
    
    // Check email creation response
    const createEmailSuccess = check(createEmailRes, {
      'create email status is 201': (r) => r.status === 201,
      'has email id': (r) => r.json('data.id') !== undefined,
    });
    
    successRate.add(createEmailSuccess);
    
    if (createEmailSuccess) {
      const emailId = createEmailRes.json('data.id');
      
      // Send the created email
      const sendEmailStart = new Date();
      const sendEmailRes = http.post(`${API_URL}/emails/${emailId}/send`, '', { headers });
      
      apiCallDuration.add(new Date() - sendEmailStart, { name: 'send_email' });
      
      // Check send email response
      const sendEmailSuccess = check(sendEmailRes, {
        'send email status is 200': (r) => r.status === 200,
        'email sent successfully': (r) => r.json('success') === true,
      });
      
      successRate.add(sendEmailSuccess);
      
      if (!sendEmailSuccess) {
        failedRequests.add(1);
      }
    } else {
      failedRequests.add(1);
    }
    
    sleep(3);
  });
  
  group('Analytics', function () {
    if (!token) {
      failedRequests.add(1);
      return;
    }
    
    // Get analytics data
    const analyticsStart = new Date();
    const analyticsRes = http.get(`${API_URL}/analytics/overview?timeRange=7d`, { headers });
    
    apiCallDuration.add(new Date() - analyticsStart, { name: 'get_analytics' });
    
    // Check analytics response
    const analyticsSuccess = check(analyticsRes, {
      'analytics status is 200': (r) => r.status === 200,
      'has analytics data': (r) => r.json('data') !== undefined,
    });
    
    successRate.add(analyticsSuccess);
    
    if (!analyticsSuccess) {
      failedRequests.add(1);
    }
    
    sleep(1);
  });
  
  group('Search', function () {
    if (!token) {
      failedRequests.add(1);
      return;
    }
    
    // Search for contacts or emails
    const searchQuery = `test-${Math.floor(Math.random() * 1000)}`;
    
    const searchStart = new Date();
    const searchRes = http.get(`${API_URL}/search?q=${searchQuery}`, { headers });
    
    apiCallDuration.add(new Date() - searchStart, { name: 'search' });
    
    // Check search response
    const searchSuccess = check(searchRes, {
      'search status is 200': (r) => r.status === 200,
    });
    
    successRate.add(searchSuccess);
    
    if (!searchSuccess) {
      failedRequests.add(1);
    }
    
    sleep(1);
  });
  
  // Random sleep between 1-5 seconds before next iteration
  sleep(Math.random() * 4 + 1);
}
