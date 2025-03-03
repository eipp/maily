#!/bin/bash
# load-testing.sh
# Script to perform load testing for Maily

set -e

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
  echo "Error: k6 is not installed. Please install it first."
  echo "Visit: https://k6.io/docs/getting-started/installation/"
  exit 1
fi

# Default values
API_BASE_URL="https://api.maily.com"
TEST_DURATION="5m"
VIRTUAL_USERS=50
RAMP_UP_TIME="30s"
RAMP_DOWN_TIME="30s"
OUTPUT_FORMAT="json"
OUTPUT_FILE="load-test-results.json"
TEST_TYPE="api"
ENVIRONMENT="production"
THRESHOLD_HTTP_REQ_FAILED="1"
THRESHOLD_HTTP_REQ_DURATION_P95="500"
THRESHOLD_HTTP_REQ_DURATION_P99="1000"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --api-base-url)
      API_BASE_URL="$2"
      shift 2
      ;;
    --test-duration)
      TEST_DURATION="$2"
      shift 2
      ;;
    --virtual-users)
      VIRTUAL_USERS="$2"
      shift 2
      ;;
    --ramp-up-time)
      RAMP_UP_TIME="$2"
      shift 2
      ;;
    --ramp-down-time)
      RAMP_DOWN_TIME="$2"
      shift 2
      ;;
    --output-format)
      OUTPUT_FORMAT="$2"
      shift 2
      ;;
    --output-file)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --test-type)
      TEST_TYPE="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --threshold-http-req-failed)
      THRESHOLD_HTTP_REQ_FAILED="$2"
      shift 2
      ;;
    --threshold-http-req-duration-p95)
      THRESHOLD_HTTP_REQ_DURATION_P95="$2"
      shift 2
      ;;
    --threshold-http-req-duration-p99)
      THRESHOLD_HTTP_REQ_DURATION_P99="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create a temporary directory for test scripts
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Create API load test script
if [ "$TEST_TYPE" = "api" ]; then
  echo "Creating API load test script..."
  
  cat > $TEMP_DIR/api-load-test.js << EOF
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { SharedArray } from 'k6/data';

// Custom metrics
const errorRate = new Rate('error_rate');
const authLatency = new Trend('auth_latency');
const campaignLatency = new Trend('campaign_latency');
const emailLatency = new Trend('email_latency');
const analyticsLatency = new Trend('analytics_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '${RAMP_UP_TIME}', target: ${VIRTUAL_USERS} },
    { duration: '${TEST_DURATION}', target: ${VIRTUAL_USERS} },
    { duration: '${RAMP_DOWN_TIME}', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<${THRESHOLD_HTTP_REQ_FAILED}%'],
    http_req_duration: ['p(95)<${THRESHOLD_HTTP_REQ_DURATION_P95}', 'p(99)<${THRESHOLD_HTTP_REQ_DURATION_P99}'],
    'auth_latency': ['p(95)<300'],
    'campaign_latency': ['p(95)<500'],
    'email_latency': ['p(95)<400'],
    'analytics_latency': ['p(95)<600'],
  },
};

// Simulated user data
const users = new SharedArray('users', function() {
  return [
    { email: 'user1@example.com', password: 'password1' },
    { email: 'user2@example.com', password: 'password2' },
    { email: 'user3@example.com', password: 'password3' },
    { email: 'user4@example.com', password: 'password4' },
    { email: 'user5@example.com', password: 'password5' },
  ];
});

// Simulated campaign data
const campaigns = new SharedArray('campaigns', function() {
  return [
    { name: 'Welcome Campaign', description: 'Welcome new users' },
    { name: 'Newsletter', description: 'Monthly newsletter' },
    { name: 'Product Update', description: 'New features announcement' },
    { name: 'Promotional Offer', description: 'Special discount' },
    { name: 'Re-engagement', description: 'Bring back inactive users' },
  ];
});

// Main test function
export default function() {
  const baseUrl = '${API_BASE_URL}';
  const user = users[Math.floor(Math.random() * users.length)];
  let authToken;
  
  // Step 1: Authentication
  const authStartTime = new Date();
  const loginRes = http.post(\`\${baseUrl}/auth/login\`, JSON.stringify({
    email: user.email,
    password: user.password,
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  authLatency.add(new Date() - authStartTime);
  
  const authSuccess = check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'has auth token': (r) => r.json('token') !== undefined,
  });
  
  errorRate.add(!authSuccess);
  
  if (authSuccess) {
    authToken = loginRes.json('token');
    
    // Step 2: Get campaigns
    const campaignStartTime = new Date();
    const campaignsRes = http.get(\`\${baseUrl}/api/campaigns\`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': \`Bearer \${authToken}\`,
      },
    });
    
    campaignLatency.add(new Date() - campaignStartTime);
    
    const campaignsSuccess = check(campaignsRes, {
      'campaigns status is 200': (r) => r.status === 200,
      'has campaigns data': (r) => Array.isArray(r.json()),
    });
    
    errorRate.add(!campaignsSuccess);
    
    // Step 3: Create a campaign
    const campaign = campaigns[Math.floor(Math.random() * campaigns.length)];
    const createCampaignRes = http.post(\`\${baseUrl}/api/campaigns\`, JSON.stringify({
      name: campaign.name,
      description: campaign.description,
      audience: {
        filters: [
          { field: 'country', operator: 'equals', value: 'US' }
        ]
      },
      template: {
        subject: 'Test Email',
        body: '<p>This is a test email</p>'
      },
      schedule: {
        sendAt: new Date(Date.now() + 86400000).toISOString()
      }
    }), {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': \`Bearer \${authToken}\`,
      },
    });
    
    const createCampaignSuccess = check(createCampaignRes, {
      'create campaign status is 201': (r) => r.status === 201,
      'has campaign id': (r) => r.json('id') !== undefined,
    });
    
    errorRate.add(!createCampaignSuccess);
    
    if (createCampaignSuccess) {
      const campaignId = createCampaignRes.json('id');
      
      // Step 4: Get campaign details
      const getCampaignRes = http.get(\`\${baseUrl}/api/campaigns/\${campaignId}\`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': \`Bearer \${authToken}\`,
        },
      });
      
      const getCampaignSuccess = check(getCampaignRes, {
        'get campaign status is 200': (r) => r.status === 200,
        'campaign has correct id': (r) => r.json('id') === campaignId,
      });
      
      errorRate.add(!getCampaignSuccess);
    }
    
    // Step 5: Get email templates
    const emailStartTime = new Date();
    const templatesRes = http.get(\`\${baseUrl}/api/email-templates\`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': \`Bearer \${authToken}\`,
      },
    });
    
    emailLatency.add(new Date() - emailStartTime);
    
    const templatesSuccess = check(templatesRes, {
      'templates status is 200': (r) => r.status === 200,
      'has templates data': (r) => Array.isArray(r.json()),
    });
    
    errorRate.add(!templatesSuccess);
    
    // Step 6: Get analytics
    const analyticsStartTime = new Date();
    const analyticsRes = http.get(\`\${baseUrl}/api/analytics/dashboard\`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': \`Bearer \${authToken}\`,
      },
    });
    
    analyticsLatency.add(new Date() - analyticsStartTime);
    
    const analyticsSuccess = check(analyticsRes, {
      'analytics status is 200': (r) => r.status === 200,
      'has analytics data': (r) => r.json() !== undefined,
    });
    
    errorRate.add(!analyticsSuccess);
  }
  
  // Wait between iterations
  sleep(1);
}
EOF
fi

# Create web load test script
if [ "$TEST_TYPE" = "web" ]; then
  echo "Creating web load test script..."
  
  cat > $TEMP_DIR/web-load-test.js << EOF
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const homePageLatency = new Trend('home_page_latency');
const dashboardLatency = new Trend('dashboard_latency');
const campaignsPageLatency = new Trend('campaigns_page_latency');
const analyticsPageLatency = new Trend('analytics_page_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '${RAMP_UP_TIME}', target: ${VIRTUAL_USERS} },
    { duration: '${TEST_DURATION}', target: ${VIRTUAL_USERS} },
    { duration: '${RAMP_DOWN_TIME}', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<${THRESHOLD_HTTP_REQ_FAILED}%'],
    http_req_duration: ['p(95)<${THRESHOLD_HTTP_REQ_DURATION_P95}', 'p(99)<${THRESHOLD_HTTP_REQ_DURATION_P99}'],
    'home_page_latency': ['p(95)<500'],
    'dashboard_latency': ['p(95)<800'],
    'campaigns_page_latency': ['p(95)<700'],
    'analytics_page_latency': ['p(95)<900'],
  },
};

// Main test function
export default function() {
  const baseUrl = '${API_BASE_URL}'.replace('api.', 'app.');
  
  // Step 1: Load home page
  const homeStartTime = new Date();
  const homeRes = http.get(baseUrl);
  homePageLatency.add(new Date() - homeStartTime);
  
  const homeSuccess = check(homeRes, {
    'home page status is 200': (r) => r.status === 200,
    'home page has correct title': (r) => r.body.includes('<title>Maily</title>'),
  });
  
  errorRate.add(!homeSuccess);
  
  // Step 2: Load dashboard page
  const dashboardStartTime = new Date();
  const dashboardRes = http.get(\`\${baseUrl}/dashboard\`);
  dashboardLatency.add(new Date() - dashboardStartTime);
  
  const dashboardSuccess = check(dashboardRes, {
    'dashboard page status is 200': (r) => r.status === 200,
    'dashboard page has correct content': (r) => r.body.includes('Dashboard'),
  });
  
  errorRate.add(!dashboardSuccess);
  
  // Step 3: Load campaigns page
  const campaignsStartTime = new Date();
  const campaignsRes = http.get(\`\${baseUrl}/campaigns\`);
  campaignsPageLatency.add(new Date() - campaignsStartTime);
  
  const campaignsSuccess = check(campaignsRes, {
    'campaigns page status is 200': (r) => r.status === 200,
    'campaigns page has correct content': (r) => r.body.includes('Campaigns'),
  });
  
  errorRate.add(!campaignsSuccess);
  
  // Step 4: Load analytics page
  const analyticsStartTime = new Date();
  const analyticsRes = http.get(\`\${baseUrl}/analytics\`);
  analyticsPageLatency.add(new Date() - analyticsStartTime);
  
  const analyticsSuccess = check(analyticsRes, {
    'analytics page status is 200': (r) => r.status === 200,
    'analytics page has correct content': (r) => r.body.includes('Analytics'),
  });
  
  errorRate.add(!analyticsSuccess);
  
  // Wait between iterations
  sleep(1);
}
EOF
fi

# Create email service load test script
if [ "$TEST_TYPE" = "email" ]; then
  echo "Creating email service load test script..."
  
  cat > $TEMP_DIR/email-service-load-test.js << EOF
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { SharedArray } from 'k6/data';

// Custom metrics
const errorRate = new Rate('error_rate');
const sendEmailLatency = new Trend('send_email_latency');
const templateRenderLatency = new Trend('template_render_latency');
const emailStatusLatency = new Trend('email_status_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '${RAMP_UP_TIME}', target: ${VIRTUAL_USERS} },
    { duration: '${TEST_DURATION}', target: ${VIRTUAL_USERS} },
    { duration: '${RAMP_DOWN_TIME}', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<${THRESHOLD_HTTP_REQ_FAILED}%'],
    http_req_duration: ['p(95)<${THRESHOLD_HTTP_REQ_DURATION_P95}', 'p(99)<${THRESHOLD_HTTP_REQ_DURATION_P99}'],
    'send_email_latency': ['p(95)<500'],
    'template_render_latency': ['p(95)<300'],
    'email_status_latency': ['p(95)<200'],
  },
};

// Simulated email data
const emails = new SharedArray('emails', function() {
  return [
    { to: 'recipient1@example.com', subject: 'Test Email 1', body: '<p>This is test email 1</p>' },
    { to: 'recipient2@example.com', subject: 'Test Email 2', body: '<p>This is test email 2</p>' },
    { to: 'recipient3@example.com', subject: 'Test Email 3', body: '<p>This is test email 3</p>' },
    { to: 'recipient4@example.com', subject: 'Test Email 4', body: '<p>This is test email 4</p>' },
    { to: 'recipient5@example.com', subject: 'Test Email 5', body: '<p>This is test email 5</p>' },
  ];
});

// Simulated templates
const templates = new SharedArray('templates', function() {
  return [
    { id: 'template1', name: 'Welcome Template' },
    { id: 'template2', name: 'Newsletter Template' },
    { id: 'template3', name: 'Promotional Template' },
    { id: 'template4', name: 'Transactional Template' },
    { id: 'template5', name: 'Notification Template' },
  ];
});

// Main test function
export default function() {
  const baseUrl = '${API_BASE_URL}';
  const email = emails[Math.floor(Math.random() * emails.length)];
  const template = templates[Math.floor(Math.random() * templates.length)];
  
  // Step 1: Send email
  const sendStartTime = new Date();
  const sendRes = http.post(\`\${baseUrl}/api/email\`, JSON.stringify({
    to: email.to,
    subject: email.subject,
    body: email.body,
    isHtml: true,
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  sendEmailLatency.add(new Date() - sendStartTime);
  
  const sendSuccess = check(sendRes, {
    'send email status is 202': (r) => r.status === 202,
    'has email id': (r) => r.json('id') !== undefined,
  });
  
  errorRate.add(!sendSuccess);
  
  if (sendSuccess) {
    const emailId = sendRes.json('id');
    
    // Step 2: Check email status
    const statusStartTime = new Date();
    const statusRes = http.get(\`\${baseUrl}/api/email/\${emailId}/status\`, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    emailStatusLatency.add(new Date() - statusStartTime);
    
    const statusSuccess = check(statusRes, {
      'status check is 200': (r) => r.status === 200,
      'has status field': (r) => r.json('status') !== undefined,
    });
    
    errorRate.add(!statusSuccess);
  }
  
  // Step 3: Render template
  const renderStartTime = new Date();
  const renderRes = http.post(\`\${baseUrl}/api/email/render-template\`, JSON.stringify({
    templateId: template.id,
    data: {
      name: 'Test User',
      company: 'Maily',
      product: 'Email Service',
    },
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  templateRenderLatency.add(new Date() - renderStartTime);
  
  const renderSuccess = check(renderRes, {
    'render template status is 200': (r) => r.status === 200,
    'has rendered content': (r) => r.json('content') !== undefined,
  });
  
  errorRate.add(!renderSuccess);
  
  // Wait between iterations
  sleep(1);
}
EOF
fi

# Run the load test
echo "Running load test..."
if [ "$TEST_TYPE" = "api" ]; then
  k6 run --out $OUTPUT_FORMAT=$OUTPUT_FILE $TEMP_DIR/api-load-test.js
elif [ "$TEST_TYPE" = "web" ]; then
  k6 run --out $OUTPUT_FORMAT=$OUTPUT_FILE $TEMP_DIR/web-load-test.js
elif [ "$TEST_TYPE" = "email" ]; then
  k6 run --out $OUTPUT_FORMAT=$OUTPUT_FILE $TEMP_DIR/email-service-load-test.js
else
  echo "Error: Unknown test type: $TEST_TYPE"
  exit 1
fi

# Generate HTML report if output format is json
if [ "$OUTPUT_FORMAT" = "json" ]; then
  echo "Generating HTML report..."
  
  # Create HTML report template
  cat > $TEMP_DIR/report-template.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Maily Load Test Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 20px;
      background-color: #f5f5f5;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background-color: white;
      padding: 20px;
      border-radius: 5px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
      color: #333;
    }
    .summary {
      display: flex;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }
    .summary-item {
      flex: 1;
      min-width: 200px;
      margin: 10px;
      padding: 15px;
      background-color: #f9f9f9;
      border-radius: 5px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .summary-item h3 {
      margin-top: 0;
    }
    .chart-container {
      margin-bottom: 30px;
    }
    .metrics-table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
    }
    .metrics-table th, .metrics-table td {
      padding: 10px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    .metrics-table th {
      background-color: #f2f2f2;
    }
    .pass {
      color: green;
    }
    .fail {
      color: red;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Maily Load Test Report</h1>
    <p id="test-info">Test run on <span id="test-date"></span> for <span id="test-duration"></span> with <span id="test-vus"></span> virtual users</p>
    
    <div class="summary">
      <div class="summary-item">
        <h3>Total Requests</h3>
        <p id="total-requests"></p>
      </div>
      <div class="summary-item">
        <h3>Failed Requests</h3>
        <p id="failed-requests"></p>
      </div>
      <div class="summary-item">
        <h3>Avg Request Duration</h3>
        <p id="avg-duration"></p>
      </div>
      <div class="summary-item">
        <h3>P95 Request Duration</h3>
        <p id="p95-duration"></p>
      </div>
    </div>
    
    <h2>Response Time</h2>
    <div class="chart-container">
      <canvas id="response-time-chart"></canvas>
    </div>
    
    <h2>Requests Per Second</h2>
    <div class="chart-container">
      <canvas id="rps-chart"></canvas>
    </div>
    
    <h2>Custom Metrics</h2>
    <div class="chart-container">
      <canvas id="custom-metrics-chart"></canvas>
    </div>
    
    <h2>Thresholds</h2>
    <table class="metrics-table" id="thresholds-table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Threshold</th>
          <th>Value</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
      </tbody>
    </table>
    
    <h2>HTTP Metrics</h2>
    <table class="metrics-table" id="http-metrics-table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
      </tbody>
    </table>
  </div>
  
  <script>
    // Load and parse the JSON data
    fetch('LOAD_TEST_RESULTS_JSON')
      .then(response => response.json())
      .then(data => {
        // Fill in test info
        document.getElementById('test-date').textContent = new Date(data.metrics.vus.first_value.time).toLocaleString();
        document.getElementById('test-duration').textContent = formatDuration(data.state.testRunDurationMs);
        document.getElementById('test-vus').textContent = data.metrics.vus.max;
        
        // Fill in summary
        document.getElementById('total-requests').textContent = data.metrics.http_reqs.count;
        document.getElementById('failed-requests').textContent = data.metrics.http_req_failed.fails;
        document.getElementById('avg-duration').textContent = formatDuration(data.metrics.http_req_duration.avg);
        document.getElementById('p95-duration').textContent = formatDuration(data.metrics.http_req_duration.p(95));
        
        // Create response time chart
        const responseTimeCtx = document.getElementById('response-time-chart').getContext('2d');
        new Chart(responseTimeCtx, {
          type: 'line',
          data: {
            labels: data.metrics.http_req_duration.values.map(v => formatTime(v.time)),
            datasets: [{
              label: 'Response Time (ms)',
              data: data.metrics.http_req_duration.values.map(v => v.value),
              borderColor: 'rgba(75, 192, 192, 1)',
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              tension: 0.1
            }]
          },
          options: {
            scales: {
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Duration (ms)'
                }
              },
              x: {
                title: {
                  display: true,
                  text: 'Time'
                }
              }
            }
          }
        });
        
        // Create RPS chart
        const rpsCtx = document.getElementById('rps-chart').getContext('2d');
        new Chart(rpsCtx, {
          type: 'line',
          data: {
            labels: data.metrics.http_reqs.values.map(v => formatTime(v.time)),
            datasets: [{
              label: 'Requests Per Second',
              data: data.metrics.http_reqs.values.map(v => v.value),
              borderColor: 'rgba(54, 162, 235, 1)',
              backgroundColor: 'rgba(54, 162, 235, 0.2)',
              tension: 0.1
            }]
          },
          options: {
            scales: {
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'RPS'
                }
              },
              x: {
                title: {
                  display: true,
                  text: 'Time'
                }
              }
            }
          }
        });
        
        // Create custom metrics chart
        const customMetricsCtx = document.getElementById('custom-metrics-chart').getContext('2d');
        const customMetrics = Object.keys(data.metrics).filter(key => key.endsWith('_latency'));
        
        new Chart(customMetricsCtx, {
          type: 'bar',
          data: {
            labels: customMetrics.map(m => m.replace('_latency', '')),
            datasets: [{
              label: 'P95 Latency (ms)',
              data: customMetrics.map(m => data.metrics[m].p(95)),
              backgroundColor: 'rgba(153, 102, 255, 0.2)',
              borderColor: 'rgba(153, 102, 255, 1)',
              borderWidth: 1
            }]
          },
          options: {
            scales: {
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'P95 Latency (ms)'
                }
              }
            }
          }
        });
        
        // Fill in thresholds table
        const thresholdsTable = document.getElementById('thresholds-table').getElementsByTagName('tbody')[0];
        
        for (const [metric, thresholds] of Object.entries(data.options.thresholds)) {
          for (const threshold of thresholds) {
            const row = thresholdsTable.insertRow();
            
            const metricCell = row.insertCell();
            metricCell.textContent = metric;
            
            const thresholdCell = row.insertCell();
            thresholdCell.textContent = threshold;
            
            const valueCell = row.insertCell();
            let value;
            
            if (metric === 'http_req_failed') {
              value = (data.metrics.http_req_failed.rate * 100).toFixed(2) + '%';
            } else if (metric.includes('p(95)')) {
              const metricName = metric.split('p(95)')[0].trim();
              value = formatDuration(data.metrics[metricName].p(95));
            } else if (metric.includes('p(99)')) {
              const metricName = metric.split('p(99)')[0].trim();
              value = formatDuration(data.metrics[metricName].p(99));
            } else {
              value = 'N/A';
            }
            
            valueCell.textContent = value;
            
            const statusCell = row.insertCell();
            statusCell.textContent = data.root_group.checks.find(c => c.name.includes(threshold)) ? 'PASS' : 'FAIL';
            statusCell.className = statusCell.textContent === 'PASS' ? 'pass' : 'fail';
          }
        }
        
        // Fill in HTTP metrics table
        const httpMetricsTable = document.getElementById('http-metrics-table').getElementsByTagName('tbody')[0];
        
        const httpMetrics = [
          { name: 'Total Requests', value: data.metrics

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done

