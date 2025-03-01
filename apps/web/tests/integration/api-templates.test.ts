import { describe, it, expect, beforeEach, vi } from 'vitest';
import { NextRequest } from 'next/server';
import { GET } from '../../app/api/templates/route';
import { getServerSession } from 'next-auth';
import { prisma } from '../../lib/prisma';

// Mock next-auth
vi.mock('next-auth', () => ({
  getServerSession: vi.fn(),
}));

// Mock prisma
vi.mock('../../lib/prisma', () => ({
  prisma: {
    emailTemplate: {
      count: vi.fn(),
      findMany: vi.fn(),
    },
  },
}));

// Add type assertion to avoid TypeScript errors
const mockedPrisma = prisma as unknown as {
  emailTemplate: {
    count: ReturnType<typeof vi.fn>;
    findMany: ReturnType<typeof vi.fn>;
  }
};

describe('Templates API', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('GET /api/templates', () => {
    it('should return 401 if user is not authenticated', async () => {
      // Mock getServerSession to return null (unauthenticated)
      vi.mocked(getServerSession).mockResolvedValue(null);

      // Create a mock request
      const request = new NextRequest('http://localhost:3000/api/templates');

      // Call the API route handler
      const response = await GET(request);

      // Check if the response status is 401
      expect(response.status).toBe(401);

      // Check if the response body contains the expected message
      const data = await response.json();
      expect(data).toEqual({ message: 'Unauthorized' });
    });

    it('should return templates if user is authenticated', async () => {
      // Mock getServerSession to return a user session
      vi.mocked(getServerSession).mockResolvedValue({
        user: { id: 'user-123', name: 'Test User', email: 'test@example.com' },
        expires: '2025-02-26T00:00:00.000Z',
      });

      // Mock prisma count and findMany
      const mockTemplates = [
        {
          id: 1,
          name: 'Template 1',
          description: 'Description 1',
          thumbnail: null,
          category: 'Marketing',
          tags: ['tag1', 'tag2'],
          is_public: true,
          userId: 'user-123',
          createdAt: new Date(),
          updatedAt: new Date(),
          user: {
            name: 'Test User',
            email: 'test@example.com',
          },
        },
      ];

      vi.mocked(mockedPrisma.emailTemplate.count).mockResolvedValue(1);
      vi.mocked(mockedPrisma.emailTemplate.findMany).mockResolvedValue(mockTemplates);

      // Create a mock request
      const request = new NextRequest('http://localhost:3000/api/templates');

      // Call the API route handler
      const response = await GET(request);

      // Check if the response status is 200
      expect(response.status).toBe(200);

      // Check if the response body contains the expected data
      const data = await response.json();
      expect(data).toEqual({
        templates: mockTemplates,
        pagination: {
          total: 1,
          page: 1,
          limit: 12,
          pages: 1,
        },
      });

      // Verify that prisma was called with the correct parameters
      expect(mockedPrisma.emailTemplate.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            OR: [
              { userId: 'user-123' },
              { is_public: true },
            ],
          }),
        })
      );
    });
  });
});
