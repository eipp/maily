import { executeQuery } from '@/lib/apollo-server';
import { GET_CAMPAIGN } from '@/graphql/queries';
import { formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  CalendarIcon,
  Clock4Icon,
  CopyIcon,
  MailIcon,
  SendIcon,
  UsersIcon
} from 'lucide-react';

interface CampaignDetailProps {
  id: string;
}

interface CampaignStats {
  sent: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
}

interface Campaign {
  id: string;
  name: string;
  subject: string;
  previewText: string;
  status: string;
  createdAt: string;
  scheduledFor: string | null;
  sentAt: string | null;
  stats: CampaignStats;
  template: {
    id: string;
    name: string;
  };
  segment: {
    id: string;
    name: string;
    count: number;
  };
}

interface CampaignData {
  campaign: Campaign;
}

export async function CampaignDetail({ id }: CampaignDetailProps) {
  try {
    const data = await executeQuery<CampaignData>(GET_CAMPAIGN, { id });
    const campaign = data.campaign;

    if (!campaign) {
      return (
        <div className="text-center py-12">
          <p className="text-destructive">Campaign not found</p>
        </div>
      );
    }

    // Calculate statistics
    const openRate = campaign.stats.sent > 0
      ? ((campaign.stats.opened / campaign.stats.sent) * 100).toFixed(1)
      : '0';
    const clickRate = campaign.stats.sent > 0
      ? ((campaign.stats.clicked / campaign.stats.sent) * 100).toFixed(1)
      : '0';
    const bounceRate = campaign.stats.sent > 0
      ? ((campaign.stats.bounced / campaign.stats.sent) * 100).toFixed(1)
      : '0';

    const getStatusColor = () => {
      switch (campaign.status.toLowerCase()) {
        case 'draft': return 'text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-300';
        case 'scheduled': return 'text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-300';
        case 'sending': return 'text-amber-600 bg-amber-100 dark:bg-amber-900 dark:text-amber-300';
        case 'sent': return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300';
        case 'failed': return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300';
        default: return 'text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-300';
      }
    };

    return (
      <>
        <div className="bg-background rounded-lg border p-6">
          <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold">{campaign.name}</h1>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
                  {campaign.status}
                </span>
              </div>
              <p className="text-muted-foreground">
                <span className="font-medium">Subject:</span> {campaign.subject}
              </p>
              {campaign.previewText && (
                <p className="text-muted-foreground">
                  <span className="font-medium">Preview:</span> {campaign.previewText}
                </p>
              )}
              <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mt-2">
                <div className="flex items-center">
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  Created {formatDate(campaign.createdAt)}
                </div>
                {campaign.scheduledFor && (
                  <div className="flex items-center">
                    <Clock4Icon className="mr-2 h-4 w-4" />
                    Scheduled for {formatDate(campaign.scheduledFor)}
                  </div>
                )}
                {campaign.sentAt && (
                  <div className="flex items-center">
                    <SendIcon className="mr-2 h-4 w-4" />
                    Sent on {formatDate(campaign.sentAt)}
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {campaign.status === 'DRAFT' && (
                <>
                  <Button>
                    <SendIcon className="mr-2 h-4 w-4" />
                    Send Now
                  </Button>
                  <Button variant="outline">
                    <Clock4Icon className="mr-2 h-4 w-4" />
                    Schedule
                  </Button>
                </>
              )}
              <Button variant="outline">
                <CopyIcon className="mr-2 h-4 w-4" />
                Duplicate
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-background rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Sent</h3>
              <MailIcon className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-3xl font-bold mt-2">{campaign.stats.sent.toLocaleString()}</p>
          </div>

          <div className="bg-background rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Open Rate</h3>
              <div className="h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-xs font-medium text-blue-600">{openRate}%</span>
              </div>
            </div>
            <p className="text-3xl font-bold mt-2">{campaign.stats.opened.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">{openRate}% of total sent</p>
          </div>

          <div className="bg-background rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Click Rate</h3>
              <div className="h-5 w-5 rounded-full bg-green-100 flex items-center justify-center">
                <span className="text-xs font-medium text-green-600">{clickRate}%</span>
              </div>
            </div>
            <p className="text-3xl font-bold mt-2">{campaign.stats.clicked.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">{clickRate}% of total sent</p>
          </div>

          <div className="bg-background rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Bounce Rate</h3>
              <div className="h-5 w-5 rounded-full bg-red-100 flex items-center justify-center">
                <span className="text-xs font-medium text-red-600">{bounceRate}%</span>
              </div>
            </div>
            <p className="text-3xl font-bold mt-2">{campaign.stats.bounced.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">{bounceRate}% of total sent</p>
          </div>
        </div>
      </>
    );
  } catch (error) {
    console.error('Failed to fetch campaign:', error);
    return (
      <div className="text-center py-8">
        <p className="text-destructive">Error loading campaign. Please try again later.</p>
        <Button variant="outline" className="mt-4">
          Retry
        </Button>
      </div>
    );
  }
}
