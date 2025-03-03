import { Suspense } from 'react';
import Link from 'next/link';
import { CampaignsList } from './campaigns-list';
import { CampaignsListSkeleton } from './campaigns-list-skeleton';
import { Button } from '@/components/ui/button';
import { PlusIcon } from 'lucide-react';

export const metadata = {
  title: 'Campaigns | Maily',
  description: 'Create and manage your email marketing campaigns',
};

export default function CampaignsPage() {
  return (
    <div className="container py-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold mb-2">Campaigns</h1>
          <p className="text-muted-foreground">
            Create, send, and track your email marketing campaigns
          </p>
        </div>
        <Button asChild>
          <Link href="/campaigns/new">
            <PlusIcon className="mr-2 h-4 w-4" />
            Create Campaign
          </Link>
        </Button>
      </div>

      {/* Campaign Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-background rounded-lg border p-6">
          <h3 className="text-lg font-medium mb-1">Total Campaigns</h3>
          <p className="text-3xl font-bold">24</p>
        </div>
        <div className="bg-background rounded-lg border p-6">
          <h3 className="text-lg font-medium mb-1">Avg. Open Rate</h3>
          <p className="text-3xl font-bold">24.8%</p>
        </div>
        <div className="bg-background rounded-lg border p-6">
          <h3 className="text-lg font-medium mb-1">Avg. Click Rate</h3>
          <p className="text-3xl font-bold">3.2%</p>
        </div>
      </div>

      {/* Campaigns List */}
      <div className="bg-background rounded-lg border">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">All Campaigns</h2>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                Filter
              </Button>
              <Button variant="outline" size="sm">
                Sort
              </Button>
            </div>
          </div>
          <Suspense fallback={<CampaignsListSkeleton />}>
            <CampaignsList />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
