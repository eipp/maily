'use client';

import React from 'react';
import { Shield, ShieldCheck, ShieldAlert, ExternalLink } from 'lucide-react';
import { Button } from '@/components/Button';
import { Tooltip } from '@/components/ui/tooltip';
import { TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';

export interface VerificationData {
  status: {
    status: 'verified' | 'pending' | 'unverified' | 'failed';
    timestamp: string;
    message: string;
  };
  certificate?: {
    id: string;
    issuer: string;
    subject: string;
    issued_at: string;
    content_hash: string;
  };
  blockchain?: {
    transaction_id: string;
    block_number?: number;
    network: string;
    contract_address: string;
    timestamp?: string;
  };
  qr_code?: string;
}

interface TrustVerificationBadgeProps {
  verificationData: VerificationData | null;
  loading?: boolean;
  canvasId: string;
  onClick?: () => void;
  size?: 'small' | 'medium' | 'large';
  showDetails?: boolean;
}

export function TrustVerificationBadge({
  verificationData,
  loading = false,
  canvasId,
  onClick,
  size = 'medium',
  showDetails = false,
}: TrustVerificationBadgeProps) {
  if (loading) {
    return (
      <div className="flex items-center animate-pulse">
        <Shield className="h-5 w-5 text-gray-400" />
        <span className="ml-2 text-gray-400 text-sm">Checking verification...</span>
      </div>
    );
  }

  if (!verificationData) {
    return (
      <div className="flex items-center">
        <Shield className="h-5 w-5 text-gray-400" />
        <span className="ml-2 text-gray-400 text-sm">Not verified</span>
      </div>
    );
  }

  const { status, certificate, blockchain } = verificationData;
  
  // Determine icon and color based on status
  let icon = <Shield className={`${getSizeClass(size)} text-gray-400`} />;
  let bgColor = 'bg-gray-100';
  let textColor = 'text-gray-700';
  let borderColor = 'border-gray-200';

  if (status.status === 'verified') {
    icon = <ShieldCheck className={`${getSizeClass(size)} text-green-500`} />;
    bgColor = 'bg-green-50';
    textColor = 'text-green-700';
    borderColor = 'border-green-200';
  } else if (status.status === 'pending') {
    icon = <Shield className={`${getSizeClass(size)} text-amber-500`} />;
    bgColor = 'bg-amber-50';
    textColor = 'text-amber-700';
    borderColor = 'border-amber-200';
  } else if (status.status === 'failed') {
    icon = <ShieldAlert className={`${getSizeClass(size)} text-red-500`} />;
    bgColor = 'bg-red-50';
    textColor = 'text-red-700';
    borderColor = 'border-red-200';
  }

  const truncateString = (str: string, maxLength = 12) => {
    if (!str) return '';
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength / 2) + '...' + str.substring(str.length - maxLength / 2);
  };

  const handleVerifyOnBlockchain = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (blockchain?.transaction_id) {
      const networkUrl = getExplorerUrl(blockchain.network, blockchain.transaction_id);
      window.open(networkUrl, '_blank');
    }
  };

  const getExplorerUrl = (network: string, txId: string) => {
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
  };

  // Simple badge without details
  if (!showDetails) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge 
              onClick={onClick}
              className={`cursor-pointer flex items-center gap-1 ${bgColor} ${textColor} hover:${bgColor} border ${borderColor}`}
            >
              {icon}
              <span>{status.status === 'verified' ? 'Verified' : status.status}</span>
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>{status.message}</p>
            {status.timestamp && (
              <p className="text-xs opacity-70 mt-1">
                {new Date(status.timestamp).toLocaleString()}
              </p>
            )}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Detailed badge with certificate and blockchain info
  return (
    <div 
      className={`border rounded-md p-3 ${bgColor} ${textColor} ${borderColor}`}
      onClick={onClick}
    >
      <div className="flex items-center gap-2 font-medium">
        {icon}
        <span>
          {status.status === 'verified' ? 'Verified Content' : 
           status.status === 'pending' ? 'Verification Pending' : 
           status.status === 'failed' ? 'Verification Failed' : 
           'Unverified Content'}
        </span>
      </div>
      
      <p className="mt-1 text-sm">{status.message}</p>
      
      {certificate && (
        <div className="mt-2 text-xs">
          <div className="flex justify-between">
            <span className="opacity-70">Certificate ID:</span>
            <span className="font-mono">{truncateString(certificate.id, 14)}</span>
          </div>
          <div className="flex justify-between mt-1">
            <span className="opacity-70">Issuer:</span>
            <span>{certificate.issuer}</span>
          </div>
          <div className="flex justify-between mt-1">
            <span className="opacity-70">Issued:</span>
            <span>{new Date(certificate.issued_at).toLocaleDateString()}</span>
          </div>
        </div>
      )}
      
      {blockchain && (
        <div className="mt-2 border-t border-opacity-30 pt-2">
          <div className="flex justify-between text-xs">
            <span className="opacity-70">Network:</span>
            <span>{blockchain.network}</span>
          </div>
          {blockchain.block_number && (
            <div className="flex justify-between text-xs mt-1">
              <span className="opacity-70">Block:</span>
              <span>{blockchain.block_number}</span>
            </div>
          )}
          <div className="mt-2">
            <Button
              size="sm"
              variant="outline"
              className="w-full text-xs flex items-center justify-center"
              onClick={handleVerifyOnBlockchain}
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              Verify on Blockchain
            </Button>
          </div>
        </div>
      )}
      
      {verificationData.qr_code && (
        <div className="mt-3 flex justify-center">
          <img 
            src={verificationData.qr_code} 
            alt="Verification QR Code" 
            className="w-20 h-20 object-contain" 
          />
        </div>
      )}
    </div>
  );
}

function getSizeClass(size: 'small' | 'medium' | 'large') {
  switch (size) {
    case 'small':
      return 'h-3 w-3';
    case 'large':
      return 'h-6 w-6';
    case 'medium':
    default:
      return 'h-4 w-4';
  }
}