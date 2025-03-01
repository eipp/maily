import Link from 'next/link';
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { CampaignForm } from '../../campaign-form';
import { CampaignFormSkeleton } from '../../campaign-form-skeleton';
import { Button } from '@/components/ui/button';
import { ArrowLeftIcon } from 'lucide-react';

export const metadata = {
  title: 'Edit Campaign | Maily',
  description: 'Modify your existing email marketing campaign',
};

interface EditCampaignPageProps {
  params: {
    id: string;
  };
}

export default function EditCampaignPage({ params }: EditCampaignPageProps) {
  // Check if campaign ID is valid format (e.g., UUID)
  if (!/^[a-zA-Z0-9-]+$/.test(params.id)) {
    notFound();
  }

  return (
    <div className="container py-8 space-y-6">
      <div className="flex items-center gap-2 mb-6">
        <Button variant="ghost" size="sm" asChild>
          <Link href={`/campaigns/${params.id}`}>
            <ArrowLeftIcon className="mr-2 h-4 w-4" />
            Back to Campaign
          </Link>
        </Button>
      </div>

      <div className="bg-background rounded-lg border p-6">
        <h1 className="text-2xl font-bold mb-6">Edit Campaign</h1>
        <Suspense fallback={<CampaignFormSkeleton />}>
          <CampaignForm campaignId={params.id} />
        </Suspense>
      </div>
    </div>
  );
}
