'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Canvas } from '@/components/Canvas';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader, AlertCircle, Check, Shield, ShieldCheck, Info } from 'lucide-react';
import { Button } from '@/components/Button';
import { canvasPerformance } from '@/utils/canvasPerformance';
import { useTrustVerification } from '@/hooks/useTrustVerification';
import { TrustVerificationBadge } from '@/components/TrustVerificationBadge';
import { TrustVerificationOverlay } from '@/components/TrustVerificationOverlay';
import { VisualizationLayers } from '@/components/Canvas/VisualizationLayers';

interface CognitiveCanvasProps {
  documentId?: string;
  userId?: string;
  userName?: string;
  readonly?: boolean;
}

export function CognitiveCanvas({
  documentId,
  userId,
  userName,
  readonly = false,
}: CognitiveCanvasProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [roomId, setRoomId] = useState<string | null>(null);
  const [perfMetrics, setPerfMetrics] = useState<Record<string, number>>({});
  const [showVerificationOverlay, setShowVerificationOverlay] = useState(false);
  const [showVisualizationLayers, setShowVisualizationLayers] = useState(false);
  const [showVerificationLayer, setShowVerificationLayer] = useState(false);

  // Get document ID from props or URL
  const docId = documentId || searchParams?.get('id') || 'default';
  const user = userId || 'user-' + Math.floor(Math.random() * 10000);
  const displayName = userName || 'Guest User';

  // Trust verification integration
  const {
    verificationData,
    loading: verificationLoading,
    verifyContent,
    isVerified
  } = useTrustVerification({
    canvasId: docId,
    enabled: true
  });

  // Function to fetch real-time performance metrics (if in development/demo mode)
  const updatePerformanceMetrics = useCallback(() => {
    if (process.env.NODE_ENV === 'development' || searchParams?.get('showMetrics')) {
      const metrics = canvasPerformance.getAllAverageMetrics();
      setPerfMetrics(metrics);
    }
  }, [searchParams]);

  // Initialize canvas and establish WebSocket connection
  useEffect(() => {
    setIsLoading(true);
    setError(null);

    // Set a unique room ID for this document
    const generatedRoomId = `canvas-${docId}-${Date.now()}`;
    setRoomId(generatedRoomId);
    
    const connectTimeout = setTimeout(() => {
      if (!isConnected) {
        setError('Connection timeout. Please check your internet connection.');
      }
    }, 10000);

    // Set up performance monitoring interval
    let metricsInterval: NodeJS.Timeout | null = null;
    if (process.env.NODE_ENV === 'development' || searchParams?.get('showMetrics')) {
      metricsInterval = setInterval(updatePerformanceMetrics, 2000);
    }

    setIsLoading(false);

    return () => {
      clearTimeout(connectTimeout);
      if (metricsInterval) {
        clearInterval(metricsInterval);
      }
    };
  }, [docId, isConnected, searchParams, updatePerformanceMetrics]);

  const handleConnectionChange = useCallback((connected: boolean) => {
    setIsConnected(connected);
    if (connected) {
      setError(null);
    }
  }, []);

  const handleVerifyContent = useCallback(async () => {
    if (!docId) return;
    
    try {
      // Get canvas state for verification (in a real implementation, you would get the actual content)
      const canvasState = {
        docId,
        user,
        timestamp: new Date().toISOString(),
        // In a real implementation, we would include the actual shapes, layers, etc.
      };
      
      await verifyContent(JSON.stringify(canvasState));
    } catch (error) {
      console.error('Error verifying content:', error);
    }
  }, [docId, user, verifyContent]);

  // Compute verification status for UI display
  const verificationStatusElement = useMemo(() => {
    if (verificationLoading) {
      return (
        <div className="flex items-center animate-pulse">
          <Shield className="h-4 w-4 text-gray-400 mr-1" />
          <span className="text-xs text-gray-400">Checking...</span>
        </div>
      );
    }
    
    return (
      <TrustVerificationBadge
        verificationData={verificationData}
        canvasId={docId}
        size="small"
        onClick={() => setShowVerificationOverlay(true)}
      />
    );
  }, [verificationData, verificationLoading, docId]);

  if (isLoading) {
    return (
      <div className="flex h-[80vh] w-full flex-col items-center justify-center">
        <Loader className="mb-4 h-12 w-12 animate-spin text-blue-500" />
        <p className="text-lg">Loading Cognitive Canvas...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[80vh] w-full flex-col items-center justify-center">
        <AlertCircle className="mb-4 h-12 w-12 text-red-500" />
        <p className="mb-4 text-lg text-red-500">{error}</p>
        <Button onClick={() => window.location.reload()}>Try Again</Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-2">
      {/* Header information */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <h2 className="text-lg font-semibold">Cognitive Canvas</h2>
          <div className="ml-4 flex items-center space-x-2">
            <span className="text-sm text-gray-500">Document ID: {docId}</span>
            <span className="text-sm text-gray-500">|</span>
            <div className="flex items-center space-x-1">
              <span className="text-sm text-gray-500">Status:</span>
              {isConnected ? (
                <span className="flex items-center text-sm text-green-500">
                  <Check className="mr-1 h-4 w-4" /> Connected
                </span>
              ) : (
                <span className="flex items-center text-sm text-orange-500">
                  <Loader className="mr-1 h-4 w-4 animate-spin" /> Connecting...
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {verificationStatusElement}
          
          {readonly && (
            <div className="rounded bg-amber-100 px-2 py-1 text-xs text-amber-800 dark:bg-amber-900 dark:text-amber-200">
              View Only Mode
            </div>
          )}
          
          <Button 
            variant={showVisualizationLayers ? "primary" : "ghost"} 
            size="sm"
            onClick={() => setShowVisualizationLayers(!showVisualizationLayers)}
          >
            Layers
          </Button>
        </div>
      </div>

      {/* Visualization and Canvas Container */}
      <div className="flex gap-4">
        {/* Main Canvas */}
        <div className="flex-grow rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          {roomId && (
            <Canvas
              roomId={roomId}
              userId={user}
              readonly={readonly}
              verificationStatus={{
                isVerified: isVerified,
                showVerificationLayer: showVerificationLayer,
                certificateData: verificationData?.certificate ? {
                  id: verificationData.certificate.id,
                  issuer: verificationData.certificate.issuer,
                  timestamp: verificationData.certificate.issued_at
                } : undefined
              }}
              onToggleVerificationLayer={() => setShowVerificationLayer(!showVerificationLayer)}
            />
          )}
        </div>
        
        {/* Visualization Layers Panel */}
        {showVisualizationLayers && (
          <div className="w-80 shrink-0">
            {roomId && <VisualizationLayers canvasId={docId} />}
          </div>
        )}
      </div>

      {/* Trust Verification Info */}
      {!isVerified && !readonly && (
        <div className="bg-blue-50 border border-blue-100 rounded-md p-3 text-blue-800 text-sm flex items-start">
          <Info className="h-5 w-5 mr-2 flex-shrink-0 text-blue-500 mt-0.5" />
          <div>
            <p className="font-medium">Content verification available</p>
            <p className="mt-1">
              Verify this canvas content to create a trusted record on the blockchain.
              This provides a tamper-proof mechanism for ensuring content hasn't been modified.
            </p>
            <div className="mt-2">
              <Button 
                size="sm" 
                onClick={() => setShowVerificationOverlay(true)}
              >
                Verify Content
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Performance metrics (only in development/demo mode) */}
      {(process.env.NODE_ENV === 'development' || searchParams?.get('showMetrics')) && Object.keys(perfMetrics).length > 0 && (
        <div className="mt-4 rounded border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
          <h3 className="mb-2 text-sm font-semibold">Performance Metrics</h3>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
            {Object.entries(perfMetrics).map(([key, value]) => (
              <div key={key} className="rounded bg-gray-100 p-2 dark:bg-gray-700">
                <div className="text-xs text-gray-500 dark:text-gray-300">{key}</div>
                <div className="text-sm font-medium">{value.toFixed(2)} ms</div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Verification Overlay */}
      {showVerificationOverlay && (
        <TrustVerificationOverlay
          verificationData={verificationData}
          loading={verificationLoading}
          canvasId={docId}
          onClose={() => setShowVerificationOverlay(false)}
          onVerifyContent={handleVerifyContent}
        />
      )}
    </div>
  );
}