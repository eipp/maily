'use client';

import React, { useState } from 'react';
import { Shield, ShieldCheck, X, Info, ExternalLink } from 'lucide-react';
import { Button } from '@/components/Button';
import { TrustVerificationBadge, VerificationData } from './TrustVerificationBadge';

interface TrustVerificationOverlayProps {
  verificationData: VerificationData | null;
  loading?: boolean;
  canvasId: string;
  onClose: () => void;
  onVerifyContent: () => Promise<void>;
}

export function TrustVerificationOverlay({
  verificationData,
  loading = false,
  canvasId,
  onClose,
  onVerifyContent,
}: TrustVerificationOverlayProps) {
  const [verifying, setVerifying] = useState(false);

  const handleVerifyContent = async () => {
    setVerifying(true);
    try {
      await onVerifyContent();
    } finally {
      setVerifying(false);
    }
  };

  const isVerified = verificationData?.status?.status === 'verified';
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-auto dark:bg-gray-800">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-medium flex items-center">
            {isVerified ? (
              <>
                <ShieldCheck className="h-5 w-5 text-green-500 mr-2" />
                <span>Content Verification</span>
              </>
            ) : (
              <>
                <Shield className="h-5 w-5 mr-2" />
                <span>Content Verification</span>
              </>
            )}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-10">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <p className="mt-4 text-sm text-gray-500">Loading verification data...</p>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <TrustVerificationBadge 
                  verificationData={verificationData}
                  canvasId={canvasId}
                  showDetails={true}
                />
              </div>
              
              {!isVerified && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-blue-800 text-sm mb-6 flex">
                  <Info className="h-5 w-5 mr-2 flex-shrink-0 text-blue-500" />
                  <div>
                    Verification provides tamper-proof evidence that your content hasn't been modified. 
                    The verification data is stored on the blockchain, ensuring transparency and trust.
                  </div>
                </div>
              )}
              
              <div className="flex flex-col space-y-3">
                {!isVerified && (
                  <Button 
                    onClick={handleVerifyContent} 
                    disabled={verifying}
                    className="w-full"
                  >
                    {verifying ? 'Verifying...' : 'Verify This Content'}
                  </Button>
                )}
                
                {isVerified && verificationData?.blockchain?.transaction_id && (
                  <Button 
                    variant="outline"
                    className="w-full flex items-center justify-center"
                    onClick={() => {
                      const networkUrl = getExplorerUrl(
                        verificationData.blockchain!.network, 
                        verificationData.blockchain!.transaction_id
                      );
                      window.open(networkUrl, '_blank');
                    }}
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View on Blockchain Explorer
                  </Button>
                )}
                
                {isVerified && (
                  <Button 
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      // Create URL for verification badge
                      const verificationUrl = `/api/v1/canvas/${canvasId}/verification/badge`;
                      window.open(verificationUrl, '_blank');
                    }}
                  >
                    Download Verification Badge
                  </Button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function getExplorerUrl(network: string, txId: string) {
  switch (network.toLowerCase()) {
    case 'ethereum':
    case 'eth':
      return `https://etherscan.io/tx/${txId}`;
    case 'polygon':
    case 'matic':
      return `https://polygonscan.com/tx/${txId}`;
    case 'arbitrum':
      return `https://arbiscan.io/tx/${txId}`;
    case 'optimism':
      return `https://optimistic.etherscan.io/tx/${txId}`;
    case 'base':
      return `https://basescan.org/tx/${txId}`;
    case 'testnet':
    default:
      return `https://sepolia.etherscan.io/tx/${txId}`;
  }
}