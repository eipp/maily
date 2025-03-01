import React from 'react';
import { NextPage } from 'next';
import { useTranslation } from 'react-i18next';
import Head from 'next/head';
import Link from 'next/link';
import { FiPlusCircle } from 'react-icons/fi';
import { DashboardLayout } from '../../components/Layout/DashboardLayout';
import { TemplateList } from '../../components/Templates/TemplateList';
import { withAuth } from '../../utils/withAuth';

const TemplatesPage: NextPage = () => {
  const { t } = useTranslation();

  return (
    <DashboardLayout>
      <Head>
        <title>{t('templates.title')} | Maily</title>
      </Head>

      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {t('templates.title')}
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {t('templates.description')}
            </p>
          </div>

          <div className="mt-4 md:mt-0">
            <Link
              href="/templates/new"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <FiPlusCircle className="mr-2" />
              {t('templates.createNew')}
            </Link>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg overflow-hidden">
          <TemplateList />
        </div>
      </div>
    </DashboardLayout>
  );
};

export default withAuth(TemplatesPage);
