/**
 * Mock Email Server
 *
 * Creates a simple HTTP server that simulates an email API for testing purposes.
 * Allows controlling response success/failure rate and simulating network latency.
 */

import { createServer, Server, IncomingMessage, ServerResponse } from 'http';

interface MockEmailServerOptions {
  port: number;
  failureRate: number;
  delayMs: number;
}

interface MockEmailServer {
  setFailureRate: (rate: number) => void;
  close: () => void;
}

/**
 * Creates a mock email server for testing
 */
export function createMockEmailServer({ port, failureRate = 0, delayMs = 50 }: MockEmailServerOptions): MockEmailServer {
  let currentFailureRate = failureRate;

  const server = createServer((req: IncomingMessage, res: ServerResponse) => {
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

        // Parse URL to determine response
        const path = req.url?.split('?')[0];

        // Handle different API endpoints
        if (path?.startsWith('/emails')) {
          if (req.method === 'POST') {
            // Handle email send
            try {
              let parsedBody = {};
              try {
                parsedBody = JSON.parse(body);
              } catch (e) {
                // Ignore parsing errors for simplicity
              }

              res.statusCode = 200;
              res.end(JSON.stringify({
                id: `msg_${Date.now()}_${Math.floor(Math.random() * 1000000)}`,
                from: (parsedBody as any).from,
                to: (parsedBody as any).to,
                status: 'sent',
                created_at: new Date().toISOString()
              }));
            } catch (error) {
              res.statusCode = 500;
              res.end(JSON.stringify({
                error: 'server_error',
                message: 'An unexpected error occurred'
              }));
            }
          } else if (req.method === 'GET' && path?.match(/\/emails\/[^/]+$/)) {
            // Handle email status check
            const emailId = path.split('/').pop();

            res.statusCode = 200;
            res.end(JSON.stringify({
              id: emailId,
              status: 'delivered',
              delivered_at: new Date().toISOString()
            }));
          } else {
            res.statusCode = 404;
            res.end(JSON.stringify({ error: 'not_found' }));
          }
        } else if (path?.startsWith('/templates')) {
          if (req.method === 'POST') {
            // Handle template creation
            res.statusCode = 200;
            res.end(JSON.stringify({
              id: `template_${Date.now()}`,
              name: 'Test Template',
              version: '1',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }));
          } else if (req.method === 'GET' && path?.match(/\/templates\/[^/]+$/)) {
            // Handle template retrieval
            const templateId = path.split('/').pop();

            res.statusCode = 200;
            res.end(JSON.stringify({
              id: templateId,
              name: 'Test Template',
              html: '<p>Test template content</p>',
              text: 'Test template content',
              version: '1',
              variables: ['name', 'company'],
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }));
          } else if (req.method === 'PATCH' && path?.match(/\/templates\/[^/]+$/)) {
            // Handle template update
            const templateId = path.split('/').pop();

            res.statusCode = 200;
            res.end(JSON.stringify({
              id: templateId,
              name: 'Updated Template',
              html: '<p>Updated template content</p>',
              text: 'Updated template content',
              version: '2',
              variables: ['name', 'company'],
              created_at: new Date(Date.now() - 86400000).toISOString(), // Yesterday
              updated_at: new Date().toISOString()
            }));
          } else if (req.method === 'DELETE' && path?.match(/\/templates\/[^/]+$/)) {
            // Handle template deletion
            res.statusCode = 200;
            res.end(JSON.stringify({ deleted: true }));
          } else {
            res.statusCode = 404;
            res.end(JSON.stringify({ error: 'not_found' }));
          }
        } else {
          // Unknown endpoint
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
