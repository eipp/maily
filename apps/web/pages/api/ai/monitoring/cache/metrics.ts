import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/pages/api/auth/[...nextauth]';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Check if the request method is GET
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Check authentication
    const session = await getServerSession(req, res, authOptions);
    if (!session) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    // Check if user is admin
    if (!session.user?.isAdmin) {
      return res.status(403).json({ error: 'Forbidden: Admin access required' });
    }

    // Get API URL from environment variables
    const apiUrl = process.env.API_URL || 'http://localhost:8000';

    // Fetch cache metrics from backend
    const response = await fetch(
      `${apiUrl}/ai/monitoring/cache/metrics`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      // If the cache metrics are not found, return an empty response
      // instead of an error, as this is an optional feature
      if (response.status === 404) {
        return res.status(200).json(null);
      }

      const errorData = await response.json();
      return res.status(response.status).json(errorData);
    }

    const data = await response.json();
    return res.status(200).json(data);
  } catch (error) {
    console.error('Error fetching cache metrics:', error);
    return res.status(500).json({ error: 'Failed to fetch cache metrics' });
  }
}
