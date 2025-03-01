import { Suspense } from 'react';
import { Metadata } from 'next';
import DashboardStats from '@/components/dashboard/dashboard-stats';
import DashboardCharts from '@/components/dashboard/dashboard-charts';
import RecentCampaigns from '@/components/dashboard/recent-campaigns';
import { DashboardSkeleton } from '@/components/dashboard/dashboard-skeleton';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Brush } from 'lucide-react';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Dashboard | Maily',
  description: 'View your email marketing performance and analytics',
};

export default function DashboardPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            View your email marketing performance and analytics
          </p>
        </div>
        <Button asChild>
          <Link href="/canvas/dashboard" className="flex items-center">
            <Brush className="mr-2 h-4 w-4" />
            Canvas Dashboard
          </Link>
        </Button>
      </div>

      <div className="mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Canvas Feature</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4">
              Our new collaborative canvas feature allows you to create and share
              interactive designs with your team in real-time.
            </p>
            <Button asChild variant="outline">
              <Link href="/canvas/dashboard">
                Try Canvas Feature
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <Suspense fallback={<DashboardSkeleton type="stats" />}>
        <DashboardStats />
      </Suspense>

      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
        <Suspense fallback={<DashboardSkeleton type="chart" />}>
          <DashboardCharts type="opens" />
        </Suspense>

        <Suspense fallback={<DashboardSkeleton type="chart" />}>
          <DashboardCharts type="clicks" />
        </Suspense>
      </div>

      <div className="mt-8">
        <Suspense fallback={<DashboardSkeleton type="campaigns" />}>
          <RecentCampaigns />
        </Suspense>
      </div>
    </div>
  );
}
