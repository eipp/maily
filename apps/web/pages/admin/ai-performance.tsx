import { GetServerSideProps } from 'next';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/pages/api/auth/[...nextauth]';
import AdminLayout from '@/components/layouts/AdminLayout';
import AIPerformanceDashboard from '@/components/admin/AIPerformanceDashboard';
import { NextSeo } from 'next-seo';

export default function AIPerformancePage() {
  return (
    <>
      <NextSeo
        title="AI Performance Monitoring | Maily Admin"
        description="Monitor AI performance metrics and usage patterns"
        noindex={true}
      />
      <AdminLayout>
        <AIPerformanceDashboard />
      </AdminLayout>
    </>
  );
}

export const getServerSideProps: GetServerSideProps = async (context) => {
  const session = await getServerSession(context.req, context.res, authOptions);

  // Check if user is authenticated
  if (!session) {
    return {
      redirect: {
        destination: '/auth/signin?callbackUrl=/admin/ai-performance',
        permanent: false,
      },
    };
  }

  // Check if user is an admin
  if (!session.user?.isAdmin) {
    return {
      redirect: {
        destination: '/dashboard',
        permanent: false,
      },
    };
  }

  return {
    props: {},
  };
}
