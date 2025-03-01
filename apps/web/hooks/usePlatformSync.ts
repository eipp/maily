import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface SyncPlatformParams {
  platform: string;
  sync_all?: boolean;
}

export const usePlatformSync = () => {
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Mutation for syncing platform data
  const { mutate, isLoading } = useMutation(
    async (platformId: string) => {
      try {
        const response = await fetch('/api/platforms/sync', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            platform: platformId,
            sync_all: false
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to sync platform data');
        }

        return await response.json();
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('An unknown error occurred');
        }
        throw err;
      }
    },
    {
      onSuccess: () => {
        // Invalidate platform queries to refresh the data
        queryClient.invalidateQueries(['platforms']);
        queryClient.invalidateQueries(['contacts']);
      },
    }
  );

  const syncPlatform = async (platformId: string) => {
    setError(null);
    return mutate(platformId);
  };

  return {
    syncPlatform,
    isLoading,
    error,
  };
};
