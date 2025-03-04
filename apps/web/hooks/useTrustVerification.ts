'use client';

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { VerificationData } from '@/components/TrustVerificationBadge';

interface UseTrustVerificationProps {
  canvasId: string;
  enabled?: boolean;
}

export function useTrustVerification({ canvasId, enabled = true }: UseTrustVerificationProps) {
  const [verificationData, setVerificationData] = useState<VerificationData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchVerificationData = useCallback(async () => {
    if (!canvasId || !enabled) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`/api/v1/canvas/${canvasId}/verification`);
      setVerificationData(response.data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch verification data'));
      console.error('Error fetching verification data:', err);
    } finally {
      setLoading(false);
    }
  }, [canvasId, enabled]);

  const verifyContent = useCallback(async (content?: string) => {
    if (!canvasId) {
      throw new Error('Canvas ID is required for verification');
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // If content is not provided, use the current canvas state
      const contentToVerify = content || JSON.stringify({ canvasId, timestamp: new Date().toISOString() });
      
      const response = await axios.post(`/api/v1/canvas/${canvasId}/verify`, {
        content: contentToVerify
      });
      
      setVerificationData(response.data);
      return response.data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to verify content');
      setError(error);
      console.error('Error verifying content:', err);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [canvasId]);

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      fetchVerificationData();
    }
  }, [fetchVerificationData, enabled]);

  return {
    verificationData,
    loading,
    error,
    fetchVerificationData,
    verifyContent,
    isVerified: verificationData?.status?.status === 'verified'
  };
}