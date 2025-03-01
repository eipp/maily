import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/router';
import { NextPage } from 'next';
import { toast } from 'react-hot-toast';
import Head from 'next/head';
import { DashboardLayout } from '../../components/Layout/DashboardLayout';
import { TemplateEditor } from '../../components/Templates/TemplateEditor';
import { withAuth } from '../../utils/withAuth';

const TemplatePage: NextPage = () => {
  const { t } = useTranslation();
  const router = useRouter();
  const { id, mode } = router.query;

  const [isNew, setIsNew] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    if (router.isReady) {
      if (id === 'new' || mode === 'new') {
        setIsNew(true);
        setIsLoading(false);
      } else if (id) {
        // Check if template exists
        const checkTemplate = async () => {
          try {
            const response = await fetch(`/api/templates/${id}`);
            if (!response.ok) {
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
    }
  }, [id, mode, router.isReady, router, t]);

  const handleBack = () => {
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
          {isNew
            ? t('templates.createNew')
            : t('templates.editTemplate')} | Maily
        </title>
      </Head>

      <div className="container mx-auto px-4 py-6">
        <TemplateEditor
          templateId={isNew ? undefined : Number(id)}
          isNew={isNew}
          onBack={handleBack}
        />
      </div>
    </DashboardLayout>
  );
};

export default withAuth(TemplatePage);
