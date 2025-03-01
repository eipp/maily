import { Suspense } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { PlusIcon, SearchIcon, FilterIcon, TagIcon, DownloadIcon } from 'lucide-react';
import { SubscribersList } from './subscribers-list';
import { SubscribersListSkeleton } from './subscribers-list-skeleton';
import { SubscribersFilter } from './subscribers-filter';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

export const metadata = {
  title: 'Subscribers | Maily',
  description: 'Manage your email subscribers and audience segments',
};

export default function SubscribersPage() {
  return (
    <div className="container py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Subscribers</h1>
          <p className="text-muted-foreground mt-1">
            Manage your contacts and create targeted segments for your campaigns
          </p>
        </div>
        <Button asChild>
          <Link href="/subscribers/new">
            <PlusIcon className="mr-2 h-4 w-4" />
            Add Subscriber
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="md:col-span-1 p-4">
          <div className="space-y-4">
            <div className="relative">
              <SearchIcon className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search subscribers..."
                className="pl-8"
              />
            </div>

            <div className="border-t pt-4">
              <h3 className="font-medium mb-3 flex items-center">
                <FilterIcon className="mr-2 h-4 w-4" />
                Filters
              </h3>
              <Suspense fallback={<div className="h-[200px] flex items-center justify-center">Loading filters...</div>}>
                <SubscribersFilter />
              </Suspense>
            </div>

            <div className="border-t pt-4">
              <h3 className="font-medium mb-3 flex items-center">
                <TagIcon className="mr-2 h-4 w-4" />
                Tags
              </h3>
              <div className="space-y-2">
                <div className="flex items-center">
                  <input type="checkbox" id="tag-newsletter" className="mr-2" />
                  <label htmlFor="tag-newsletter" className="text-sm">Newsletter</label>
                  <span className="ml-auto text-xs text-muted-foreground">1,245</span>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" id="tag-customer" className="mr-2" />
                  <label htmlFor="tag-customer" className="text-sm">Customer</label>
                  <span className="ml-auto text-xs text-muted-foreground">857</span>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" id="tag-vip" className="mr-2" />
                  <label htmlFor="tag-vip" className="text-sm">VIP</label>
                  <span className="ml-auto text-xs text-muted-foreground">123</span>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" id="tag-trial" className="mr-2" />
                  <label htmlFor="tag-trial" className="text-sm">Trial User</label>
                  <span className="ml-auto text-xs text-muted-foreground">412</span>
                </div>
                <Button variant="outline" size="sm" className="w-full mt-2">
                  Manage Tags
                </Button>
              </div>
            </div>

            <div className="border-t pt-4">
              <Button variant="outline" size="sm" className="w-full">
                <DownloadIcon className="mr-2 h-4 w-4" />
                Export CSV
              </Button>
            </div>
          </div>
        </Card>

        <div className="md:col-span-3 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-muted-foreground">
                Showing <strong>2,637</strong> subscribers
              </span>
            </div>
            <div className="flex gap-2">
              <select className="px-2 py-1 border rounded text-sm">
                <option>Sort by Name</option>
                <option>Sort by Date Added</option>
                <option>Sort by Last Activity</option>
              </select>
            </div>
          </div>

          <Suspense fallback={<SubscribersListSkeleton />}>
            <SubscribersList />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
