import Link from 'next/link';
import { executeQuery } from '@/lib/apollo-server';
import { GET_CAMPAIGNS } from '@/graphql/queries';
import { formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  BarChart2Icon,
  EditIcon,
  MailIcon,
  MoreHorizontalIcon,
  TrashIcon,
} from 'lucide-react';

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
    const data = await executeQuery<CampaignsData>(GET_CAMPAIGNS, { page: 1, pageSize: 20 });
    const campaigns = data.campaigns || [];

    if (campaigns.length === 0) {
      return (
        <div className="text-center py-12">
          <MailIcon className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium">No campaigns yet</h3>
          <p className="text-muted-foreground mt-2">
            Get started by creating your first email campaign.
          </p>
          <Button className="mt-4" asChild>
            <Link href="/campaigns/new">Create Campaign</Link>
          </Button>
        </div>
      );
    }

    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Subject</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created</TableHead>
            <TableHead>Open Rate</TableHead>
            <TableHead>Click Rate</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {campaigns.map((campaign) => {
            const openRate = campaign.stats.sent > 0
              ? Math.round((campaign.stats.opened / campaign.stats.sent) * 100)
              : 0;

            const clickRate = campaign.stats.sent > 0
              ? Math.round((campaign.stats.clicked / campaign.stats.sent) * 100)
              : 0;

            return (
              <TableRow key={campaign.id}>
                <TableCell className="font-medium">
                  <Link
                    href={`/campaigns/${campaign.id}`}
                    className="hover:underline"
                  >
                    {campaign.name}
                  </Link>
                </TableCell>
                <TableCell className="max-w-xs truncate">
                  {campaign.subject}
                </TableCell>
                <TableCell>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusClass(campaign.status)}`}>
                    {campaign.status}
                  </span>
                </TableCell>
                <TableCell>{formatDate(campaign.createdAt)}</TableCell>
                <TableCell>{openRate}%</TableCell>
                <TableCell>{clickRate}%</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      asChild
                    >
                      <Link href={`/campaigns/${campaign.id}/stats`}>
                        <BarChart2Icon className="h-4 w-4" />
                        <span className="sr-only">View Stats</span>
                      </Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      asChild
                    >
                      <Link href={`/campaigns/${campaign.id}/edit`}>
                        <EditIcon className="h-4 w-4" />
                        <span className="sr-only">Edit</span>
                      </Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive"
                    >
                      <TrashIcon className="h-4 w-4" />
                      <span className="sr-only">Delete</span>
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    );
  } catch (error) {
    console.error('Failed to fetch campaigns:', error);
    return (
      <div className="text-center py-8">
        <p className="text-destructive">Error loading campaigns. Please try again later.</p>
        <Button variant="outline" className="mt-4">
          Retry
        </Button>
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
