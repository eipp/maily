import { useState } from 'react';
import { useRouter } from 'next/router';
// Using @tanstack/react-query instead of react-query
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface ContactDiscoveryParams {
  target_criteria: Record<string, any>;
  discovery_depth?: string;
  enrichment_level?: string;
}

interface Contact {
  id: string;
  name: string;
  email: string;
  role?: string;
  company?: string;
  industry?: string;
  quality_score?: number;
  [key: string]: any;
}

interface ContactDiscoveryResponse {
  contacts: Contact[];
  count: number;
  has_more: boolean;
}

export const useContactDiscovery = () => {
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const queryClient = useQueryClient();

  // Mutation for discovering contacts
  const { mutate, isLoading } = useMutation(
    async (params: ContactDiscoveryParams) => {
      try {
        const response = await fetch('/api/contacts/discover', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(params),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to discover contacts');
        }

        return await response.json() as ContactDiscoveryResponse;
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
      onSuccess: (data: ContactDiscoveryResponse) => {
        // Invalidate contacts query to refresh the list
        queryClient.invalidateQueries('contacts');

        // Redirect to contacts page if contacts were found
        if (data.contacts.length > 0) {
          router.push('/contacts');
        }
      },
    }
  );

  const discoverContacts = async (params: ContactDiscoveryParams) => {
    setError(null);
    return mutate(params);
  };

  return {
    discoverContacts,
    isLoading,
    error,
  };
};
