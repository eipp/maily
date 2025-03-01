import { NextRequest, NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';
import { PrismaClient } from '@prisma/client';
import { z } from 'zod';

// Initialize Redis client
const redis = new Redis({
  url: process.env.REDIS_URL || '',
  token: process.env.REDIS_TOKEN || '',
});

// Initialize Prisma client
const prisma = new PrismaClient();

// Tracking types
const TrackingType = z.enum(['open', 'click']);
type TrackingType = z.infer<typeof TrackingType>;

/**
 * Handle tracking requests for email opens and clicks
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { type: string; messageId: string } }
) {
  try {
    // Validate tracking type
    const type = TrackingType.parse(params.type);
    const messageId = params.messageId;

    // Get IP address for analytics
    const ip = request.headers.get('x-forwarded-for') ||
               request.headers.get('x-real-ip') ||
               'unknown';

    // Get user agent for analytics
    const userAgent = request.headers.get('user-agent') || 'unknown';

    // Track the event
    await trackEvent(type, messageId, ip, userAgent, request);

    if (type === 'open') {
      // For opens, return a 1x1 transparent pixel
      return new NextResponse(getTransparentPixel(), {
        headers: {
          'Content-Type': 'image/gif',
          'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      });
    } else if (type === 'click') {
      // For clicks, redirect to the original URL
      const url = new URL(request.url).searchParams.get('url');
      if (!url) {
        return NextResponse.json({ error: 'Missing URL parameter' }, { status: 400 });
      }

      return NextResponse.redirect(url);
    }

    return NextResponse.json({ error: 'Invalid tracking type' }, { status: 400 });
  } catch (error) {
    console.error('Tracking error:', error);

    // Don't expose errors to the client for tracking requests
    if (params.type === 'open') {
      return new NextResponse(getTransparentPixel(), {
        headers: { 'Content-Type': 'image/gif' },
      });
    } else if (params.type === 'click') {
      // Fallback URL if there's an error
      return NextResponse.redirect('/');
    }

    return NextResponse.json({ error: 'Tracking failed' }, { status: 500 });
  }
}

/**
 * Track an email event (open or click)
 */
async function trackEvent(
  type: TrackingType,
  messageId: string,
  ip: string,
  userAgent: string,
  request: NextRequest
) {
  // Create a unique key for rate limiting
  const rateLimitKey = `tracking:${type}:${messageId}:${ip}`;

  // Check if this event was already tracked recently (5 min rate limit)
  const isRateLimited = await redis.get(rateLimitKey);
  if (isRateLimited) {
    return;
  }

  // Set rate limit for 5 minutes
  await redis.set(rateLimitKey, 'true', { ex: 300 });

  try {
    // Find the email record
    const email = await prisma.email.findFirst({
      where: { message_id: messageId },
      include: { campaign: true },
    });

    if (!email) {
      console.warn(`Email not found for message ID: ${messageId}`);
      return;
    }

    // Update the email record based on the event type
    if (type === 'open') {
      await prisma.email.update({
        where: { id: email.id },
        data: {
          opened: true,
          opened_at: new Date(),
          open_count: { increment: 1 },
        },
      });

      // Update campaign metrics
      await updateCampaignMetrics(email.campaign_id);
    } else if (type === 'click') {
      const url = new URL(request.url).searchParams.get('url') || '';

      await prisma.email.update({
        where: { id: email.id },
        data: {
          clicked: true,
          clicked_at: new Date(),
          click_count: { increment: 1 },
        },
      });

      // Record the click
      await prisma.click.create({
        data: {
          email_id: email.id,
          url,
          ip,
          user_agent: userAgent,
        },
      });

      // Update campaign metrics
      await updateCampaignMetrics(email.campaign_id);
    }
  } catch (error) {
    console.error(`Error tracking ${type} event:`, error);
    // Don't throw, as we don't want to break the user experience
  }
}

/**
 * Update campaign metrics after an event
 */
async function updateCampaignMetrics(campaignId: number) {
  try {
    // Get all emails for this campaign
    const emails = await prisma.email.findMany({
      where: { campaign_id: campaignId },
    });

    // Calculate metrics
    const totalEmails = emails.length;
    const openedEmails = emails.filter(email => email.opened).length;
    const clickedEmails = emails.filter(email => email.clicked).length;

    // Update campaign metrics
    await prisma.campaign.update({
      where: { id: campaignId },
      data: {
        open_rate: totalEmails > 0 ? openedEmails / totalEmails : 0,
        click_rate: totalEmails > 0 ? clickedEmails / totalEmails : 0,
        last_activity: new Date(),
      },
    });

    // Invalidate analytics cache
    await redis.del(`analytics:${campaignId}`);
  } catch (error) {
    console.error('Error updating campaign metrics:', error);
  }
}

/**
 * Generate a 1x1 transparent GIF pixel
 */
function getTransparentPixel() {
  // 1x1 transparent GIF
  const pixel = Buffer.from(
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
    'base64'
  );
  return pixel;
}
