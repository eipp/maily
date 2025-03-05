import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { WebSocket } from 'k6/experimental/websockets';

// Custom metrics
const websocketMsgs = new Counter('websocket_messages');
const taskCreationRate = new Rate('task_creation_success');
const networkCreationRate = new Rate('network_creation_success');
const canvasLoadTime = new Trend('canvas_load_time');
const agentResponseTime = new Trend('agent_response_time');
const fullOperationTime = new Trend('full_operation_time');

export const options = {
  scenarios: {
    // Scenario 1: Load test with moderate number of concurrent users
    load_test: {
      executor: 'ramping-vus',
      startVUs: 5,
      stages: [
        { duration: '30s', target: 20 },  // Ramp up to 20 users over 30 seconds
        { duration: '1m', target: 20 },   // Stay at 20 users for 1 minute
        { duration: '30s', target: 0 },   // Ramp down to 0 users over 30 seconds
      ],
      gracefulRampDown: '10s',
    },
    
    // Scenario 2: Stress test with higher concurrency
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '20s', target: 50 },  // Ramp up to 50 users over 20 seconds
        { duration: '30s', target: 50 },  // Stay at 50 users for 30 seconds
        { duration: '10s', target: 0 },   // Ramp down to 0 users over 10 seconds
      ],
      gracefulRampDown: '10s',
      exec: 'stressTest',  // Use a different function for stress testing
    },
    
    // Scenario 3: Websocket performance test
    websocket_test: {
      executor: 'constant-vus',
      vus: 10,
      duration: '1m',
      exec: 'websocketTest',  // Use the websocket test function
    },
  },
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],  // 95% of requests should be below 500ms, 99% below 1000ms
    'canvas_load_time': ['p(95)<800'],                 // 95% of canvas loads should be below 800ms
    'agent_response_time': ['p(90)<2000'],             // 90% of AI agent responses should be below 2000ms
    'full_operation_time': ['p(90)<5000'],             // 90% of full operations should be below 5000ms
    'websocket_messages': ['count>100'],               // Should process at least 100 websocket messages during test
    'task_creation_success': ['rate>0.95'],            // Task creation success rate should be above 95%
    'network_creation_success': ['rate>0.98'],         // Network creation success rate should be above 98%
  },
};

// Default function for the load test scenario
export default function () {
  const baseUrl = __ENV.API_URL || 'https://staging-api.maily.app';
  const userId = `test-user-${__VU}-${__ITER}`;
  
  // Test session authentication (simplified for performance testing)
  const loginRes = http.post(`${baseUrl}/api/auth/test-login`, {
    user_id: userId,
  });
  
  check(loginRes, {
    'login successful': (r) => r.status === 200,
  });
  
  const authToken = loginRes.json('data.token');
  
  // 1. Create an AI Mesh Network for canvas editing
  const startTime = new Date();
  const createNetworkRes = http.post(`${baseUrl}/api/v1/ai/mesh/network/create`, {
    purpose: 'canvas_editing',
    user_id: userId,
    settings: {
      max_agents: 4,
      auto_analyze: true,
    }
  }, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  const networkCreationSuccess = check(createNetworkRes, {
    'network creation successful': (r) => r.status === 200,
    'network ID returned': (r) => r.json('data.network_id') !== undefined,
  });
  
  networkCreationRate.add(networkCreationSuccess);
  
  if (!networkCreationSuccess) {
    console.log(`Failed to create network: ${createNetworkRes.status} ${createNetworkRes.body}`);
    return;
  }
  
  const networkId = createNetworkRes.json('data.network_id');
  
  // 2. Load the canvas (simulating canvas data retrieval)
  const canvasStartTime = new Date();
  const canvasRes = http.get(`${baseUrl}/api/v1/canvas/demo`, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
    },
  });
  
  const canvasLoadSuccess = check(canvasRes, {
    'canvas load successful': (r) => r.status === 200,
    'canvas data returned': (r) => r.json('data') !== undefined,
  });
  
  canvasLoadTime.add(new Date() - canvasStartTime);
  
  // 3. Create tasks to test AI Mesh performance
  // Create an analysis task
  const taskStartTime = new Date();
  const createTaskRes = http.post(`${baseUrl}/api/v1/ai/mesh/task/create`, {
    network_id: networkId,
    type: 'analyze_canvas_element',
    priority: 'high',
    data: {
      element_id: `element-${__VU}-${__ITER}`,
      element_type: 'rect',
      properties: {
        x: 100,
        y: 100,
        width: 200,
        height: 150,
        fill: '#e0e0e0',
        stroke: '#000000',
      }
    }
  }, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  const taskCreationSuccess = check(createTaskRes, {
    'task creation successful': (r) => r.status === 200,
    'task ID returned': (r) => r.json('data.task_id') !== undefined,
  });
  
  taskCreationRate.add(taskCreationSuccess);
  
  if (!taskCreationSuccess) {
    console.log(`Failed to create task: ${createTaskRes.status} ${createTaskRes.body}`);
    return;
  }
  
  const taskId = createTaskRes.json('data.task_id');
  
  // 4. Poll for task completion (simulating waiting for AI agents to process)
  let taskCompleted = false;
  let attempts = 0;
  const maxAttempts = 10;
  
  while (!taskCompleted && attempts < maxAttempts) {
    sleep(1);  // Wait 1 second between polls
    attempts++;
    
    const taskStatusRes = http.get(`${baseUrl}/api/v1/ai/mesh/task/${taskId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });
    
    const status = taskStatusRes.json('data.status');
    taskCompleted = status === 'completed' || status === 'failed';
    
    if (taskCompleted && status === 'completed') {
      // Record the agent response time (time from task creation to completion)
      agentResponseTime.add(new Date() - taskStartTime);
      
      // Check the analysis results
      check(taskStatusRes, {
        'analysis data returned': (r) => r.json('data.analysis') !== undefined,
        'design analysis included': (r) => r.json('data.analysis.design') !== undefined,
        'reasoning analysis included': (r) => r.json('data.analysis.reasoning') !== undefined,
      });
    }
  }
  
  // 5. Create a canvas update (simulating user editing)
  http.post(`${baseUrl}/api/v1/canvas/update`, {
    canvas_id: 'demo',
    element_id: `element-${__VU}-${__ITER}`,
    properties: {
      fill: '#f0f0f0',
      stroke: '#0000ff',
    }
  }, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  // Record the total operation time
  fullOperationTime.add(new Date() - startTime);
  
  // 6. Clean up - close the network (not always needed in performance tests)
  http.post(`${baseUrl}/api/v1/ai/mesh/network/${networkId}/close`, {}, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  // Add some randomized think time between iterations
  sleep(Math.random() * 3 + 1);  // 1-4 seconds of "think time"
}

// Stress test function with more complex operations
export function stressTest() {
  const baseUrl = __ENV.API_URL || 'https://staging-api.maily.app';
  const userId = `stress-user-${__VU}-${__ITER}`;
  
  // Authenticate
  const loginRes = http.post(`${baseUrl}/api/auth/test-login`, {
    user_id: userId,
  });
  
  const authToken = loginRes.json('data.token');
  
  // Create network
  const createNetworkRes = http.post(`${baseUrl}/api/v1/ai/mesh/network/create`, {
    purpose: 'canvas_stress_test',
    user_id: userId,
    settings: {
      max_agents: 4,
      auto_analyze: true,
      high_performance: true,
    }
  }, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  const networkId = createNetworkRes.json('data.network_id');
  
  // Create multiple tasks in rapid succession
  const taskIds = [];
  const numTasks = 5;
  
  for (let i = 0; i < numTasks; i++) {
    const createTaskRes = http.post(`${baseUrl}/api/v1/ai/mesh/task/create`, {
      network_id: networkId,
      type: i % 2 === 0 ? 'analyze_canvas_element' : 'generate_canvas_layout',
      priority: 'high',
      data: {
        element_id: `stress-element-${__VU}-${__ITER}-${i}`,
        element_type: 'rect',
        properties: {
          x: 100 * i,
          y: 100 * i,
          width: 200,
          height: 150,
        }
      }
    }, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    });
    
    taskIds.push(createTaskRes.json('data.task_id'));
  }
  
  // Poll for completion of all tasks
  let allTasksCompleted = false;
  let attempts = 0;
  const maxAttempts = 15;
  
  while (!allTasksCompleted && attempts < maxAttempts) {
    sleep(1);
    attempts++;
    
    // Check status of all tasks
    let completedCount = 0;
    
    for (const taskId of taskIds) {
      const taskStatusRes = http.get(`${baseUrl}/api/v1/ai/mesh/task/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });
      
      const status = taskStatusRes.json('data.status');
      if (status === 'completed' || status === 'failed') {
        completedCount++;
      }
    }
    
    allTasksCompleted = completedCount === taskIds.length;
  }
  
  // Clean up
  http.post(`${baseUrl}/api/v1/ai/mesh/network/${networkId}/close`, {}, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  sleep(Math.random() * 2 + 1);  // 1-3 seconds of "think time"
}

// WebSocket test function
export function websocketTest() {
  const baseUrl = __ENV.API_URL || 'https://staging-api.maily.app';
  const wsBaseUrl = baseUrl.replace('https://', 'wss://').replace('http://', 'ws://');
  const userId = `ws-user-${__VU}-${__ITER}`;
  
  // Authenticate
  const loginRes = http.post(`${baseUrl}/api/auth/test-login`, {
    user_id: userId,
  });
  
  const authToken = loginRes.json('data.token');
  
  // Create AI Mesh Network
  const createNetworkRes = http.post(`${baseUrl}/api/v1/ai/mesh/network/create`, {
    purpose: 'websocket_test',
    user_id: userId,
  }, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  const networkId = createNetworkRes.json('data.network_id');
  
  // Create WebSocket connection
  const ws = new WebSocket(`${wsBaseUrl}/api/mesh/network/${networkId}/ws?token=${authToken}`);
  
  // WebSocket open handler
  ws.addEventListener('open', () => {
    // Send a ping message
    ws.send(JSON.stringify({
      type: 'ping',
      timestamp: new Date().toISOString(),
    }));
    
    // Request active tasks
    ws.send(JSON.stringify({
      type: 'get_active_tasks',
      network_id: networkId,
    }));
  });
  
  // WebSocket message handler
  ws.addEventListener('message', (msg) => {
    websocketMsgs.add(1);
    const data = JSON.parse(msg.data);
    
    // If we received a pong, send another ping after a delay
    if (data.type === 'pong') {
      setTimeout(() => {
        ws.send(JSON.stringify({
          type: 'ping',
          timestamp: new Date().toISOString(),
        }));
      }, 1000);
    }
  });
  
  // Create a task that will generate WebSocket updates
  const createTaskRes = http.post(`${baseUrl}/api/v1/ai/mesh/task/create`, {
    network_id: networkId,
    type: 'generate_canvas_layout',
    data: {
      prompt: 'Create a simple layout with a header and 2 columns',
    }
  }, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  const taskId = createTaskRes.json('data.task_id');
  
  // Subscribe to task updates
  ws.send(JSON.stringify({
    type: 'subscribe_task',
    task_id: taskId,
  }));
  
  // Keep the WebSocket connection open for 10 seconds
  sleep(10);
  
  // Unsubscribe from task
  ws.send(JSON.stringify({
    type: 'unsubscribe_task',
    task_id: taskId,
  }));
  
  // Close the WebSocket connection
  ws.close();
  
  // Clean up the network
  http.post(`${baseUrl}/api/v1/ai/mesh/network/${networkId}/close`, {}, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
  });
}