import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeftIcon, EditIcon } from 'lucide-react';
import { SubscriberDetail } from './subscriber-detail';
import { SubscriberDetailSkeleton } from './subscriber-detail-skeleton';
import { SubscriberActivity } from './subscriber-activity';
import { SubscriberActivitySkeleton } from './subscriber-activity-skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export const metadata = {
  title: 'Subscriber Details | Maily',
  description: 'View detailed information about a subscriber',
};

interface SubscriberDetailPageProps {
  params: {
    id: string;
  };
}

export default function SubscriberDetailPage({ params }: SubscriberDetailPageProps) {
  // Check if subscriber ID is valid format (e.g., UUID)
  if (!/^[a-zA-Z0-9-]+$/.test(params.id)) {
    notFound();
  }

  return (
    <div className="container py-8 space-y-6">
      <div className="flex items-center gap-2 mb-6">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/subscribers">
            <ArrowLeftIcon className="mr-2 h-4 w-4" />
            Back to Subscribers
          </Link>
        </Button>
      </div>

      <Suspense fallback={<SubscriberDetailSkeleton />}>
        <SubscriberDetail id={params.id} />
      </Suspense>

      <div className="mt-8">
        <Tabs defaultValue="activity" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="activity">Activity History</TabsTrigger>
            <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
            <TabsTrigger value="preferences">Preferences</TabsTrigger>
            <TabsTrigger value="custom">Custom Fields</TabsTrigger>
          </TabsList>

          <TabsContent value="activity" className="space-y-6">
            <Suspense fallback={<SubscriberActivitySkeleton />}>
              <SubscriberActivity id={params.id} />
            </Suspense>
          </TabsContent>

          <TabsContent value="campaigns">
            <div className="bg-background rounded-lg border p-6">
              <h3 className="text-lg font-medium mb-4">Campaign History</h3>
              <div className="space-y-4">
                <div className="border rounded-md p-4 flex items-center">
                  <div>
                    <h4 className="font-medium">Monthly Newsletter - February 2025</h4>
                    <p className="text-sm text-muted-foreground">Sent February 15, 2025</p>
                  </div>
                  <div className="ml-auto text-right">
                    <div className="text-green-600 text-sm font-medium">Opened</div>
                    <div className="text-green-600 text-sm font-medium">Clicked</div>
                  </div>
                </div>
                <div className="border rounded-md p-4 flex items-center">
                  <div>
                    <h4 className="font-medium">Product Update - January 2025</h4>
                    <p className="text-sm text-muted-foreground">Sent January 20, 2025</p>
                  </div>
                  <div className="ml-auto text-right">
                    <div className="text-green-600 text-sm font-medium">Opened</div>
                    <div className="text-red-600 text-sm font-medium">Not Clicked</div>
                  </div>
                </div>
                <div className="border rounded-md p-4 flex items-center">
                  <div>
                    <h4 className="font-medium">Year-end Recap - December 2024</h4>
                    <p className="text-sm text-muted-foreground">Sent December 28, 2024</p>
                  </div>
                  <div className="ml-auto text-right">
                    <div className="text-red-600 text-sm font-medium">Not Opened</div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="preferences">
            <div className="bg-background rounded-lg border p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium">Subscription Preferences</h3>
                <Button variant="outline" size="sm">
                  <EditIcon className="mr-2 h-4 w-4" />
                  Edit Preferences
                </Button>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Email Frequency</p>
                    <p className="font-medium">Weekly updates</p>
                  </div>
                  <div className="p-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Content Preferences</p>
                    <p className="font-medium">Product updates, Industry news</p>
                  </div>
                  <div className="p-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Unsubscribed Categories</p>
                    <p className="font-medium">Promotional offers</p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="custom">
            <div className="bg-background rounded-lg border p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium">Custom Fields</h3>
                <Button variant="outline" size="sm">
                  <EditIcon className="mr-2 h-4 w-4" />
                  Edit Fields
                </Button>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Company</p>
                    <p className="font-medium">Acme Inc.</p>
                  </div>
                  <div className="p-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Job Title</p>
                    <p className="font-medium">Marketing Manager</p>
                  </div>
                  <div className="p-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Industry</p>
                    <p className="font-medium">Technology</p>
                  </div>
                  <div className="p-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Company Size</p>
                    <p className="font-medium">50-100 employees</p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
