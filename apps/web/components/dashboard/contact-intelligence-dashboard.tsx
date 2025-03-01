import React, { useState, useEffect } from 'react';
import { Card, Spinner, Button, Table } from '../ui';
import ContactHealthVisualization from './contact-health-visualization';
import MultiSignalValidation from './multi-signal-validation';
import ContactLifecycleManager from './contact-lifecycle-manager';
import BlockchainVerification from './blockchain-verification';
import ComplianceAutomation from './compliance-automation';

interface Contact {
  id: string;
  email: string;
  name: string;
  health_score: number;
  last_activity: string;
  last_validated: string;
  compliance_status: 'compliant' | 'non_compliant' | 'unknown';
  bounce_rate: number;
  engagement_score: number;
  is_verified: boolean;
  blockchain_verified: boolean;
}

interface ContactIntelligenceDashboardProps {
  userId: string;
  listId?: string;
}

export const ContactIntelligenceDashboard: React.FC<ContactIntelligenceDashboardProps> = ({
  userId,
  listId
}) => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filterOptions, setFilterOptions] = useState({
    healthScore: 'all',
    complianceStatus: 'all',
    isVerified: 'all',
  });
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [isCleaningList, setIsCleaningList] = useState<boolean>(false);
  const [healthScores, setHealthScores] = useState<{
    overall: number;
    email_validity: number;
    engagement: number;
    deliverability: number;
    consent_level: 'explicit' | 'implied' | 'unknown';
    domain_reputation: number;
    last_evaluated: string;
  } | null>(null);

  useEffect(() => {
    fetchContacts();
  }, [userId, listId, filterOptions]);

  const fetchContacts = async () => {
    setLoading(true);
    setError(null);

    try {
      // Build query params
      const params = new URLSearchParams();
      if (listId) params.append('list_id', listId);
      if (filterOptions.healthScore !== 'all') params.append('health_score', filterOptions.healthScore);
      if (filterOptions.complianceStatus !== 'all') params.append('compliance_status', filterOptions.complianceStatus);
      if (filterOptions.isVerified !== 'all') params.append('is_verified', filterOptions.isVerified);

      // This would be a real API call in production
      const response = await fetch(`/api/contacts?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch contacts');
      }

      const data = await response.json();
      setContacts(data.contacts);
    } catch (err) {
      setError('Error fetching contacts: ' + (err as Error).message);
      console.error('Error fetching contacts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filterName: string, value: string) => {
    setFilterOptions(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  const handleCleanList = async () => {
    setIsCleaningList(true);

    try {
      // This would be a real API call in production
      const response = await fetch('/api/contacts/clean-list', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          list_id: listId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to clean contact list');
      }

      // Refetch contacts after cleaning
      await fetchContacts();
    } catch (err) {
      setError('Error cleaning list: ' + (err as Error).message);
      console.error('Error cleaning list:', err);
    } finally {
      setIsCleaningList(false);
    }
  };

  const handleContactSelect = (contact: Contact) => {
    setSelectedContact(contact);

    // Fetch health scores for the selected contact
    fetch(`/api/contacts/${contact.id}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch health scores');
        return response.json();
      })
      .then(data => {
        setHealthScores(data.health_scores);
      })
      .catch(err => {
        console.error('Error fetching health scores:', err);
      });
  };

  const renderHealthStatusIndicator = (score: number) => {
    let color = 'bg-red-500';
    if (score >= 80) color = 'bg-green-500';
    else if (score >= 60) color = 'bg-yellow-500';

    return (
      <div className="flex items-center">
        <div className={`w-3 h-3 rounded-full ${color} mr-2`}></div>
        <span>{score}%</span>
      </div>
    );
  };

  const renderDetailView = () => {
    if (!selectedContact) {
      return (
        <div className="text-center py-20 bg-gray-50 rounded-lg">
          <p className="text-gray-500">Select a contact to view detailed intelligence</p>
        </div>
      );
    }

    if (activeTab === 'health' && healthScores) {
      return <ContactHealthVisualization healthScore={healthScores} />;
    }

    if (activeTab === 'validation') {
      return <MultiSignalValidation contactId={selectedContact.id} contactEmail={selectedContact.email} />;
    }

    if (activeTab === 'lifecycle') {
      return <ContactLifecycleManager contactId={selectedContact.id} contactEmail={selectedContact.email} />;
    }

    if (activeTab === 'blockchain') {
      return <BlockchainVerification contactId={selectedContact.id} contactEmail={selectedContact.email} />;
    }

    if (activeTab === 'compliance') {
      return <ComplianceAutomation contactId={selectedContact.id} contactEmail={selectedContact.email} />;
    }

    // Overview tab - show summary of all sections
    return (
      <div className="space-y-6">
        {healthScores && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ContactHealthVisualization healthScore={healthScores} />
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card>
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <Button
                  onClick={() => setActiveTab('validation')}
                  className="w-full justify-start"
                >
                  Run Multi-Signal Validation
                </Button>
                <Button
                  onClick={() => setActiveTab('lifecycle')}
                  className="w-full justify-start"
                  variant="outline"
                >
                  View Lifecycle Management
                </Button>
                <Button
                  onClick={() => setActiveTab('blockchain')}
                  className="w-full justify-start"
                  variant="outline"
                >
                  Verify on Blockchain
                </Button>
                <Button
                  onClick={() => setActiveTab('compliance')}
                  className="w-full justify-start"
                  variant="outline"
                >
                  Check Compliance Status
                </Button>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Contact Summary</h3>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-gray-500">Name:</div>
                  <div>{selectedContact.name}</div>

                  <div className="text-gray-500">Email:</div>
                  <div>{selectedContact.email}</div>

                  <div className="text-gray-500">Health Score:</div>
                  <div>{renderHealthStatusIndicator(selectedContact.health_score)}</div>

                  <div className="text-gray-500">Last Activity:</div>
                  <div>{new Date(selectedContact.last_activity).toLocaleDateString()}</div>

                  <div className="text-gray-500">Last Validated:</div>
                  <div>{new Date(selectedContact.last_validated).toLocaleDateString()}</div>

                  <div className="text-gray-500">Compliance:</div>
                  <div className="capitalize">{selectedContact.compliance_status.replace('_', ' ')}</div>

                  <div className="text-gray-500">Engagement:</div>
                  <div>{selectedContact.engagement_score}%</div>

                  <div className="text-gray-500">Blockchain Verified:</div>
                  <div>{selectedContact.blockchain_verified ? 'Yes' : 'No'}</div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Contact Intelligence Dashboard</h2>
          <p className="text-sm text-gray-500">
            Comprehensive intelligence and automated management for your contacts
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={handleCleanList}
            disabled={isCleaningList || loading}
          >
            {isCleaningList ? <Spinner size="sm" className="mr-2" /> : null}
            {isCleaningList ? 'Cleaning...' : 'Clean Contact List'}
          </Button>
          <Button
            onClick={fetchContacts}
            disabled={loading}
            variant="outline"
          >
            {loading ? <Spinner size="sm" className="mr-2" /> : null}
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 text-sm rounded-lg">
          {error}
        </div>
      )}

      <Card>
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center space-x-2">
              <label htmlFor="healthScore" className="text-sm font-medium text-gray-700">
                Health Score:
              </label>
              <select
                id="healthScore"
                className="rounded-md border-gray-300 shadow-sm text-sm focus:border-blue-500 focus:ring-blue-500"
                value={filterOptions.healthScore}
                onChange={(e) => handleFilterChange('healthScore', e.target.value)}
              >
                <option value="all">All</option>
                <option value="high">High (80%+)</option>
                <option value="medium">Medium (60-79%)</option>
                <option value="low">Low (&lt;60%)</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <label htmlFor="complianceStatus" className="text-sm font-medium text-gray-700">
                Compliance:
              </label>
              <select
                id="complianceStatus"
                className="rounded-md border-gray-300 shadow-sm text-sm focus:border-blue-500 focus:ring-blue-500"
                value={filterOptions.complianceStatus}
                onChange={(e) => handleFilterChange('complianceStatus', e.target.value)}
              >
                <option value="all">All</option>
                <option value="compliant">Compliant</option>
                <option value="non_compliant">Non-Compliant</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <label htmlFor="isVerified" className="text-sm font-medium text-gray-700">
                Verification:
              </label>
              <select
                id="isVerified"
                className="rounded-md border-gray-300 shadow-sm text-sm focus:border-blue-500 focus:ring-blue-500"
                value={filterOptions.isVerified}
                onChange={(e) => handleFilterChange('isVerified', e.target.value)}
              >
                <option value="all">All</option>
                <option value="true">Verified</option>
                <option value="false">Unverified</option>
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="p-6 flex justify-center">
            <Spinner size="lg" />
          </div>
        ) : contacts.length === 0 ? (
          <div className="p-6 text-center">
            <p className="text-gray-500">No contacts found matching the current filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <Table.Header>
                <Table.Row>
                  <Table.Head>Name</Table.Head>
                  <Table.Head>Email</Table.Head>
                  <Table.Head>Health Score</Table.Head>
                  <Table.Head>Last Activity</Table.Head>
                  <Table.Head>Compliance</Table.Head>
                  <Table.Head>Verified</Table.Head>
                  <Table.Head>Actions</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {contacts.map((contact) => (
                  <Table.Row
                    key={contact.id}
                    className={`cursor-pointer ${selectedContact?.id === contact.id ? 'bg-blue-50' : ''}`}
                    onClick={() => handleContactSelect(contact)}
                  >
                    <Table.Cell className="font-medium">{contact.name}</Table.Cell>
                    <Table.Cell>{contact.email}</Table.Cell>
                    <Table.Cell>{renderHealthStatusIndicator(contact.health_score)}</Table.Cell>
                    <Table.Cell>{new Date(contact.last_activity).toLocaleDateString()}</Table.Cell>
                    <Table.Cell className="capitalize">{contact.compliance_status.replace('_', ' ')}</Table.Cell>
                    <Table.Cell>{contact.is_verified ? 'Yes' : 'No'}</Table.Cell>
                    <Table.Cell>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleContactSelect(contact);
                          setActiveTab('validation');
                        }}
                      >
                        Validate
                      </Button>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </div>
        )}
      </Card>

      {selectedContact && (
        <div className="space-y-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('health')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'health'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Health Score
              </button>
              <button
                onClick={() => setActiveTab('validation')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'validation'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Multi-Signal Validation
              </button>
              <button
                onClick={() => setActiveTab('lifecycle')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'lifecycle'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Lifecycle Management
              </button>
              <button
                onClick={() => setActiveTab('blockchain')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'blockchain'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Blockchain Verification
              </button>
              <button
                onClick={() => setActiveTab('compliance')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'compliance'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Compliance
              </button>
            </nav>
          </div>

          {renderDetailView()}
        </div>
      )}
    </div>
  );
};

export default ContactIntelligenceDashboard;
