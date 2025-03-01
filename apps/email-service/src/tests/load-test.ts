/**
 * Load/Stress Test for Email Service
 *
 * This script tests the email service under high load to verify:
 * 1. Concurrent batch processing performance
 * 2. Circuit breaker functionality under load
 * 3. Error handling during high volume operations
 *
 * Usage:
 * NODE_ENV=test ts-node load-test.ts [--emails=1000] [--batch-size=50] [--concurrent=5]
 */

import { ResendEmailProvider } from '../adapters/providers/resend-provider';
import { Email } from '../domain/models';
import * as dotenv from 'dotenv';
import { createServer } from 'http';
import { createMockEmailServer } from './helpers/mock-email-server';

// Load environment variables
dotenv.config();

// Parse command line arguments
const args = process.argv.slice(2).reduce((acc, arg) => {
  const [key, value] = arg.replace('--', '').split('=');
  acc[key] = value;
  return acc;
}, {} as Record<string, string>);

// Configuration
const EMAIL_COUNT = parseInt(args.emails || '1000', 10);
const BATCH_SIZE = parseInt(args['batch-size'] || '50', 10);
const CONCURRENT_OPERATIONS = parseInt(args.concurrent || '5', 10);
const FAILURE_RATE = parseFloat(args['failure-rate'] || '0.05'); // 5% failure rate by default
const MOCK_DELAY_MS = parseInt(args.delay || '50', 10); // Simulated API delay

// Start mock email server for testing
const mockServer = createMockEmailServer({
  port: 3456,
  failureRate: FAILURE_RATE,
  delayMs: MOCK_DELAY_MS,
});

// Create test emails
function generateTestEmails(count: number): Email[] {
  return Array(count).fill(null).map((_, i) => ({
    id: `load-test-${i}`,
    from: 'loadtest@example.com',
    to: `recipient-${i}@example.com`,
    subject: `Load Test Email ${i}`,
    html: `<p>This is a load test email ${i}</p>`,
    text: `This is a load test email ${i}`,
    tags: ['load-test']
  }));
}

// Run batched email sending test
async function runBatchedSendTest() {
  console.log(`
🚀 Starting Email Service Load Test
=================================
Emails: ${EMAIL_COUNT}
Batch Size: ${BATCH_SIZE}
Concurrent Operations: ${CONCURRENT_OPERATIONS}
Simulated Failure Rate: ${FAILURE_RATE * 100}%
API Delay: ${MOCK_DELAY_MS}ms
=================================
  `);

  // Create provider using the mock server
  const provider = new ResendEmailProvider('test-api-key', {
    failureThreshold: 10,
    resetTimeout: 5000
  });

  // Override the API client to use our mock server
  (provider as any).apiClient = {
    post: async (path: string, data: any) => {
      const response = await fetch(`http://localhost:3456${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw {
          response: {
            status: response.status,
            data: errorData
          }
        };
      }

      return { data: await response.json() };
    },
    get: async (path: string) => {
      const response = await fetch(`http://localhost:3456${path}`);
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      return { data: await response.json() };
    }
  };

  // Generate test emails
  const emails = generateTestEmails(EMAIL_COUNT);

  console.log(`Generated ${emails.length} test emails`);

  // Track performance metrics
  const startTime = Date.now();
  let successCount = 0;
  let failureCount = 0;
  let totalSent = 0;

  try {
    // Send emails in concurrent batches
    console.log(`Sending emails in ${CONCURRENT_OPERATIONS} concurrent operations...`);

    // Split emails into chunks for concurrent processing
    const emailChunks: Email[][] = [];
    for (let i = 0; i < emails.length; i += Math.ceil(emails.length / CONCURRENT_OPERATIONS)) {
      emailChunks.push(emails.slice(i, i + Math.ceil(emails.length / CONCURRENT_OPERATIONS)));
    }

    // Process each chunk concurrently
    const results = await Promise.all(
      emailChunks.map(async (chunk, index) => {
        console.log(`Starting concurrent operation ${index + 1} with ${chunk.length} emails`);
        const result = await provider.sendBulk(chunk, BATCH_SIZE);
        return result;
      })
    );

    // Aggregate results
    for (const result of results) {
      successCount += result.sent;
      failureCount += result.failed;
      totalSent += result.total;
    }

    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;
    const emailsPerSecond = totalSent / duration;

    // Calculate percentiles for response times
    // (For a real implementation, we'd track individual response times)

    // Print results
    console.log(`
📊 Load Test Results
=================================
Total Emails: ${totalSent}
Successful: ${successCount} (${((successCount / totalSent) * 100).toFixed(2)}%)
Failed: ${failureCount} (${((failureCount / totalSent) * 100).toFixed(2)}%)
Duration: ${duration.toFixed(2)} seconds
Throughput: ${emailsPerSecond.toFixed(2)} emails/second
=================================
    `);

    // Test circuit breaker
    console.log(`Testing circuit breaker functionality...`);
    if (FAILURE_RATE > 0) {
      console.log(`Set mock server to 100% failure rate to trigger circuit breaker`);
      mockServer.setFailureRate(1.0); // 100% failure

      try {
        // Send a few emails to trigger circuit breaker
        for (let i = 0; i < 15; i++) {
          try {
            await provider.sendEmail({
              from: 'circuit@example.com',
              to: 'test@example.com',
              subject: 'Circuit Breaker Test'
            });
            console.log(`Attempt ${i + 1}: Email sent`);
          } catch (error) {
            console.log(`Attempt ${i + 1}: Failed as expected`);
          }
        }

        // Try once more - should be blocked by circuit breaker
        const finalResult = await provider.sendEmail({
          from: 'circuit@example.com',
          to: 'test@example.com',
          subject: 'Circuit Breaker Test'
        });

        if (finalResult.circuitBroken) {
          console.log(`✅ Circuit breaker activated successfully`);
        } else {
          console.log(`❌ Circuit breaker did not activate as expected`);
        }

        // Reset circuit breaker
        console.log(`Waiting for circuit breaker reset (5 seconds)...`);
        await new Promise(resolve => setTimeout(resolve, 5500));

        // Set mock server back to success
        mockServer.setFailureRate(0);

        // Try again - should work now
        const resetResult = await provider.sendEmail({
          from: 'circuit@example.com',
          to: 'test@example.com',
          subject: 'Circuit Breaker Reset Test'
        });

        if (resetResult.success) {
          console.log(`✅ Circuit breaker reset successfully`);
        } else {
          console.log(`❌ Circuit breaker did not reset as expected`);
        }
      } catch (error) {
        console.error(`Error during circuit breaker test:`, error);
      }
    }
  } catch (error) {
    console.error('Test failed with error:', error);
  } finally {
    // Cleanup
    mockServer.close();
    console.log('Load test completed');
  }
}

// Create mock email server helper
function createMockEmailServer({ port, failureRate, delayMs }: { port: number, failureRate: number, delayMs: number }) {
  let currentFailureRate = failureRate;

  const server = createServer((req, res) => {
    let body = '';

    req.on('data', chunk => {
      body += chunk.toString();
    });

    req.on('end', () => {
      // Add artificial delay to simulate network latency
      setTimeout(() => {
        res.setHeader('Content-Type', 'application/json');

        // Simulate random failures based on failure rate
        if (Math.random() < currentFailureRate) {
          res.statusCode = 429;
          res.end(JSON.stringify({
            error: 'rate_limit_exceeded',
            message: 'Too many requests, please try again later.'
          }));
          return;
        }

        // Success response
        if (req.url?.includes('/emails')) {
          res.statusCode = 200;
          res.end(JSON.stringify({
            id: `msg_${Date.now()}_${Math.floor(Math.random() * 1000000)}`,
            status: 'sent'
          }));
        } else {
          res.statusCode = 404;
          res.end(JSON.stringify({ error: 'not_found' }));
        }
      }, delayMs);
    });
  });

  server.listen(port);
  console.log(`Mock email server running on port ${port}`);

  return {
    setFailureRate: (rate: number) => {
      currentFailureRate = rate;
    },
    close: () => {
      server.close();
    }
  };
}

// Run the test
runBatchedSendTest().catch(console.error);
