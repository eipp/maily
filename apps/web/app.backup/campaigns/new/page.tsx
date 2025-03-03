import Link from 'next/link';
import { CampaignForm } from '../campaign-form';
import { Button } from '@/components/ui/button';
import { ArrowLeftIcon } from 'lucide-react';

export const metadata = {
  title: 'Create Campaign | Maily',
  description: 'Create a new email marketing campaign',
};

export default function NewCampaignPage() {
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

      <div className="bg-background rounded-lg border p-6">
        <h1 className="text-2xl font-bold mb-6">Create New Campaign</h1>
        <CampaignForm />
      </div>
    </div>
  );
}
