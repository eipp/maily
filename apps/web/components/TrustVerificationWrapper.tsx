'use client';

import React, { useState, useEffect } from 'react';
import { TrustVerificationBadge, VerificationData } from './TrustVerificationBadge';
import { TrustVerificationOverlay } from './TrustVerificationOverlay';
import { Button } from '@/components/Button';
import { Shield } from 'lucide-react';

interface TrustVerificationWrapperProps {
  canvasId: string;
  emailId?: string;
  showBadge?: boolean;
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

export function TrustVerificationWrapper({
  canvasId,
  emailId,
  showBadge = true,
  size = 'medium',
  className,
}: TrustVerificationWrapperProps) {
  const [loading, setLoading] = useState(true);
  const [verificationData, setVerificationData] = useState<VerificationData | null>(null);
  const [showOverlay, setShowOverlay] = useState(false);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    const fetchVerificationData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/trust-verification/data/${canvasId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch verification data: ${response.status}`);
        }
        
        const data = await response.json();
        setVerificationData(data);
      } catch (err) {
        console.error('Error fetching verification data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (canvasId) {
      fetchVerificationData();
    }
  }, [canvasId]);

  const handleVerifyContent = async () => {
    try {
      setVerifying(true);
      const response = await fetch(`/api/trust-verification/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          canvasId,
          emailId,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to verify content: ${response.status}`);
      }
      
      const data = await response.json();
      setVerificationData(data);
    } catch (err) {
      console.error('Error verifying content:', err);
    } finally {
      setVerifying(false);
    }
  };

  const toggleOverlay = () => {
    setShowOverlay(!showOverlay);
  };

  if (!showBadge) {
    return (
      <Button 
        variant="outline" 
        size="sm" 
        onClick={toggleOverlay}
        className={className}
      >
        <Shield className="h-4 w-4 mr-2" />
        Verify Content
      </Button>
    );
  }

  return (
    <>
      <div className={className} onClick={toggleOverlay}>
        <TrustVerificationBadge
          verificationData={verificationData}
          loading={loading}
          canvasId={canvasId}
          onClick={toggleOverlay}
          size={size}
          showDetails={false}
        />
      </div>
      
      {showOverlay && (
        <TrustVerificationOverlay
          verificationData={verificationData}
          loading={loading}
          canvasId={canvasId}
          onClose={toggleOverlay}
          onVerifyContent={handleVerifyContent}
        />
      )}
    </>
  );
}