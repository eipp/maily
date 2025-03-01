'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import type { FC } from 'react';
import { useSession } from 'next-auth/react';
import { motion, AnimatePresence } from 'framer-motion';
import { analyticsService, type CampaignAnalytics } from '@/services/analytics';
import { useToast } from '@/hooks/useToast';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { cn } from '@/lib/utils';

interface AnalyticsDashboardProps {
  campaignId: string;
  className?: string;
  refreshInterval?: number; // in milliseconds
}

const METRIC_ICONS = {
  'Open Rate': (
    <svg className="size-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ),
  'Click Rate': (
    <svg className="size-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
    </svg>
  ),
  'Conversion Rate': (
    <svg className="size-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  'Engagement': (
    <svg className="size-6 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
    </svg>
  ),
};

const AnalyticsDashboard: FC<AnalyticsDashboardProps> = ({
  campaignId,
  className = '',
  refreshInterval = 300000, // 5 minutes default
}) => {
  const { data: session } = useSession();
  const { showToast } = useToast();
  const [metrics, setMetrics] = useState<CampaignAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const loadAnalytics = useCallback(async (silent = false) => {
    if (!session?.user) return;

    try {
      if (!silent) setLoading(true);
      setError(null);
      const data = await analyticsService.getCampaignAnalytics(campaignId);
      setMetrics(data);
      setRetryCount(0);
    } catch (err) {
      setError('Failed to load analytics data');
      console.error('Analytics error:', err);

      // Implement exponential backoff for retries
      if (retryCount < 3) {
        const timeout = Math.pow(2, retryCount) * 1000;
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          void loadAnalytics(true);
        }, timeout);
      } else {
        showToast({
          type: 'error',
          message: 'Failed to load analytics after multiple attempts',
        });
      }
    } finally {
      setLoading(false);
    }
  }, [campaignId, session?.user, retryCount, showToast]);

  // Initial load and refresh interval
  useEffect(() => {
    void loadAnalytics();

    const intervalId = setInterval(() => {
      void loadAnalytics(true);
    }, refreshInterval);

    return () => clearInterval(intervalId);
  }, [loadAnalytics, refreshInterval]);

  // Memoize metric cards data
  const metricCards = useMemo(() => {
    if (!metrics) return [];

    return [
      { label: 'Open Rate', value: metrics.openRate },
      { label: 'Click Rate', value: metrics.clickRate },
      { label: 'Conversion Rate', value: metrics.conversionRate },
      { label: 'Engagement', value: metrics.engagement },
    ];
  }, [metrics]);

  if (loading && !metrics) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 rounded w-1/4 bg-gray-200"></div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array(4).fill(0).map((_, i) => (
            <div key={i} className="h-32 rounded-lg bg-gray-200"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <div className="shrink-0">
            <svg className="size-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-red-800">{error}</p>
            <button
              onClick={() => void loadAnalytics()}
              className="mt-2 text-sm font-medium text-red-600 hover:text-red-500"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  return (
    <ErrorBoundary fallback={<div>Something went wrong with the analytics display.</div>}>
      <div className={cn(
        'flex flex-col items-center justify-center',
        'rounded-lg bg-white p-6 shadow-lg',
        'dark:bg-gray-800'
      )}>
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Campaign Analytics</h2>
          <button
            onClick={() => void loadAnalytics()}
            className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
          >
            Refresh
          </button>
        </div>

        <AnimatePresence>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {metricCards.map((metric, index) => (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className={cn(
                  'rounded-lg bg-white p-6 shadow transition duration-200 hover:scale-105',
                  'dark:bg-gray-700'
                )}
              >
                <div className="flex items-center space-x-3">
                  {METRIC_ICONS[metric.label as keyof typeof METRIC_ICONS]}
                  <h3 className="text-sm font-medium text-gray-500">{metric.label}</h3>
                </div>
                <p className="mt-2 text-3xl font-semibold text-gray-900">
                  {metric.value.toFixed(1)}%
                </p>
                {loading && (
                  <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-white/50">
                    <div className="size-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"></div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      </div>
    </ErrorBoundary>
  );
};

AnalyticsDashboard.displayName = 'AnalyticsDashboard';

export default AnalyticsDashboard;
