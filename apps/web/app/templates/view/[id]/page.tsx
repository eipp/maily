'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { toast } from 'react-hot-toast';
import { TemplatePreview } from '../../../../components/Templates/TemplatePreview';
import LoadingSpinner from '../../../../components/ui/LoadingSpinner';

export default function ViewTemplatePage() {
  const params = useParams() || {};
  const router = useRouter();
  const id = params.id as string;

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [templateExists, setTemplateExists] = useState<boolean>(false);
  const [templateName, setTemplateName] = useState<string>('');

  useEffect(() => {
    if (id) {
      // Check if template exists
      const checkTemplate = async () => {
        try {
          const response = await fetch(`/api/templates/${id}`);
          if (response.ok) {
            const data = await response.json();
            setTemplateExists(true);
            setTemplateName(data.name);
          } else {
            toast.error('Template not found');
            router.push('/templates');
          }
        } catch (error) {
          console.error('Error checking template:', error);
          toast.error('Error fetching template');
        } finally {
          setIsLoading(false);
        }
      };

      checkTemplate();
    }
  }, [id, router]);

  const handleBack = () => {
    router.push('/templates');
  };

  const handleEdit = (templateId: number) => {
    router.push(`/templates/${templateId}?mode=edit`);
  };

  const handleDuplicate = (templateId: number) => {
    router.push(`/templates/${templateId}`);
  };

  const handleDelete = () => {
    router.push('/templates');
  };

  if (isLoading) {
    return (
      <div className="flex justify-center my-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {templateExists && id && (
        <TemplatePreview
          templateId={Number(id)}
          onBack={handleBack}
          onEdit={handleEdit}
          onDuplicate={handleDuplicate}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}
