'use server';

import Link from 'next/link';
import { formatDate } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight, Edit, Eye } from 'lucide-react';

interface Campaign {
  id: string;
  name: string;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'canceled';
  scheduledAt: string | null;
  sentAt: string | null;
  openRate: number | null;
  clickRate: number | null;
  totalRecipients: number;
}

async function getRecentCampaigns(): Promise<Campaign[]> {
  // In a real implementation, this would fetch from an API
  await new Promise(resolve => setTimeout(resolve, 1500));

  return [
    {
      id: 'camp_1',
      name: 'Summer Product Launch',
      status: 'sent',
      scheduledAt: null,
      sentAt: '2023-06-25T14:30:00Z',
      openRate: 32.8,
      clickRate: 5.4,
      totalRecipients: 5400,
    },
    {
      id: 'camp_2',
      name: 'Monthly Newsletter - July',
      status: 'scheduled',
      scheduledAt: '2023-07-10T09:00:00Z',
      sentAt: null,
      openRate: null,
      clickRate: null,
      totalRecipients: 8500,
    },
    {
      id: 'camp_3',
      name: 'Special Discount Promotion',
      status: 'draft',
      scheduledAt: null,
      sentAt: null,
      openRate: null,
      clickRate: null,
      totalRecipients: 0,
    },
    {
      id: 'camp_4',
      name: 'Product Update - New Features',
      status: 'sent',
      scheduledAt: null,
      sentAt: '2023-06-10T08:15:00Z',
      openRate: 28.5,
      clickRate: 4.2,
      totalRecipients: 4800,
    },
    {
      id: 'camp_5',
      name: 'Customer Feedback Survey',
      status: 'sending',
      scheduledAt: null,
      sentAt: '2023-07-01T12:00:00Z',
      openRate: 18.3,
      clickRate: 2.7,
      totalRecipients: 7200,
    },
  ];
}

function getCampaignStatusBadge(status: Campaign['status']) {
  const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";

  switch (status) {
    case 'draft':
      return <span className={`${baseClasses} bg-gray-100 text-gray-800`}>Draft</span>;
    case 'scheduled':
      return <span className={`${baseClasses} bg-blue-100 text-blue-800`}>Scheduled</span>;
    case 'sending':
      return <span className={`${baseClasses} bg-yellow-100 text-yellow-800 animate-pulse`}>Sending</span>;
    case 'sent':
      return <span className={`${baseClasses} bg-green-100 text-green-800`}>Sent</span>;
    case 'canceled':
      return <span className={`${baseClasses} bg-red-100 text-red-800`}>Canceled</span>;
    default:
      return null;
  }
}

export default async function RecentCampaigns() {
  const campaigns = await getRecentCampaigns();

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Campaigns</CardTitle>
        <Link href="/dashboard/campaigns">
          <Button variant="ghost" size="sm" className="gap-1">
            View All
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {campaigns.map((campaign) => (
            <div key={campaign.id} className="flex items-start justify-between">
              <div className="space-y-1">
                <h3 className="font-medium">{campaign.name}</h3>
                <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                  {getCampaignStatusBadge(campaign.status)}
                  <span>
                    {campaign.status === 'sent' && campaign.sentAt
                      ? `Sent on ${formatDate(campaign.sentAt)}`
                      : campaign.status === 'scheduled' && campaign.scheduledAt
                      ? `Scheduled for ${formatDate(campaign.scheduledAt)}`
                      : campaign.status === 'sending'
                      ? `Started on ${formatDate(campaign.sentAt!)}`
                      : 'Not scheduled'}
                  </span>
                  {campaign.openRate !== null && (
                    <span>Open: {campaign.openRate}%</span>
                  )}
                  {campaign.clickRate !== null && (
                    <span>Click: {campaign.clickRate}%</span>
                  )}
                </div>
              </div>

              <Link href={`/dashboard/campaigns/${campaign.id}`}>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-1"
                >
                  {campaign.status === 'draft' ? (
                    <>
                      <Edit className="h-3.5 w-3.5" />
                      Edit
                    </>
                  ) : (
                    <>
                      <Eye className="h-3.5 w-3.5" />
                      View
                    </>
                  )}
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
