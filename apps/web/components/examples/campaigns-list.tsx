import { executeQuery } from '@/lib/apollo-server';
import { GET_CAMPAIGNS } from '@/graphql/queries';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { formatDate } from '@/lib/utils';

interface CampaignStats {
  sent: number;
  opened: number;
  clicked: number;
}

interface Campaign {
  id: string;
  name: string;
  subject: string;
  status: string;
  createdAt: string;
  stats: CampaignStats;
}

interface CampaignsData {
  campaigns: Campaign[];
}

export async function CampaignsList() {
  try {
    const data = await executeQuery<CampaignsData>(GET_CAMPAIGNS, { page: 1, pageSize: 10 });
    const campaigns = data.campaigns || [];

    if (campaigns.length === 0) {
      return (
        <div className="bg-background p-6 rounded-lg border border-border">
          <h2 className="text-xl font-semibold mb-4">Recent Campaigns</h2>
          <p className="text-muted-foreground">No campaigns found. Create your first campaign to get started.</p>
        </div>
      );
    }

    return (
      <div className="bg-background p-6 rounded-lg border border-border">
        <h2 className="text-xl font-semibold mb-4">Recent Campaigns</h2>
        <Table>
          <TableCaption>List of your recent campaigns</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Subject</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="text-right">Open Rate</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {campaigns.map((campaign) => {
              const openRate = campaign.stats.sent > 0
                ? (campaign.stats.opened / campaign.stats.sent) * 100
                : 0;

              return (
                <TableRow key={campaign.id}>
                  <TableCell className="font-medium">{campaign.name}</TableCell>
                  <TableCell>{campaign.subject}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusClass(campaign.status)}`}>
                      {campaign.status}
                    </span>
                  </TableCell>
                  <TableCell>{formatDate(campaign.createdAt)}</TableCell>
                  <TableCell className="text-right">{openRate.toFixed(1)}%</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    );
  } catch (error) {
    console.error('Failed to fetch campaigns:', error);
    return (
      <div className="bg-background p-6 rounded-lg border border-border">
        <h2 className="text-xl font-semibold mb-4">Recent Campaigns</h2>
        <p className="text-destructive">Error loading campaigns. Please try again later.</p>
      </div>
    );
  }
}

function getStatusClass(status: string): string {
  switch (status.toLowerCase()) {
    case 'draft':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    case 'scheduled':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
    case 'sending':
      return 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300';
    case 'sent':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    case 'failed':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
  }
}
