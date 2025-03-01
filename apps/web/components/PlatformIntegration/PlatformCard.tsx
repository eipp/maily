import React, { useState } from 'react';
import { Card, Button, Icon, Badge } from '../../ui';
import { usePlatformSync } from '../../hooks/usePlatformSync';

interface PlatformCardProps {
  platform: {
    id: string;
    name: string;
    icon: string;
    isConnected: boolean;
    lastSynced?: string;
  };
  onConnect: (platformId: string) => void;
}

export const PlatformCard: React.FC<PlatformCardProps> = ({
  platform,
  onConnect
}) => {
  const { syncPlatform, isLoading, error } = usePlatformSync();
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle');

  const handleSync = async () => {
    setSyncStatus('syncing');
    try {
      await syncPlatform(platform.id);
      setSyncStatus('success');
      setTimeout(() => setSyncStatus('idle'), 3000);
    } catch (err) {
      setSyncStatus('error');
      setTimeout(() => setSyncStatus('idle'), 3000);
    }
  };

  return (
    <Card className="p-4 flex flex-col items-center">
      <div className="h-16 w-16 flex items-center justify-center mb-3">
        <Icon name={platform.icon} className="h-10 w-10 text-gray-600" />
      </div>

      <h3 className="text-lg font-medium mb-1">{platform.name}</h3>

      {platform.isConnected && (
        <Badge color="green" className="mb-3">Connected</Badge>
      )}

      {platform.lastSynced && (
        <p className="text-xs text-gray-500 mb-3">
          Last synced: {new Date(platform.lastSynced).toLocaleDateString()}
        </p>
      )}

      {platform.isConnected ? (
        <Button
          size="sm"
          variant={syncStatus === 'syncing' ? 'outline' : 'default'}
          onClick={handleSync}
          disabled={syncStatus === 'syncing'}
          className="w-full"
        >
          {syncStatus === 'syncing' ? (
            <>
              <Icon name="refresh" className="h-4 w-4 mr-1 animate-spin" />
              Syncing...
            </>
          ) : syncStatus === 'success' ? (
            <>
              <Icon name="check" className="h-4 w-4 mr-1" />
              Synced!
            </>
          ) : syncStatus === 'error' ? (
            <>
              <Icon name="alert-triangle" className="h-4 w-4 mr-1" />
              Retry
            </>
          ) : (
            'Sync Data'
          )}
        </Button>
      ) : (
        <Button
          size="sm"
          variant="outline"
          onClick={() => onConnect(platform.id)}
          className="w-full"
        >
          Connect
        </Button>
      )}

      {error && (
        <p className="text-xs text-red-500 mt-2">{error}</p>
      )}
    </Card>
  );
};
