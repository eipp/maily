import React, { useState, useEffect } from 'react';
import { Card, Spinner, Button } from '../ui';

interface ContactLifecycleMetrics {
  last_activity_date: string;
  predicted_decay_date: string;
  current_health_score: number;
  predicted_health_trend: 'improving' | 'stable' | 'declining';
  self_healing_actions: SelfHealingAction[];
  decay_rate: number; // percentage per month
  recommended_actions: RecommendedAction[];
}

interface SelfHealingAction {
  id: string;
  type: 'verification' | 'enrichment' | 'cleansing' | 'recovery';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  timestamp: string;
  description: string;
  result?: string;
}

interface RecommendedAction {
  id: string;
  type: 'verification' | 'enrichment' | 'cleansing' | 'recovery';
  priority: 'high' | 'medium' | 'low';
  description: string;
  estimated_impact: number; // 0-100 percentage
}

interface ContactLifecycleManagerProps {
  contactId: string;
  contactEmail: string;
  onMetricsUpdated?: (metrics: ContactLifecycleMetrics) => void;
}

export const ContactLifecycleManager: React.FC<ContactLifecycleManagerProps> = ({
  contactId,
  contactEmail,
  onMetricsUpdated
}) => {
  const [lifecycleMetrics, setLifecycleMetrics] = useState<ContactLifecycleMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAction, setSelectedAction] = useState<RecommendedAction | null>(null);
  const [isExecutingAction, setIsExecutingAction] = useState<boolean>(false);

  useEffect(() => {
    fetchLifecycleMetrics();
  }, [contactId]);

  const fetchLifecycleMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      // This would be a real API call in production
      const response = await fetch(`/api/contacts/${contactId}/lifecycle`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch contact lifecycle metrics');
      }

      const data = await response.json();
      setLifecycleMetrics(data.lifecycle_metrics);

      if (onMetricsUpdated) {
        onMetricsUpdated(data.lifecycle_metrics);
      }
    } catch (err) {
      setError('Error fetching lifecycle metrics: ' + (err as Error).message);
      console.error('Error fetching lifecycle metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  const executeRecommendedAction = async (actionId: string) => {
    setIsExecutingAction(true);

    try {
      // This would be a real API call in production
      const response = await fetch(`/api/contacts/${contactId}/execute-action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action_id: actionId }),
      });

      if (!response.ok) {
        throw new Error('Failed to execute action');
      }

      // Refetch lifecycle metrics after action execution
      await fetchLifecycleMetrics();
      setSelectedAction(null);
    } catch (err) {
      setError('Error executing action: ' + (err as Error).message);
    } finally {
      setIsExecutingAction(false);
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-600';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const renderTrendIndicator = (trend: 'improving' | 'stable' | 'declining') => {
    switch (trend) {
      case 'improving':
        return (
          <div className="flex items-center text-green-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
            </svg>
            Improving
          </div>
        );
      case 'stable':
        return (
          <div className="flex items-center text-blue-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a1 1 0 01-1 1H3a1 1 0 110-2h14a1 1 0 011 1z" clipRule="evenodd" />
            </svg>
            Stable
          </div>
        );
      case 'declining':
        return (
          <div className="flex items-center text-red-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12 13a1 1 0 100 2h5a1 1 0 001-1v-5a1 1 0 10-2 0v2.586l-4.293-4.293a1 1 0 00-1.414 0L8 9.586l-4.293-4.293a1 1 0 00-1.414 1.414l5 5a1 1 0 001.414 0L11 9.414 14.586 13H12z" clipRule="evenodd" />
            </svg>
            Declining
          </div>
        );
    }
  };

  const getPriorityBadgeClass = (priority: 'high' | 'medium' | 'low') => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
    }
  };

  const getActionTypeIcon = (type: 'verification' | 'enrichment' | 'cleansing' | 'recovery') => {
    switch (type) {
      case 'verification':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'enrichment':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor">
            <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM14 11a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-1a1 1 0 011-1z" />
          </svg>
        );
      case 'cleansing':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-indigo-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'recovery':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-purple-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  return (
    <Card className="overflow-hidden">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Contact Lifecycle Management</h3>
            <p className="text-sm text-gray-500">{contactEmail}</p>
          </div>
          <Button
            onClick={fetchLifecycleMetrics}
            disabled={loading}
            size="sm"
          >
            {loading ? <Spinner size="sm" className="mr-2" /> : null}
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 text-sm">
          {error}
        </div>
      )}

      {loading && !lifecycleMetrics && (
        <div className="p-6 flex justify-center">
          <div className="text-center">
            <Spinner size="lg" className="mb-4" />
            <p className="text-gray-500">Loading lifecycle data...</p>
          </div>
        </div>
      )}

      {lifecycleMetrics && (
        <div>
          {/* Health and Prediction Summary */}
          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 bg-gray-50 border-b border-gray-200">
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">Current Health Score</p>
              <h3 className={`text-3xl font-bold ${getHealthScoreColor(lifecycleMetrics.current_health_score)}`}>
                {lifecycleMetrics.current_health_score}%
              </h3>
              <div className="mt-2">
                {renderTrendIndicator(lifecycleMetrics.predicted_health_trend)}
              </div>
            </div>

            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">Last Activity</p>
              <h3 className="text-xl font-semibold text-gray-800">
                {formatDate(lifecycleMetrics.last_activity_date)}
              </h3>
              <p className="text-sm text-gray-500 mt-2">
                {new Date(lifecycleMetrics.last_activity_date).toLocaleDateString() === new Date().toLocaleDateString()
                  ? 'Today'
                  : `${Math.ceil((new Date().getTime() - new Date(lifecycleMetrics.last_activity_date).getTime()) / (1000 * 60 * 60 * 24))} days ago`}
              </p>
            </div>

            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">Predicted Decay</p>
              <h3 className="text-xl font-semibold text-gray-800">
                {formatDate(lifecycleMetrics.predicted_decay_date)}
              </h3>
              <p className="text-sm text-gray-500 mt-2">
                {`${lifecycleMetrics.decay_rate.toFixed(1)}% per month`}
              </p>
            </div>
          </div>

          {/* Self-Healing Actions */}
          <div className="p-6 border-b border-gray-200">
            <h4 className="font-medium text-gray-900 mb-4">Automated Self-Healing Actions</h4>

            {lifecycleMetrics.self_healing_actions.length === 0 ? (
              <p className="text-sm text-gray-500">No self-healing actions have been performed yet.</p>
            ) : (
              <div className="bg-white overflow-hidden shadow-sm rounded-lg divide-y divide-gray-200">
                {lifecycleMetrics.self_healing_actions.map((action) => (
                  <div key={action.id} className="p-4">
                    <div className="flex justify-between">
                      <div className="flex items-center">
                        {getActionTypeIcon(action.type)}
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{action.description}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(action.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          action.status === 'completed' ? 'bg-green-100 text-green-800' :
                          action.status === 'failed' ? 'bg-red-100 text-red-800' :
                          action.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {action.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    {action.result && (
                      <p className="text-sm text-gray-600 mt-2 ml-8">
                        Result: {action.result}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recommended Actions */}
          <div className="p-6">
            <h4 className="font-medium text-gray-900 mb-4">Recommended Actions</h4>

            {lifecycleMetrics.recommended_actions.length === 0 ? (
              <p className="text-sm text-gray-500">No recommended actions at this time.</p>
            ) : (
              <div className="space-y-4">
                {lifecycleMetrics.recommended_actions.map((action) => (
                  <div
                    key={action.id}
                    className={`bg-white overflow-hidden shadow-sm rounded-lg border ${
                      selectedAction?.id === action.id ? 'border-blue-500' : 'border-gray-200'
                    }`}
                  >
                    <div className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex items-center">
                          {getActionTypeIcon(action.type)}
                          <div className="ml-3">
                            <div className="flex items-center">
                              <p className="text-sm font-medium text-gray-900">{action.description}</p>
                              <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityBadgeClass(action.priority)}`}>
                                {action.priority}
                              </span>
                            </div>
                            <p className="text-xs text-gray-500">
                              Estimated impact: +{action.estimated_impact}% to health score
                            </p>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => setSelectedAction(action)}
                          variant="outline"
                        >
                          Details
                        </Button>
                      </div>

                      {selectedAction?.id === action.id && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <p className="text-sm text-gray-600 mb-4">
                            Executing this action will improve the contact's health score by approximately {action.estimated_impact}%.
                            This type of {action.type} action is recommended for contacts with {action.priority} priority attention needs.
                          </p>
                          <div className="flex justify-end space-x-3">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedAction(null)}
                            >
                              Cancel
                            </Button>
                            <Button
                              size="sm"
                              onClick={() => executeRecommendedAction(action.id)}
                              disabled={isExecutingAction}
                            >
                              {isExecutingAction ? <Spinner size="sm" className="mr-2" /> : null}
                              {isExecutingAction ? 'Executing...' : 'Execute Action'}
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {!lifecycleMetrics && !loading && (
        <div className="p-6 text-center">
          <p className="text-gray-500 mb-4">No lifecycle data available. Click refresh to load the latest data.</p>
          <Button onClick={fetchLifecycleMetrics}>Load Lifecycle Data</Button>
        </div>
      )}
    </Card>
  );
};

export default ContactLifecycleManager;
