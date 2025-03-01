'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'react-hot-toast';
import { TemplateEditor } from '../../../components/Templates/TemplateEditor';
import LoadingSpinner from '../../../components/ui/LoadingSpinner';
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeftIcon, PencilIcon, CopyIcon, MailIcon } from 'lucide-react';
import { TemplateDetail } from './template-detail';
import { TemplateDetailSkeleton } from './template-detail-skeleton';

export const metadata = {
  title: 'Template Details | Maily',
  description: 'View and manage email template details',
};

interface TemplateDetailPageProps {
  params: {
    id: string;
  };
}

export default function TemplateDetailPage({ params }: TemplateDetailPageProps) {
  // Check if template ID is valid format
  if (!/^[a-zA-Z0-9-]+$/.test(params.id)) {
    notFound();
  }

  return (
    <div className="container py-8 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/templates">
            <ArrowLeftIcon className="mr-2 h-4 w-4" />
            Back to Templates
          </Link>
        </Button>

        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" asChild>
            <Link href={`/templates/${params.id}/edit`}>
              <PencilIcon className="mr-2 h-4 w-4" />
              Edit
            </Link>
          </Button>
          <Button size="sm" variant="outline">
            <CopyIcon className="mr-2 h-4 w-4" />
            Duplicate
          </Button>
          <Button size="sm">
            <MailIcon className="mr-2 h-4 w-4" />
            Use in Campaign
          </Button>
        </div>
      </div>

      <Suspense fallback={<TemplateDetailSkeleton />}>
        <TemplateDetail id={params.id} />
      </Suspense>
    </div>
  );
}
