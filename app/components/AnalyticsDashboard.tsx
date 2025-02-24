import React, { useCallback, useState, useEffect } from 'react';
import { useDataProcessor } from '../hooks/useDataProcessor';

interface AnalyticsData {
  openRate: number;
  clickRate: number;
  conversionRate: number;
  engagement: number;
}

interface AnalyticsDashboardProps {
  campaignId: string;
  onRefresh?: () => void;
}

const MetricCard = React.memo(({ label, value }: { label: string; value: number }) => (
  <div className="bg-white p-6 rounded-lg shadow-sm">
    <h3 className="text-sm font-medium text-gray-500">{label}</h3>
    <p className="mt-2 text-3xl font-semibold text-gray-900">{value.toFixed(2)}%</p>
  </div>
));

const AnalyticsDashboard = React.memo(({ campaignId, onRefresh }: AnalyticsDashboardProps) => {
  const [metrics, setMetrics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const { processAnalytics, isProcessing, error } = useDataProcessor();

  const fetchAndProcessData = useCallback(async () => {
    try {
      setLoading(true);
      // Fetch raw data
      const response = await fetch(`/api/campaigns/${campaignId}/analytics`);
      const rawData = await response.json();

      // Process data in web worker
      const processedData = await processAnalytics([rawData]);
      setMetrics(processedData[0]);
    } catch (err) {
      console.error('Error processing analytics:', err);
    } finally {
      setLoading(false);
    }
  }, [campaignId, processAnalytics]);

  const handleRefresh = useCallback(() => {
    fetchAndProcessData();
    onRefresh?.();
  }, [fetchAndProcessData, onRefresh]);

  useEffect(() => {
    fetchAndProcessData();
  }, [fetchAndProcessData]);

  if (loading || isProcessing) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading analytics: {error.message}</p>
        <button
          onClick={handleRefresh}
          className="mt-2 text-red-600 hover:text-red-800 font-medium"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Campaign Analytics</h2>
        <button
          onClick={handleRefresh}
          className="text-indigo-600 hover:text-indigo-800 font-medium"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Open Rate" value={metrics.openRate} />
        <MetricCard label="Click Rate" value={metrics.clickRate} />
        <MetricCard label="Conversion Rate" value={metrics.conversionRate} />
        <MetricCard label="Engagement Score" value={metrics.engagement} />
      </div>
    </div>
  );
});

AnalyticsDashboard.displayName = 'AnalyticsDashboard';

export default AnalyticsDashboard; 