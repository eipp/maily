import { describe, it, expect, beforeEach, jest, afterEach } from '@jest/globals';
import axios from 'axios';
import { ResendEmailProvider } from '../adapters/providers/resend-provider';
import { Email, DeliveryStatus } from '../domain/models';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('ResendEmailProvider', () => {
  let provider: ResendEmailProvider;

  beforeEach(() => {
    // Create a new provider instance with test config
    provider = new ResendEmailProvider('test-api-key', {
      failureThreshold: 3,
      resetTimeout: 1000
    });

    // Reset mocks
    jest.clearAllMocks();

    // Setup default axios create mock implementation
    mockedAxios.create.mockReturnValue({
      post: jest.fn(),
      get: jest.fn(),
      patch: jest.fn(),
      delete: jest.fn()
    } as any);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('sendBulk', () => {
    it('should process emails in batches with the specified batch size', async () => {
      // Prepare test data
      const testEmails: Email[] = Array(50).fill(null).map((_, i) => ({
        id: `email-${i}`,
        from: 'test@example.com',
        to: `recipient-${i}@example.com`,
        subject: `Test Email ${i}`
      }));

      // Mock successful responses
      const mockApiClient = {
        post: jest.fn().mockImplementation(() => Promise.resolve({
          data: { id: 'message-id', status: 'success' }
        }))
      };
      (provider as any).apiClient = mockApiClient;

      // Set batch size to 10
      const batchSize = 10;

      // Call the method
      const result = await provider.sendBulk(testEmails, batchSize);

      // Verify results
      expect(result.success).toBe(true);
      expect(result.total).toBe(50);
      expect(result.sent).toBe(50);
      expect(result.failed).toBe(0);
      expect(result.results.length).toBe(50);

      // Verify that the post method was called for each email
      expect(mockApiClient.post).toHaveBeenCalledTimes(50);
    });

    it('should handle failures in specific emails without failing the entire batch', async () => {
      // Prepare test data
      const testEmails: Email[] = Array(10).fill(null).map((_, i) => ({
        id: `email-${i}`,
        from: 'test@example.com',
        to: `recipient-${i}@example.com`,
        subject: `Test Email ${i}`
      }));

      // Mock responses - make 3 emails fail
      const mockApiClient = {
        post: jest.fn().mockImplementation((url, data) => {
          const emailIndex = testEmails.findIndex(
            email => Array.isArray(email.to)
              ? email.to[0] === data.to[0]
              : email.to === data.to[0]
          );

          // Make every third email fail
          if (emailIndex % 3 === 0) {
            return Promise.reject({
              response: {
                status: 400,
                data: { message: 'Invalid recipient' }
              }
            });
          }

          return Promise.resolve({
            data: { id: `message-id-${emailIndex}`, status: 'success' }
          });
        })
      };
      (provider as any).apiClient = mockApiClient;

      // Call the method
      const result = await provider.sendBulk(testEmails, 5);

      // Verify results
      expect(result.success).toBe(false); // Some emails failed
      expect(result.total).toBe(10);
      expect(result.sent).toBe(7);
      expect(result.failed).toBe(3);
      expect(result.results.length).toBe(10);

      // Verify specific results
      const failedResults = result.results.filter(r => !r.success);
      expect(failedResults.length).toBe(3);
      failedResults.forEach(r => {
        expect(r.error).toContain('Invalid recipient');
      });
    });
  });

  describe('Circuit Breaker', () => {
    it('should open circuit after reaching failure threshold', async () => {
      jest.useFakeTimers();

      // Mock consecutive failures
      const mockApiClient = {
        post: jest.fn().mockImplementation(() =>
          Promise.reject({
            response: {
              status: 500,
              data: { message: 'Server error' }
            }
          })
        )
      };
      (provider as any).apiClient = mockApiClient;

      // Send multiple emails to trigger failures
      const testEmail: Email = {
        from: 'test@example.com',
        to: 'recipient@example.com',
        subject: 'Test Email'
      };

      // Trigger 4 failures (threshold is 3)
      await provider.sendEmail(testEmail);
      await provider.sendEmail(testEmail);
      await provider.sendEmail(testEmail);

      // This should fail with circuit breaker message
      const result = await provider.sendEmail(testEmail);

      expect(result.success).toBe(false);
      expect(result.circuitBroken).toBe(true);
      expect(result.error).toContain('Circuit breaker open');

      // Verify that the API wasn't called for the last request
      expect(mockApiClient.post).toHaveBeenCalledTimes(3);
    });

    it('should transition to half-open state after reset timeout', async () => {
      jest.useFakeTimers();

      // Mock consecutive failures followed by success
      const mockApiClient = {
        post: jest.fn()
          .mockImplementationOnce(() => Promise.reject({
            response: { status: 500, data: { message: 'Server error' } }
          }))
          .mockImplementationOnce(() => Promise.reject({
            response: { status: 500, data: { message: 'Server error' } }
          }))
          .mockImplementationOnce(() => Promise.reject({
            response: { status: 500, data: { message: 'Server error' } }
          }))
          .mockImplementationOnce(() => Promise.resolve({
            data: { id: 'message-id', status: 'success' }
          }))
      };
      (provider as any).apiClient = mockApiClient;

      const testEmail: Email = {
        from: 'test@example.com',
        to: 'recipient@example.com',
        subject: 'Test Email'
      };

      // Trigger 3 failures to open circuit
      await provider.sendEmail(testEmail);
      await provider.sendEmail(testEmail);
      await provider.sendEmail(testEmail);

      // Circuit should be open now
      let result = await provider.sendEmail(testEmail);
      expect(result.circuitBroken).toBe(true);

      // Advance time past reset timeout
      jest.advanceTimersByTime(1500); // Timeout is 1000ms

      // Circuit should be half-open now and allow one test request
      result = await provider.sendEmail(testEmail);
      expect(result.success).toBe(true);
      expect(result.circuitBroken).toBeUndefined();

      // Verify API was called again after timeout
      expect(mockApiClient.post).toHaveBeenCalledTimes(4);
    });
  });
});
