import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/router';
import { NextPage } from 'next';
import { toast } from 'react-hot-toast';
import Head from 'next/head';
import { DashboardLayout } from '../../../components/Layout/DashboardLayout';
import { TemplatePreview } from '../../../components/Templates/TemplatePreview';
import { withAuth } from '../../../utils/withAuth';

const ViewTemplatePage: NextPage = () => {
  const { t } = useTranslation();
  const router = useRouter();
  const { id } = router.query;

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [templateExists, setTemplateExists] = useState<boolean>(false);
  const [templateName, setTemplateName] = useState<string>('');

  useEffect(() => {
    if (router.isReady && id) {
      // Check if template exists
      const checkTemplate = async () => {
        try {
          const response = await fetch(`/api/templates/${id}`);
          if (response.ok) {
            const data = await response.json();
            setTemplateExists(true);
            setTemplateName(data.name);
          } else {
            toast.error(t('templates.notFound'));
            router.push('/templates');
          }
        } catch (error) {
          console.error('Error checking template:', error);
          toast.error(t('templates.fetchError'));
        } finally {
          setIsLoading(false);
        }
      };

      checkTemplate();
    }
  }, [id, router.isReady, router, t]);

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
      <DashboardLayout>
        <div className="flex justify-center my-12">
          <div className="size-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Head>
        <title>
          {templateName ? `${templateName} | ` : ''}{t('templates.viewTemplate')} | Maily
        </title>
      </Head>

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
    </DashboardLayout>
  );
};

export default withAuth(ViewTemplatePage);
