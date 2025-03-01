import Link from 'next/link';
import { executeQuery } from '@/lib/apollo-server';
import { GET_SUBSCRIBERS } from '@/graphql/queries';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  MoreHorizontalIcon,
  PencilIcon,
  TagIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
} from 'lucide-react';
import { formatDate } from '@/lib/utils';

interface SubscriberTag {
  id: string;
  name: string;
}

interface Subscriber {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  isActive: boolean;
  joinedAt: string;
  lastActivity: string;
  tags: SubscriberTag[];
  engagementScore: number;
}

interface SubscribersData {
  subscribers: Subscriber[];
}

export async function SubscribersList() {
  try {
    const data = await executeQuery<SubscribersData>(GET_SUBSCRIBERS);
    const subscribers = data.subscribers;

    if (!subscribers || subscribers.length === 0) {
      return (
        <div className="text-center py-12 border rounded-lg bg-background">
          <h3 className="text-lg font-medium">No subscribers found</h3>
          <p className="text-muted-foreground mt-2">
            Add your first subscriber or import a list to get started
          </p>
          <div className="mt-6 flex justify-center gap-4">
            <Button asChild>
              <Link href="/subscribers/new">Add Subscriber</Link>
            </Button>
            <Button variant="outline">Import CSV</Button>
          </div>
        </div>
      );
    }

    const getEngagementColor = (score: number) => {
      if (score >= 80) return 'text-green-600';
      if (score >= 50) return 'text-amber-600';
      return 'text-red-600';
    };

    return (
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[300px]">Subscriber</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Joined</TableHead>
              <TableHead>Last Activity</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>Engagement</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {subscribers.map((subscriber) => (
              <TableRow key={subscriber.id}>
                <TableCell className="font-medium">
                  <div>
                    <Link href={`/subscribers/${subscriber.id}`} className="hover:underline">
                      {subscriber.firstName} {subscriber.lastName}
                    </Link>
                    <div className="text-sm text-muted-foreground">{subscriber.email}</div>
                  </div>
                </TableCell>
                <TableCell>
                  {subscriber.isActive ? (
                    <div className="flex items-center text-green-600">
                      <CheckCircleIcon className="mr-1 h-4 w-4" />
                      <span className="text-sm">Active</span>
                    </div>
                  ) : (
                    <div className="flex items-center text-red-600">
                      <XCircleIcon className="mr-1 h-4 w-4" />
                      <span className="text-sm">Inactive</span>
                    </div>
                  )}
                </TableCell>
                <TableCell>{formatDate(subscriber.joinedAt)}</TableCell>
                <TableCell>{formatDate(subscriber.lastActivity)}</TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {subscriber.tags.slice(0, 2).map((tag) => (
                      <Badge key={tag.id} variant="outline">
                        {tag.name}
                      </Badge>
                    ))}
                    {subscriber.tags.length > 2 && (
                      <Badge variant="outline">+{subscriber.tags.length - 2}</Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className={`font-medium ${getEngagementColor(subscriber.engagementScore)}`}>
                    {subscriber.engagementScore}%
                  </div>
                  <div className="w-full h-1.5 bg-gray-100 rounded-full mt-1">
                    <div
                      className={`h-full rounded-full ${
                        subscriber.engagementScore >= 80
                          ? 'bg-green-500'
                          : subscriber.engagementScore >= 50
                            ? 'bg-amber-500'
                            : 'bg-red-500'
                      }`}
                      style={{ width: `${subscriber.engagementScore}%` }}
                    />
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button variant="ghost" size="icon" asChild>
                      <Link href={`/subscribers/${subscriber.id}/edit`}>
                        <PencilIcon className="h-4 w-4" />
                        <span className="sr-only">Edit</span>
                      </Link>
                    </Button>
                    <Button variant="ghost" size="icon">
                      <TagIcon className="h-4 w-4" />
                      <span className="sr-only">Tags</span>
                    </Button>
                    <Button variant="ghost" size="icon">
                      <TrashIcon className="h-4 w-4" />
                      <span className="sr-only">Delete</span>
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <div className="py-4 px-6 border-t flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Showing 1-{Math.min(subscribers.length, 10)} of {subscribers.length} subscribers
          </div>
          <div className="flex gap-1">
            <Button variant="outline" size="sm" disabled>
              Previous
            </Button>
            <Button variant="outline" size="sm">
              Next
            </Button>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Failed to fetch subscribers:', error);
    return (
      <div className="text-center py-8 border rounded-lg bg-background">
        <p className="text-destructive">Error loading subscribers. Please try again later.</p>
        <Button variant="outline" className="mt-4">
          Retry
        </Button>
      </div>
    );
  }
}
