import { NextRequest, NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';
import { Ratelimit } from '@upstash/ratelimit';
import { getServerSession } from 'next-auth';
import { z } from 'zod';
import { analyticsService } from '@/services/analytics';
import { prisma } from '@/lib/prisma';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';

// Initialize Redis client
const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

// Create rate limiter
const ratelimit = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(20, '1 m'), // 20 requests per minute
});

// Campaign analytics response schema
const analyticsResponseSchema = z.object({
  openRate: z.number().min(0).max(100),
  clickRate: z.number().min(0).max(100),
  conversionRate: z.number().min(0).max(100),
  engagement: z.number().min(0).max(100),
});

export async function GET(
  request: NextRequest,
  { params }: { params: { campaignId: string } }
) {
  try {
    // 1. Rate limiting check
    const ip = request.ip ?? '127.0.0.1';
    const { success, reset } = await ratelimit.limit(ip);

    if (!success) {
      return NextResponse.json(
        { error: 'Too many requests' },
        {
          status: 429,
          headers: { 'Retry-After': String(reset) }
        }
      );
    }

    // 2. Authentication check
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // 3. Check cache first
    const cacheKey = `analytics:${params.campaignId}`;
    const cachedData = await redis.get(cacheKey);

    if (cachedData) {
      return NextResponse.json(cachedData);
    }

    // 4. Fetch real data from database
    const campaign = await prisma.campaign.findUnique({
      where: { id: params.campaignId },
      include: {
        emails: {
          select: {
            opens: true,
            clicks: true,
            conversions: true,
            totalSent: true,
          }
        }
      }
    });

    if (!campaign) {
      return NextResponse.json(
        { error: 'Campaign not found' },
        { status: 404 }
      );
    }

    // 5. Calculate analytics
    const analytics = {
      openRate: calculateRate(
        campaign.emails.reduce((sum, email) => sum + email.opens, 0),
        campaign.emails.reduce((sum, email) => sum + email.totalSent, 0)
      ),
      clickRate: calculateRate(
        campaign.emails.reduce((sum, email) => sum + email.clicks, 0),
        campaign.emails.reduce((sum, email) => sum + email.totalSent, 0)
      ),
      conversionRate: calculateRate(
        campaign.emails.reduce((sum, email) => sum + email.conversions, 0),
        campaign.emails.reduce((sum, email) => sum + email.totalSent, 0)
      ),
      engagement: calculateEngagement(campaign.emails),
    };

    // 6. Validate response data
    const validatedData = analyticsResponseSchema.parse(analytics);

    // 7. Cache the results (5 minutes TTL)
    await redis.set(cacheKey, validatedData, { ex: 300 });

    // 8. Track analytics access
    analyticsService.trackCampaign('analytics_viewed', params.campaignId, {
      user_id: session.user.id,
      cache_hit: false,
    });

    return NextResponse.json(validatedData);
  } catch (error) {
    // 9. Error handling and logging
    console.error('Error fetching campaign analytics:', error);
    analyticsService.trackError(error as Error, {
      context: 'campaign_analytics',
      campaign_id: params.campaignId,
    });

    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid analytics data format' },
        { status: 422 }
      );
    }

    return NextResponse.json(
      { error: 'Failed to fetch analytics data' },
      { status: 500 }
    );
  }
}

// Helper functions
function calculateRate(value: number, total: number): number {
  if (total === 0) return 0;
  return (value / total) * 100;
}

function calculateEngagement(emails: { opens: number; clicks: number; totalSent: number }[]): number {
  const totalEmails = emails.reduce((sum, email) => sum + email.totalSent, 0);
  if (totalEmails === 0) return 0;

  const opens = emails.reduce((sum, email) => sum + email.opens, 0);
  const clicks = emails.reduce((sum, email) => sum + email.clicks, 0);

  // Engagement score formula: (opens + clicks * 2) / totalEmails
  return Math.min(((opens + clicks * 2) / totalEmails) * 50, 100); // Normalize to 0-100
}
