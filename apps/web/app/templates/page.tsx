import { Suspense } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { PlusIcon, SearchIcon, FilterIcon, DownloadIcon } from 'lucide-react';
import { TemplatesList } from './templates-list';
import { TemplatesListSkeleton } from './templates-list-skeleton';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

export const metadata = {
  title: 'Email Templates | Maily',
  description: 'Create and manage your email templates',
};

export default function TemplatesPage() {
  return (
    <div className="container py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Email Templates</h1>
          <p className="text-muted-foreground mt-1">
            Create reusable email templates for your marketing campaigns
          </p>
        </div>
        <Button asChild>
          <Link href="/templates/new">
            <PlusIcon className="mr-2 h-4 w-4" />
            Create Template
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
                placeholder="Search templates..."
                className="pl-8"
              />
            </div>

            <div className="border-t pt-4">
              <h3 className="font-medium mb-3 flex items-center">
                <FilterIcon className="mr-2 h-4 w-4" />
                Categories
              </h3>
              <div className="space-y-2">
                <div className="flex items-center">
                  <input type="checkbox" id="cat-newsletters" className="mr-2" />
                  <label htmlFor="cat-newsletters" className="text-sm">Newsletters</label>
                  <span className="ml-auto text-xs text-muted-foreground">18</span>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" id="cat-promotions" className="mr-2" />
                  <label htmlFor="cat-promotions" className="text-sm">Promotions</label>
                  <span className="ml-auto text-xs text-muted-foreground">12</span>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" id="cat-onboarding" className="mr-2" />
                  <label htmlFor="cat-onboarding" className="text-sm">Onboarding</label>
                  <span className="ml-auto text-xs text-muted-foreground">8</span>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" id="cat-events" className="mr-2" />
                  <label htmlFor="cat-events" className="text-sm">Events</label>
                  <span className="ml-auto text-xs text-muted-foreground">5</span>
                </div>
                <div className="flex items-center">
                  <input type="checkbox" id="cat-transactional" className="mr-2" />
                  <label htmlFor="cat-transactional" className="text-sm">Transactional</label>
                  <span className="ml-auto text-xs text-muted-foreground">7</span>
                </div>
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="font-medium mb-3">Created By</h3>
              <div className="space-y-2">
                <div className="flex items-center">
                  <input type="radio" name="creator" id="creator-all" className="mr-2" checked />
                  <label htmlFor="creator-all" className="text-sm">All Templates</label>
                </div>
                <div className="flex items-center">
                  <input type="radio" name="creator" id="creator-me" className="mr-2" />
                  <label htmlFor="creator-me" className="text-sm">Created by Me</label>
                </div>
                <div className="flex items-center">
                  <input type="radio" name="creator" id="creator-system" className="mr-2" />
                  <label htmlFor="creator-system" className="text-sm">System Templates</label>
                </div>
              </div>
            </div>

            <div className="border-t pt-4">
              <Button variant="outline" size="sm" className="w-full">
                <DownloadIcon className="mr-2 h-4 w-4" />
                Export Templates
              </Button>
            </div>
          </div>
        </Card>

        <div className="md:col-span-3 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-muted-foreground">
                Showing <strong>50</strong> templates
              </span>
            </div>
            <div className="flex gap-2">
              <select className="px-2 py-1 border rounded text-sm">
                <option>Sort by Newest</option>
                <option>Sort by Name</option>
                <option>Sort by Last Used</option>
                <option>Sort by Popularity</option>
              </select>
            </div>
          </div>

          <Suspense fallback={<TemplatesListSkeleton />}>
            <TemplatesList />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
