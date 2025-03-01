import React, { useState, useEffect } from 'react';
import { Card, Spinner, Button } from '../ui';

interface ComplianceCheck {
  id: string;
  regulation: string;
  status: 'compliant' | 'non_compliant' | 'unknown' | 'pending';
  last_checked: string;
  issue_description?: string;
  recommended_action?: string;
  risk_level?: 'high' | 'medium' | 'low';
  category: 'consent' | 'data_retention' | 'opt_out' | 'data_processing' | 'marketing_permission';
  details: Record<string, any>;
}

interface ComplianceAutomationProps {
  contactId: string;
  contactEmail: string;
  onComplianceUpdate?: (checks: ComplianceCheck[]) => void;
}

export const ComplianceAutomation: React.FC<ComplianceAutomationProps> = ({
  contactId,
  contactEmail,
  onComplianceUpdate
}) => {
  const [complianceChecks, setComplianceChecks] = useState<ComplianceCheck[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isRunningChecks, setIsRunningChecks] = useState<boolean>(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    fetchComplianceData();
  }, [contactId]);

  const fetchComplianceData = async () => {
    setLoading(true);
    setError(null);

    try {
      // This would be a real API call in production
      const response = await fetch(`/api/contacts/${contactId}/compliance`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch compliance data');
      }

      const data = await response.json();
      setComplianceChecks(data.compliance_checks);

      if (onComplianceUpdate) {
        onComplianceUpdate(data.compliance_checks);
      }
    } catch (err) {
      setError('Error fetching compliance data: ' + (err as Error).message);
      console.error('Error fetching compliance data:', err);
    } finally {
      setLoading(false);
    }
  };

  const runComplianceChecks = async () => {
    setIsRunningChecks(true);
    setError(null);

    try {
      // This would be a real API call in production
      const response = await fetch(`/api/contacts/${contactId}/run-compliance-checks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to run compliance checks');
      }

      const data = await response.json();
      setComplianceChecks(data.compliance_checks);

      if (onComplianceUpdate) {
        onComplianceUpdate(data.compliance_checks);
      }
    } catch (err) {
      setError('Error running compliance checks: ' + (err as Error).message);
      console.error('Error running compliance checks:', err);
    } finally {
      setIsRunningChecks(false);
    }
  };

  const resolveComplianceIssue = async (checkId: string) => {
    try {
      // This would be a real API call in production
      const response = await fetch(`/api/contacts/${contactId}/resolve-compliance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ check_id: checkId }),
      });

      if (!response.ok) {
        throw new Error('Failed to resolve compliance issue');
      }

      // Update the local state with the resolved check
      const data = await response.json();
      setComplianceChecks(prevChecks =>
        prevChecks.map(check =>
          check.id === checkId ? data.updated_check : check
        )
      );
    } catch (err) {
      setError('Error resolving compliance issue: ' + (err as Error).message);
      console.error('Error resolving compliance issue:', err);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-100 text-green-800';
      case 'non_compliant':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskBadgeClass = (risk?: string) => {
    switch (risk) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'consent':
        return 'Consent & Permissions';
      case 'data_retention':
        return 'Data Retention';
      case 'opt_out':
        return 'Opt-Out Handling';
      case 'data_processing':
        return 'Data Processing';
      case 'marketing_permission':
        return 'Marketing Permissions';
      default:
        return category.replace('_', ' ');
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'consent':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'data_retention':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
            <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
            <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
          </svg>
        );
      case 'opt_out':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        );
      case 'data_processing':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-purple-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
          </svg>
        );
      case 'marketing_permission':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
            <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
            <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
          </svg>
        );
      default:
        return (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  // Calculate compliance summary stats
  const complianceStats = {
    total: complianceChecks.length,
    compliant: complianceChecks.filter(check => check.status === 'compliant').length,
    nonCompliant: complianceChecks.filter(check => check.status === 'non_compliant').length,
    pending: complianceChecks.filter(check => check.status === 'pending').length,
    unknown: complianceChecks.filter(check => check.status === 'unknown').length,
  };

  // Filter checks by selected category
  const filteredChecks = selectedCategory === 'all'
    ? complianceChecks
    : complianceChecks.filter(check => check.category === selectedCategory);

  // Get unique categories for filter options
  const categories = ['all', ...new Set(complianceChecks.map(check => check.category))];

  return (
    <Card className="overflow-hidden">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Compliance Automation</h3>
            <p className="text-sm text-gray-500">{contactEmail}</p>
          </div>
          <Button
            onClick={runComplianceChecks}
            disabled={isRunningChecks}
            size="sm"
          >
            {isRunningChecks ? <Spinner size="sm" className="mr-2" /> : null}
            {isRunningChecks ? 'Running Checks...' : 'Run Compliance Checks'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 text-sm">
          {error}
        </div>
      )}

      {loading && complianceChecks.length === 0 ? (
        <div className="p-6 flex justify-center">
          <Spinner size="lg" />
        </div>
      ) : (
        <>
          {/* Compliance Stats */}
          <div className="grid grid-cols-4 gap-4 p-6 bg-gray-50 border-b border-gray-200">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-800">{complianceStats.total}</div>
              <div className="text-sm text-gray-500">Total Checks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{complianceStats.compliant}</div>
              <div className="text-sm text-gray-500">Compliant</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{complianceStats.nonCompliant}</div>
              <div className="text-sm text-gray-500">Non-Compliant</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-500">{complianceStats.pending + complianceStats.unknown}</div>
              <div className="text-sm text-gray-500">Pending/Unknown</div>
            </div>
          </div>

          {/* Category Filters */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex space-x-2 overflow-x-auto pb-2">
              {categories.map(category => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-3 py-1 rounded-full text-sm whitespace-nowrap ${
                    selectedCategory === category
                      ? 'bg-blue-100 text-blue-800 font-medium'
                      : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                  }`}
                >
                  {category === 'all' ? 'All Categories' : getCategoryLabel(category)}
                </button>
              ))}
            </div>
          </div>

          {/* Compliance Checks List */}
          <div className="p-6">
            {filteredChecks.length === 0 ? (
              <div className="text-center py-6 bg-gray-50 rounded-lg">
                <p className="text-gray-500">No compliance checks available in this category.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredChecks.map((check) => (
                  <div key={check.id} className="bg-white shadow overflow-hidden rounded-lg border border-gray-200">
                    <div className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex items-center">
                          {getCategoryIcon(check.category)}
                          <div className="ml-3">
                            <h4 className="text-sm font-medium text-gray-900">{check.regulation}</h4>
                            <div className="flex flex-wrap gap-2 mt-1">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(check.status)}`}>
                                {check.status.replace('_', ' ')}
                              </span>
                              {check.risk_level && (
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskBadgeClass(check.risk_level)}`}>
                                  {check.risk_level} risk
                                </span>
                              )}
                              <span className="text-xs text-gray-500">
                                Last checked: {formatDate(check.last_checked)}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {check.issue_description && (
                        <div className="mt-3 text-sm text-gray-600">
                          <p className="font-medium">Issue:</p>
                          <p>{check.issue_description}</p>
                        </div>
                      )}

                      {check.status === 'non_compliant' && check.recommended_action && (
                        <div className="mt-3">
                          <p className="text-sm font-medium text-gray-900">Recommended Action:</p>
                          <p className="text-sm text-gray-600">{check.recommended_action}</p>
                          <div className="mt-3">
                            <Button
                              size="sm"
                              onClick={() => resolveComplianceIssue(check.id)}
                            >
                              Resolve Issue
                            </Button>
                          </div>
                        </div>
                      )}

                      {/* Specific compliance details based on category */}
                      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-gray-500">
                        {check.category === 'consent' && check.details && (
                          <>
                            <div>Consent Date:</div>
                            <div className="font-medium">{check.details.consent_date ? formatDate(check.details.consent_date) : 'Unknown'}</div>
                            <div>Consent Source:</div>
                            <div className="font-medium">{check.details.consent_source || 'Unknown'}</div>
                            <div>Explicit Consent:</div>
                            <div className="font-medium">{check.details.explicit_consent ? 'Yes' : 'No'}</div>
                          </>
                        )}

                        {check.category === 'data_retention' && check.details && (
                          <>
                            <div>Data Age:</div>
                            <div className="font-medium">{check.details.data_age} days</div>
                            <div>Retention Limit:</div>
                            <div className="font-medium">{check.details.retention_limit} days</div>
                            <div>Data Purge Date:</div>
                            <div className="font-medium">{check.details.purge_date ? formatDate(check.details.purge_date) : 'N/A'}</div>
                          </>
                        )}

                        {check.category === 'opt_out' && check.details && (
                          <>
                            <div>Opt-Out Requested:</div>
                            <div className="font-medium">{check.details.opt_out_requested ? 'Yes' : 'No'}</div>
                            {check.details.opt_out_date && (
                              <>
                                <div>Opt-Out Date:</div>
                                <div className="font-medium">{formatDate(check.details.opt_out_date)}</div>
                              </>
                            )}
                            <div>Properly Processed:</div>
                            <div className="font-medium">{check.details.properly_processed ? 'Yes' : 'No'}</div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {!loading && complianceChecks.length === 0 && (
        <div className="p-6 text-center">
          <p className="text-gray-500 mb-4">No compliance data available. Run compliance checks to evaluate this contact.</p>
          <Button onClick={runComplianceChecks}>Run Compliance Checks</Button>
        </div>
      )}
    </Card>
  );
};

export default ComplianceAutomation;
