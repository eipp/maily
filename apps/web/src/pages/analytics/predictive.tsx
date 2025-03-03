import React from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import { Box, Container, Typography, Breadcrumbs, Link } from '@mui/material';
import { Home, Analytics } from '@mui/icons-material';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import PredictiveAnalyticsDashboard from '@/components/predictive/PredictiveAnalyticsDashboard';

const PredictiveAnalyticsPage: NextPage = () => {
  return (
    <>
      <Head>
        <title>Predictive Analytics | Maily</title>
        <meta name="description" content="AI-powered predictive analytics for email marketing" />
      </Head>

      <DashboardLayout>
        <Container maxWidth="xl">
          <Box sx={{ py: 3 }}>
            <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
              <Link
                underline="hover"
                color="inherit"
                href="/"
                sx={{ display: 'flex', alignItems: 'center' }}
              >
                <Home sx={{ mr: 0.5 }} fontSize="inherit" />
                Home
              </Link>
              <Link
                underline="hover"
                color="inherit"
                href="/analytics"
                sx={{ display: 'flex', alignItems: 'center' }}
              >
                <Analytics sx={{ mr: 0.5 }} fontSize="inherit" />
                Analytics
              </Link>
              <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
                Predictive Analytics
              </Typography>
            </Breadcrumbs>

            <PredictiveAnalyticsDashboard />
          </Box>
        </Container>
      </DashboardLayout>
    </>
  );
};

export default PredictiveAnalyticsPage;
