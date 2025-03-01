import React, { useState, useEffect } from 'react';
import { Button, Card, Icon, Spinner, Alert, Badge } from '../../ui';
import {
  getNangoAuthURL,
  getConnectedPlatforms,
  triggerNangoSync,
  disconnectPlatform
} from '../../services/api';

interface Platform {
  id: string;
  name: string;
  icon: string;
  description: string;
  capabilities: string[];
}

interface Connection {
  provider_config_key: string;
  connection_id: string;
  created_at: string;
  updated_at: string;
  sync_status: {
    [key: string]: {
      status: 'synced' | 'pending' | 'error';
      last_synced?: string;
      error?: string;
    };
  };
}

const PLATFORMS: Platform[] = [
  {
    id: 'linkedin',
    name: 'LinkedIn',
    icon: 'linkedin',
    description: 'Connect with your LinkedIn account to access your professional network',
    capabilities: ['Search for people', 'Send messages', 'Access your connections']
  },
  {
    id: 'twitter',
    name: 'Twitter',
    icon: 'twitter',
    description: 'Connect with your Twitter account to access your social network',
    capabilities: ['Post tweets', 'Search for tweets', 'Access your followers']
  },
  {
    id: 'gmail',
    name: 'Gmail',
    icon: 'gmail',
    description: 'Connect with your Gmail account to access your emails',
    capabilities: ['Send emails', 'Search for emails', 'Access your contacts']
  },
  {
    id: 'outlook',
    name: 'Outlook',
    icon: 'outlook',
    description: 'Connect with your Outlook account to access your emails',
    capabilities: ['Send emails', 'Search for emails', 'Access your contacts']
  }
];

export const PlatformIntegration: React.FC = () => {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [syncStatus, setSyncStatus] = useState<{[key: string]: 'syncing' | 'success' | 'error'}>({});

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getConnectedPlatforms();
      setConnections(response.connections);
    } catch (error) {
      console.error('Error fetching connections:', error);
      setError('Failed to load your connected platforms. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async (platformId: string) => {
    setIsLoading(true);
    try {
      const response = await getNangoAuthURL(platformId);
      window.location.href = response.auth_url;
    } catch (error) {
      console.error(`Error connecting to ${platformId}:`, error);
      setError(`Failed to connect to ${getPlatformName(platformId)}. Please try again later.`);
      setIsLoading(false);
    }
  };

  const handleSync = async (platformId: string, syncType: string) => {
    setSyncStatus(prev => ({ ...prev, [`${platformId}-${syncType}`]: 'syncing' }));
    try {
      await triggerNangoSync(platformId, syncType);
      setSyncStatus(prev => ({ ...prev, [`${platformId}-${syncType}`]: 'success' }));

      // Refresh connections after a short delay to show updated sync status
      setTimeout(() => {
        fetchConnections();
      }, 2000);
    } catch (error) {
      console.error(`Error syncing ${platformId}:`, error);
      setSyncStatus(prev => ({ ...prev, [`${platformId}-${syncType}`]: 'error' }));
    }
  };

  const handleDisconnect = async (platformId: string) => {
    if (!confirm(`Are you sure you want to disconnect ${getPlatformName(platformId)}?`)) {
      return;
    }

    setIsLoading(true);
    try {
      await disconnectPlatform(platformId);
      setConnections(prev => prev.filter(conn => conn.provider_config_key !== platformId));
    } catch (error) {
      console.error(`Error disconnecting ${platformId}:`, error);
      setError(`Failed to disconnect ${getPlatformName(platformId)}. Please try again later.`);
    } finally {
      setIsLoading(false);
    }
  };

  const getPlatformName = (platformId: string): string => {
    const platform = PLATFORMS.find(p => p.id === platformId);
    return platform ? platform.name : platformId;
  };

  const isConnected = (platformId: string): boolean => {
    return connections.some(conn => conn.provider_config_key === platformId);
  };

  const getConnection = (platformId: string): Connection | undefined => {
    return connections.find(conn => conn.provider_config_key === platformId);
  };

  const getSyncStatusForType = (platformId: string, syncType: string) => {
    const connection = getConnection(platformId);
    if (!connection) return null;

    return connection.sync_status?.[syncType] || null;
  };

  const renderSyncStatus = (platformId: string, syncType: string) => {
    const status = getSyncStatusForType(platformId, syncType);
    const currentSyncStatus = syncStatus[`${platformId}-${syncType}`];

    if (currentSyncStatus === 'syncing') {
      return <Spinner size="sm" />;
    }

    if (currentSyncStatus === 'error') {
      return <Badge color="red">Error</Badge>;
    }

    if (currentSyncStatus === 'success') {
      return <Badge color="green">Synced</Badge>;
    }

    if (!status) {
      return <Badge color="gray">Not synced</Badge>;
    }

    if (status.status === 'synced') {
      return (
        <Badge color="green">
          Synced {status.last_synced ? new Date(status.last_synced).toLocaleString() : ''}
        </Badge>
      );
    }

    if (status.status === 'pending') {
      return <Badge color="yellow">Pending</Badge>;
    }

    if (status.status === 'error') {
      return <Badge color="red" title={status.error}>Error</Badge>;
    }

    return null;
  };

  const renderPlatformCard = (platform: Platform) => {
    const connected = isConnected(platform.id);
    const connection = getConnection(platform.id);

    return (
      <Card key={platform.id} className="mb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center">
            <Icon name={platform.icon} size="lg" className="mr-3" />
            <div>
              <h3 className="text-lg font-semibold">{platform.name}</h3>
              <p className="text-sm text-gray-600">{platform.description}</p>
            </div>
          </div>

          {!connected ? (
            <Button
              onClick={() => handleConnect(platform.id)}
              disabled={isLoading}
            >
              Connect
            </Button>
          ) : (
            <Button
              variant="outline"
              color="danger"
              onClick={() => handleDisconnect(platform.id)}
              disabled={isLoading}
            >
              Disconnect
            </Button>
          )}
        </div>

        {connected && (
          <div className="mt-4">
            <h4 className="text-sm font-semibold mb-2">Synchronized Data</h4>
            <div className="space-y-2">
              {Object.keys(platform.id === 'linkedin' || platform.id === 'twitter' ?
                { contacts: 'Contacts', posts: 'Posts' } :
                { contacts: 'Contacts', messages: 'Messages' }).map(syncType => (
                <div key={syncType} className="flex items-center justify-between">
                  <span className="text-sm">{syncType === 'contacts' ? 'Contacts' :
                    syncType === 'posts' ? 'Posts' :
                    syncType === 'messages' ? 'Messages' :
                    syncType === 'followers' ? 'Followers' :
                    syncType === 'companies' ? 'Companies' :
                    syncType === 'tweets' ? 'Tweets' : syncType}</span>
                  <div className="flex items-center space-x-2">
                    {renderSyncStatus(platform.id, syncType)}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSync(platform.id, syncType)}
                      disabled={syncStatus[`${platform.id}-${syncType}`] === 'syncing'}
                    >
                      {syncStatus[`${platform.id}-${syncType}`] === 'syncing' ? 'Syncing...' : 'Sync Now'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            <h4 className="text-sm font-semibold mt-4 mb-2">Available Tools</h4>
            <ul className="list-disc list-inside text-sm text-gray-600">
              {platform.capabilities.map((capability, index) => (
                <li key={index}>{capability}</li>
              ))}
            </ul>
          </div>
        )}
      </Card>
    );
  };

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Platform Integrations</h2>
        <Button
          variant="outline"
          onClick={fetchConnections}
          disabled={isLoading}
        >
          <Icon name="refresh" className="mr-2" />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert type="error" className="mb-4">
          {error}
        </Alert>
      )}

      {isLoading && !error ? (
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      ) : (
        <div>
          {PLATFORMS.map(renderPlatformCard)}
        </div>
      )}
    </div>
  );
};

export default PlatformIntegration;
