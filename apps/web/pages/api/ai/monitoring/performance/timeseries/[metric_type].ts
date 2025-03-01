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

    // Get metric type from URL
    const { metric_type } = req.query;

    if (!metric_type || Array.isArray(metric_type)) {
      return res.status(400).json({ error: 'Invalid metric type' });
    }

    // Get query parameters
    const { operation_type = 'generation', window = '60', model_name } = req.query;

    // Build query string
    const queryParams = new URLSearchParams();
    queryParams.append('operation_type', Array.isArray(operation_type) ? operation_type[0] : operation_type);
    queryParams.append('window', Array.isArray(window) ? window[0] : window);

    if (model_name) {
      queryParams.append('model_name', Array.isArray(model_name) ? model_name[0] : model_name);
    }

    // Get API URL from environment variables
    const apiUrl = process.env.API_URL || 'http://localhost:8000';

    // Fetch timeseries data from backend
    const response = await fetch(
      `${apiUrl}/ai/monitoring/performance/timeseries/${metric_type}?${queryParams.toString()}`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      return res.status(response.status).json(errorData);
    }

    const data = await response.json();
    return res.status(200).json(data);
  } catch (error) {
    console.error('Error fetching AI timeseries data:', error);
    return res.status(500).json({ error: 'Failed to fetch AI timeseries data' });
  }
}
