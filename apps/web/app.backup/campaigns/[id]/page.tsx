import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { CampaignDetail } from './campaign-detail';
import { CampaignDetailSkeleton } from './campaign-detail-skeleton';
import { CampaignStats } from './campaign-stats';
import { CampaignStatsSkeleton } from './campaign-stats-skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { ArrowLeftIcon, EditIcon } from 'lucide-react';

export const metadata = {
  title: 'Campaign Details | Maily',
  description: 'View detailed information and performance metrics for your campaign',
};

interface CampaignDetailPageProps {
  params: {
    id: string;
  };
}

export default function CampaignDetailPage({ params }: CampaignDetailPageProps) {
  // Check if campaign ID is valid format (e.g., UUID)
  if (!/^[a-zA-Z0-9-]+$/.test(params.id)) {
    notFound();
  }

  return (
    <div className="container py-8 space-y-6">
      <div className="flex items-center gap-2 mb-6">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/campaigns">
            <ArrowLeftIcon className="mr-2 h-4 w-4" />
            Back to Campaigns
          </Link>
        </Button>
      </div>

      <Suspense fallback={<CampaignDetailSkeleton />}>
        <CampaignDetail id={params.id} />
      </Suspense>

      <div className="mt-8">
        <Tabs defaultValue="performance" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="content">Content</TabsTrigger>
            <TabsTrigger value="audience">Audience</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="performance" className="space-y-6">
            <Suspense fallback={<CampaignStatsSkeleton />}>
              <CampaignStats id={params.id} />
            </Suspense>
          </TabsContent>

          <TabsContent value="content">
            <div className="bg-background rounded-lg border p-6">
              <h3 className="text-lg font-medium mb-4">Campaign Content</h3>
              <div className="aspect-video bg-muted rounded-md flex items-center justify-center">
                <p className="text-muted-foreground">Email content preview will be displayed here</p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="audience">
            <div className="bg-background rounded-lg border p-6">
              <h3 className="text-lg font-medium mb-4">Audience Details</h3>
              <p className="text-muted-foreground">Information about the audience segments targeted in this campaign</p>
              <div className="mt-4 py-3 px-4 bg-muted rounded-md">
                <p>Total Recipients: <span className="font-medium">1,245</span></p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="settings">
            <div className="bg-background rounded-lg border p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium">Campaign Settings</h3>
                <Button asChild>
                  <Link href={`/campaigns/${params.id}/edit`}>
                    <EditIcon className="mr-2 h-4 w-4" />
                    Edit Campaign
                  </Link>
                </Button>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="py-3 px-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Sender Name</p>
                    <p className="font-medium">Maily Team</p>
                  </div>
                  <div className="py-3 px-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Reply-To</p>
                    <p className="font-medium">support@mailyapp.com</p>
                  </div>
                  <div className="py-3 px-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Track Opens</p>
                    <p className="font-medium">Enabled</p>
                  </div>
                  <div className="py-3 px-4 bg-muted rounded-md">
                    <p className="text-sm text-muted-foreground">Track Clicks</p>
                    <p className="font-medium">Enabled</p>
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
