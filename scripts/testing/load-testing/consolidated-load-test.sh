#!/bin/bash
# Consolidated Load Testing Script
# Combines functionality from multiple load testing scripts
# Provides a unified interface for all load testing operations

set -e

# Configuration
API_BASE_URL="${API_BASE_URL:-https://api.justmaily.com}"
TEST_DURATION="${TEST_DURATION:-5m}"
VIRTUAL_USERS="${VIRTUAL_USERS:-50}"
RAMP_UP_TIME="${RAMP_UP_TIME:-30s}"
RAMP_DOWN_TIME="${RAMP_DOWN_TIME:-30s}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-json}"
OUTPUT_FILE="${OUTPUT_FILE:-load-test-results.json}"
TEST_TYPE="${TEST_TYPE:-api}"
ENVIRONMENT="${ENVIRONMENT:-production}"
THRESHOLD_HTTP_REQ_FAILED="${THRESHOLD_HTTP_REQ_FAILED:-1}"
THRESHOLD_HTTP_REQ_DURATION_P95="${THRESHOLD_HTTP_REQ_DURATION_P95:-500}"
THRESHOLD_HTTP_REQ_DURATION_P99="${THRESHOLD_HTTP_REQ_DURATION_P99:-1000}"
TEST_ENGINE="${TEST_ENGINE:-k6}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
print_header() {
  echo -e "${BLUE}=================================================="
  echo -e "          MAILY LOAD TESTING SYSTEM           "
  echo -e "==================================================${NC}"
  echo ""
  echo -e "Test type: ${TEST_TYPE}"
  echo -e "Test engine: ${TEST_ENGINE}"
  echo -e "Target: ${API_BASE_URL}"
  echo -e "Duration: ${TEST_DURATION}"
  echo -e "Virtual users: ${VIRTUAL_USERS}"
  echo -e "Output: ${OUTPUT_FILE} (${OUTPUT_FORMAT})"
  echo ""
}

# Logging functions
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

# Check dependencies based on selected engine
check_dependencies() {
  log "Checking dependencies..."

  missing_deps=()
  
  # Common dependencies
  for tool in jq curl; do
    if ! command -v "${tool}" &> /dev/null; then
      missing_deps+=("${tool}")
    fi
  done
  
  # Engine-specific dependencies
  case ${TEST_ENGINE} in
    k6)
      if ! command -v k6 &> /dev/null; then
        missing_deps+=("k6")
      fi
      ;;
    locust)
      if ! command -v locust &> /dev/null; then
        missing_deps+=("locust")
      fi
      if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
      fi
      ;;
    artillery)
      if ! command -v artillery &> /dev/null; then
        missing_deps+=("artillery")
      fi
      ;;
    vegeta)
      if ! command -v vegeta &> /dev/null; then
        missing_deps+=("vegeta")
      fi
      ;;
    ab)
      if ! command -v ab &> /dev/null; then
        missing_deps+=("ab (Apache Bench)")
      fi
      ;;
    custom)
      log "Using custom test script, no specific dependencies to check"
      ;;
    *)
      warn "Unknown test engine: ${TEST_ENGINE}"
      ;;
  esac
  
  if [ ${#missing_deps[@]} -gt 0 ]; then
    error "Missing dependencies: ${missing_deps[*]}"
    error "Please install missing dependencies and try again"
    exit 1
  fi
  
  log "All required dependencies are installed"
}

# Create a temporary directory for test scripts
create_temp_dir() {
  TEMP_DIR=$(mktemp -d)
  log "Created temporary directory: $TEMP_DIR"
  
  # Register cleanup function to remove temp dir on exit
  trap 'rm -rf "$TEMP_DIR"' EXIT
}

# Prepare test scripts based on test type and engine
prepare_test_scripts() {
  log "Preparing test scripts..."
  
  case ${TEST_ENGINE} in
    k6)
      prepare_k6_script
      ;;
    locust)
      prepare_locust_script
      ;;
    artillery)
      prepare_artillery_script
      ;;
    custom)
      log "Using custom test script, no preparation needed"
      ;;
    *)
      error "Unsupported test engine: ${TEST_ENGINE}"
      exit 1
      ;;
  esac
}

# Prepare k6 test script
prepare_k6_script() {
  # Check if standard script exists for test type
  if [ -f "${SCRIPT_DIR}/k6-${TEST_TYPE}-test.js" ]; then
    log "Using existing script: k6-${TEST_TYPE}-test.js"
    cp "${SCRIPT_DIR}/k6-${TEST_TYPE}-test.js" "${TEMP_DIR}/test-script.js"
    return
  fi
  
  # Otherwise create script based on test type
  log "Creating k6 script for ${TEST_TYPE} test"
  
  case ${TEST_TYPE} in
    api)
      create_k6_api_script
      ;;
    web)
      create_k6_web_script
      ;;
    email)
      create_k6_email_script
      ;;
    performance)
      # Special handling for blockchain or canvas performance
      if [ -f "${SCRIPT_DIR}/test_blockchain_performance.js" ]; then
        cp "${SCRIPT_DIR}/test_blockchain_performance.js" "${TEMP_DIR}/test-script.js"
      elif [ -f "${SCRIPT_DIR}/test_canvas_performance.js" ]; then
        cp "${SCRIPT_DIR}/test_canvas_performance.js" "${TEMP_DIR}/test-script.js"
      else
        warn "Specialized performance test scripts not found, using generic API test"
        create_k6_api_script
      fi
      ;;
    stress)
      create_k6_stress_script
      ;;
    *)
      warn "Unknown test type: ${TEST_TYPE}, using generic API test"
      create_k6_api_script
      ;;
  esac
}

# Create k6 API test script
create_k6_api_script() {
  cat > "${TEMP_DIR}/test-script.js" << EOF
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
}

# Create k6 Web test script
create_k6_web_script() {
  cat > "${TEMP_DIR}/test-script.js" << EOF
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
}

# Create k6 Email service test script
create_k6_email_script() {
  cat > "${TEMP_DIR}/test-script.js" << EOF
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
}

# Create k6 stress test script
create_k6_stress_script() {
  cat > "${TEMP_DIR}/test-script.js" << EOF
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');

// Test configuration - more aggressive than regular load test
export const options = {
  stages: [
    { duration: '${RAMP_UP_TIME}', target: ${VIRTUAL_USERS} },
    { duration: '${TEST_DURATION}', target: ${VIRTUAL_USERS} },
    // Spike test
    { duration: '30s', target: ${VIRTUAL_USERS} * 2 },
    { duration: '1m', target: ${VIRTUAL_USERS} * 2 },
    { duration: '30s', target: ${VIRTUAL_USERS} },
    // Gradual ramp down
    { duration: '${RAMP_DOWN_TIME}', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<${THRESHOLD_HTTP_REQ_FAILED}%'],
    http_req_duration: ['p(95)<${THRESHOLD_HTTP_REQ_DURATION_P95}', 'p(99)<${THRESHOLD_HTTP_REQ_DURATION_P99}'],
  },
};

// Main test function - simplified to generate maximum load
export default function() {
  const baseUrl = '${API_BASE_URL}';
  
  // Multiple parallel requests to generate stress
  const responses = http.batch([
    ['GET', \`\${baseUrl}/health\`],
    ['GET', \`\${baseUrl}/api/campaigns\`],
    ['GET', \`\${baseUrl}/api/email-templates\`],
    ['GET', \`\${baseUrl}/api/analytics/dashboard\`]
  ]);
  
  // Check responses
  check(responses[0], {
    'health check status is 200': (r) => r.status === 200,
  });
  
  errorRate.add(responses[0].status !== 200);
  
  // Minimal sleep to maximize request rate
  sleep(0.1);
}
EOF
}

# Prepare Locust test script
prepare_locust_script() {
  log "Preparing Locust script..."
  
  # Use existing locustfile if available
  if [ -f "${SCRIPT_DIR}/locustfile.py" ]; then
    log "Using existing Locust script: locustfile.py"
    cp "${SCRIPT_DIR}/locustfile.py" "${TEMP_DIR}/locustfile.py"
    return
  fi
  
  # Otherwise create a simple locustfile
  cat > "${TEMP_DIR}/locustfile.py" << EOF
from locust import HttpUser, task, between

class MailyUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/health")
    
    @task(3)
    def get_campaigns(self):
        self.client.get("/api/campaigns")
    
    @task(2)
    def get_analytics(self):
        self.client.get("/api/analytics/dashboard")
    
    @task(2)
    def get_templates(self):
        self.client.get("/api/email-templates")
EOF
}

# Prepare Artillery test script
prepare_artillery_script() {
  log "Preparing Artillery script..."
  
  cat > "${TEMP_DIR}/artillery-config.yml" << EOF
config:
  target: "${API_BASE_URL}"
  phases:
    - duration: ${TEST_DURATION}
      arrivalRate: ${VIRTUAL_USERS}
  defaults:
    headers:
      Content-Type: "application/json"

scenarios:
  - name: "API Load Test"
    flow:
      - get:
          url: "/health"
          expect:
            - statusCode: 200
      - get:
          url: "/api/campaigns"
      - get:
          url: "/api/email-templates"
      - get:
          url: "/api/analytics/dashboard"
EOF
}

# Run the load test with the selected engine
run_load_test() {
  log "Running load test with ${TEST_ENGINE} engine..."
  
  case ${TEST_ENGINE} in
    k6)
      run_k6_test
      ;;
    locust)
      run_locust_test
      ;;
    artillery)
      run_artillery_test
      ;;
    vegeta)
      run_vegeta_test
      ;;
    ab)
      run_ab_test
      ;;
    custom)
      run_custom_test
      ;;
    *)
      error "Unsupported test engine: ${TEST_ENGINE}"
      exit 1
      ;;
  esac
}

# Run k6 load test
run_k6_test() {
  log "Running k6 load test..."
  k6 run --out ${OUTPUT_FORMAT}=${OUTPUT_FILE} ${TEMP_DIR}/test-script.js
  log "k6 test completed, results saved to: ${OUTPUT_FILE}"
}

# Run Locust load test
run_locust_test() {
  log "Running Locust load test..."
  
  # Determine output format parameters
  output_args=""
  if [ "${OUTPUT_FORMAT}" = "json" ]; then
    output_args="--json"
  elif [ "${OUTPUT_FORMAT}" = "csv" ]; then
    output_args="--csv=${OUTPUT_FILE}"
  fi
  
  # Run locust in headless mode
  locust -f ${TEMP_DIR}/locustfile.py --host=${API_BASE_URL} --users=${VIRTUAL_USERS} \
    --spawn-rate=10 --run-time=${TEST_DURATION} --headless ${output_args}
  
  log "Locust test completed"
}

# Run Artillery load test
run_artillery_test() {
  log "Running Artillery load test..."
  
  # Run the test
  artillery run --output ${OUTPUT_FILE} ${TEMP_DIR}/artillery-config.yml
  
  # Generate report if needed
  if [ "${OUTPUT_FORMAT}" = "html" ]; then
    artillery report ${OUTPUT_FILE}
    log "Artillery test completed, HTML report generated"
  else
    log "Artillery test completed, results saved to: ${OUTPUT_FILE}"
  fi
}

# Run Vegeta load test
run_vegeta_test() {
  log "Running Vegeta load test..."
  
  # Create targets file
  cat > ${TEMP_DIR}/targets.txt << EOF
GET ${API_BASE_URL}/health
GET ${API_BASE_URL}/api/campaigns
GET ${API_BASE_URL}/api/email-templates
GET ${API_BASE_URL}/api/analytics/dashboard
EOF
  
  # Run Vegeta attack
  cat ${TEMP_DIR}/targets.txt | vegeta attack -rate=${VIRTUAL_USERS} -duration=${TEST_DURATION} | vegeta report > ${OUTPUT_FILE}
  
  log "Vegeta test completed, results saved to: ${OUTPUT_FILE}"
}

# Run Apache Bench load test
run_ab_test() {
  log "Running Apache Bench load test..."
  
  # Apache Bench is simpler and only tests a single endpoint
  ab -n $((VIRTUAL_USERS * 100)) -c ${VIRTUAL_USERS} -g ${OUTPUT_FILE} ${API_BASE_URL}/health
  
  log "Apache Bench
# Run custom test script
run_custom_test() {
  log "Running custom load test script..."
  
  if [ -f "${SCRIPT_DIR}/custom-test-script.sh" ]; then
    bash "${SCRIPT_DIR}/custom-test-script.sh"
  else
    error "Custom test script not found: ${SCRIPT_DIR}/custom-test-script.sh"
    exit 1
  fi
}

# Parse command line arguments
usage() {
  cat << EOF
Maily Load Testing Script

Usage: $(basename "$0") [options]

Options:
  --url URL               Base URL to test against (default: ${API_BASE_URL})
  --type TYPE             Test type (api, web, email, performance, stress)
  --users N               Number of virtual users (default: ${VIRTUAL_USERS})
  --duration TIME         Test duration (default: ${TEST_DURATION})
  --engine ENGINE         Test engine (k6, locust, artillery, vegeta, ab, custom)
  --output-format FORMAT  Output format (json, csv, html)
  --output-file FILE      Output file name
  --environment ENV       Environment to test (production, staging)
  --help                 Show this help message

Examples:
  $(basename "$0") --url https://api.maily.com --type api --users 100 --duration 10m
  $(basename "$0") --type stress --engine k6
  $(basename "$0") --type web --engine artillery --output-format html
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --url)
        API_BASE_URL="$2"
        shift 2
        ;;
      --type)
        TEST_TYPE="$2"
        shift 2
        ;;
      --users)
        VIRTUAL_USERS="$2"
        shift 2
        ;;
      --duration)
        TEST_DURATION="$2"
        shift 2
        ;;
      --engine)
        TEST_ENGINE="$2"
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
      --environment)
        ENVIRONMENT="$2"
        shift 2
        ;;
      --help)
        usage
        exit 0
        ;;
      *)
        error "Unknown option: $1"
        usage
        exit 1
        ;;
    esac
  done
}

# Main function
main() {
  parse_args "$@"
  
  print_header
  check_dependencies
  create_temp_dir
  prepare_test_scripts
  run_load_test
  
  log "Load test completed successfully!"
}

# Run main function with all arguments
main "$@"
