'use server';

import { formatNumber } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpRight, Users, Mail, MousePointerClick } from 'lucide-react';

async function getStats() {
  // In a real implementation, this would fetch from an API or database
  // Simulate API call latency
  await new Promise(resolve => setTimeout(resolve, 1000));

  return {
    totalSubscribers: 24580,
    subscribersGrowth: 12.5,
    emailsSent: 156432,
    emailsSentGrowth: 8.2,
    clickRate: 3.6,
    clickRateGrowth: 1.2,
  };
}

export default async function DashboardStats() {
  const stats = await getStats();

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            Total Subscribers
          </CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatNumber(stats.totalSubscribers)}</div>
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
            <span className="text-green-500 flex items-center">
              <ArrowUpRight className="h-3 w-3" />
              {stats.subscribersGrowth}%
            </span>
            from last month
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            Emails Sent
          </CardTitle>
          <Mail className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatNumber(stats.emailsSent)}</div>
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
            <span className="text-green-500 flex items-center">
              <ArrowUpRight className="h-3 w-3" />
              {stats.emailsSentGrowth}%
            </span>
            from last month
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            Average Click Rate
          </CardTitle>
          <MousePointerClick className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.clickRate}%</div>
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
            <span className="text-green-500 flex items-center">
              <ArrowUpRight className="h-3 w-3" />
              {stats.clickRateGrowth}%
            </span>
            from last month
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
