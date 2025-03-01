'use client';

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
  Divider,
  Alert,
  AlertTitle
} from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import dynamic from 'next/dynamic';

// Dynamically import components to reduce initial load time
const EngagementPredictor = dynamic(
  () => import('../../components/ai/EngagementPredictor'),
  { ssr: false }
);

const SubjectLineOptimizer = dynamic(
  () => import('../../components/ai/SubjectLineOptimizer'),
  { ssr: false }
);

// Create a client
const queryClient = new QueryClient();

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ai-tabpanel-${index}`}
      aria-labelledby={`ai-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `ai-tab-${index}`,
    'aria-controls': `ai-tabpanel-${index}`,
  };
}

export default function AIFeaturesPage() {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            AI-Powered Email Marketing
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Leverage machine learning to optimize your email campaigns and increase engagement.
          </Typography>
        </Box>

        <Alert severity="info" sx={{ mb: 4 }}>
          <AlertTitle>Demo Mode</AlertTitle>
          These features are running in demonstration mode with simulated data. In production, they would use your actual campaign data and trained models.
        </Alert>

        <Paper sx={{ mb: 4 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              aria-label="AI features tabs"
              variant="fullWidth"
            >
              <Tab label="Engagement Prediction" {...a11yProps(0)} />
              <Tab label="Subject Line Optimization" {...a11yProps(1)} />
              <Tab label="About ML Pipeline" {...a11yProps(2)} />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <EngagementPredictor
              emailIds={['email_sample_1', 'email_sample_2', 'email_sample_3']}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <SubjectLineOptimizer
              initialSubjects={[
                'Special offer just for you!',
                'Your exclusive May discount inside',
                'Don\'t miss out on these deals',
                'Last chance: 24-hour flash sale'
              ]}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Box sx={{ maxWidth: 800, mx: 'auto' }}>
              <Typography variant="h5" gutterBottom>
                About Our ML Pipeline
              </Typography>

              <Typography variant="body1" paragraph>
                Maily uses a sophisticated machine learning pipeline to power its AI features. The pipeline consists of several key components:
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Feature Store
                </Typography>
                <Typography variant="body2" paragraph>
                  Our feature store manages all the data needed for training and inference. It handles feature computation, versioning, and serving, ensuring that models always have access to the most relevant and up-to-date data.
                </Typography>
              </Box>

              <Divider sx={{ my: 3 }} />

              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Model Registry
                </Typography>
                <Typography variant="body2" paragraph>
                  The model registry manages model versioning, deployment, and monitoring. It ensures that only the best-performing models are active and provides automatic rollback capabilities if a model's performance degrades.
                </Typography>
              </Box>

              <Divider sx={{ my: 3 }} />

              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  A/B Testing Framework
                </Typography>
                <Typography variant="body2" paragraph>
                  Our A/B testing framework allows for rigorous evaluation of models and features. It handles test setup, variant assignment, results analysis, and statistical significance testing to ensure that changes truly improve performance.
                </Typography>
              </Box>

              <Divider sx={{ my: 3 }} />

              <Box>
                <Typography variant="h6" gutterBottom>
                  Supported Model Types
                </Typography>
                <ul>
                  <li>
                    <Typography variant="body2">
                      <strong>Engagement Prediction:</strong> Predicts how likely a recipient is to open or click on an email.
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2">
                      <strong>Subject Line Optimization:</strong> Evaluates and ranks subject lines based on predicted open rates.
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2">
                      <strong>Send Time Optimization:</strong> Determines the optimal time to send emails to maximize engagement.
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2">
                      <strong>Audience Segmentation:</strong> Automatically groups recipients based on behavior and preferences.
                    </Typography>
                  </li>
                </ul>
              </Box>
            </Box>
          </TabPanel>
        </Paper>
      </Container>
    </QueryClientProvider>
  );
}
