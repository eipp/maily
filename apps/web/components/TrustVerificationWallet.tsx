'use client';

import React, { useState, useEffect } from 'react';
import { Wallet, Shield, AlertCircle, Check, Loader2, ExternalLink } from 'lucide-react';
import { Button } from '@/components/Button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

interface Certificate {
  id: string;
  recipient: string;
  issuer: string;
  created_at: string;
  expires_at: string | null;
  status: string;
  metadata: {
    certificate_type: number;
    content_hash?: string;
    canvas_id?: string;
    [key: string]: any;
  };
  network: string;
  contract_address: string;
  transaction_id?: string;
}

interface TrustVerificationWalletProps {
  userId: string;
  onConnect?: () => void;
  onTokenTransfer?: (tokenId: string, recipient: string) => Promise<boolean>;
}

export function TrustVerificationWallet({ 
  userId, 
  onConnect,
  onTokenTransfer 
}: TrustVerificationWalletProps) {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transferring, setTransferring] = useState<string | null>(null);
  const [recipient, setRecipient] = useState('');
  const [showTransferForm, setShowTransferForm] = useState<string | null>(null);
  const [walletConnected, setWalletConnected] = useState(false);

  useEffect(() => {
    const fetchCertificates = async () => {
      try {
        setLoading(true);
        // Check if wallet is connected first
        const walletResponse = await fetch('/api/user/wallet-status');
        const walletData = await walletResponse.json();
        
        setWalletConnected(walletData.connected);
        
        if (walletData.connected) {
          // Fetch certificates
          const response = await fetch(`/api/trust-verification/tokens?userId=${userId}`);
          
          if (!response.ok) {
            throw new Error(`Failed to fetch tokens: ${response.status}`);
          }
          
          const data = await response.json();
          setCertificates(data.tokens || []);
        }
        
        setError(null);
      } catch (err) {
        console.error('Error fetching certificates:', err);
        setError('Failed to load certificates. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchCertificates();
    }
  }, [userId]);

  const handleConnectWallet = async () => {
    try {
      setLoading(true);
      // Make API call to connect wallet
      const response = await fetch('/api/user/connect-wallet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to connect wallet: ${response.status}`);
      }
      
      setWalletConnected(true);
      
      // Fetch certificates after connecting
      const certsResponse = await fetch(`/api/trust-verification/tokens?userId=${userId}`);
      const data = await certsResponse.json();
      setCertificates(data.tokens || []);
      
      // Call onConnect callback if provided
      if (onConnect) {
        onConnect();
      }
      
      setError(null);
    } catch (err) {
      console.error('Error connecting wallet:', err);
      setError('Failed to connect wallet. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleTransfer = async (tokenId: string) => {
    if (!recipient.trim()) {
      setError('Please enter a recipient address or email');
      return;
    }
    
    try {
      setTransferring(tokenId);
      
      // Call onTokenTransfer callback if provided
      if (onTokenTransfer) {
        const success = await onTokenTransfer(tokenId, recipient);
        
        if (success) {
          // Update the local certificates array
          setCertificates(prev => 
            prev.filter(cert => cert.id !== tokenId)
          );
          setShowTransferForm(null);
          setRecipient('');
        } else {
          throw new Error('Token transfer failed');
        }
      } else {
        // Default implementation if no callback provided
        const response = await fetch('/api/trust-verification/transfer', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            tokenId,
            recipient,
          }),
        });
        
        if (!response.ok) {
          throw new Error(`Failed to transfer token: ${response.status}`);
        }
        
        // Update the local certificates array
        setCertificates(prev => 
          prev.filter(cert => cert.id !== tokenId)
        );
        setShowTransferForm(null);
        setRecipient('');
      }
      
      setError(null);
    } catch (err) {
      console.error('Error transferring token:', err);
      setError('Failed to transfer token. Please check the recipient address and try again.');
    } finally {
      setTransferring(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const truncateAddress = (address: string) => {
    if (!address) return '';
    return address.length > 10 
      ? `${address.substring(0, 6)}...${address.substring(address.length - 4)}`
      : address;
  };

  // If loading
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Wallet className="mr-2 h-5 w-5" />
            Trust Certificates
          </CardTitle>
          <CardDescription>
            Your verified content certificates
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  // If wallet not connected
  if (!walletConnected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Wallet className="mr-2 h-5 w-5" />
            Trust Certificates
          </CardTitle>
          <CardDescription>
            Connect your wallet to view and manage your certificates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Wallet className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 mb-6">
              Connect your wallet to access your verified content certificates and rewards
            </p>
            <Button onClick={handleConnectWallet}>
              Connect Wallet
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // If error
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Wallet className="mr-2 h-5 w-5" />
            Trust Certificates
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-red-50 border border-red-200 rounded-md p-4 flex items-start">
            <AlertCircle className="h-5 w-5 text-red-500 mr-3 mt-0.5" />
            <div>
              <p className="text-red-800">{error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-3"
                onClick={() => window.location.reload()}
              >
                Try Again
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // If no certificates
  if (certificates.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Wallet className="mr-2 h-5 w-5" />
            Trust Certificates
          </CardTitle>
          <CardDescription>
            Your verified content certificates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Shield className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500">
              You don't have any certificates yet. Verify your content to receive certificates.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Normal view with certificates
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Wallet className="mr-2 h-5 w-5" />
          Trust Certificates
        </CardTitle>
        <CardDescription>
          Your verified content certificates ({certificates.length})
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="w-full">
          {certificates.map((cert, index) => (
            <AccordionItem value={cert.id} key={cert.id}>
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center justify-between w-full pr-4">
                  <div className="flex items-center">
                    <Shield className="h-4 w-4 mr-2 text-green-500" />
                    <span className="font-medium">
                      {cert.metadata.canvas_id ? `Canvas Certificate` : `Certificate ${index + 1}`}
                    </span>
                  </div>
                  <Badge variant="outline" className="ml-auto mr-4">
                    {cert.status}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="pl-6 pt-2 pb-1 space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-1">
                    <span className="text-gray-500">Certificate ID:</span>
                    <span className="font-mono text-xs truncate">{truncateAddress(cert.id)}</span>
                    
                    <span className="text-gray-500">Issuer:</span>
                    <span>{cert.issuer}</span>
                    
                    <span className="text-gray-500">Issued Date:</span>
                    <span>{formatDate(cert.created_at)}</span>
                    
                    {cert.expires_at && (
                      <>
                        <span className="text-gray-500">Expires:</span>
                        <span>{formatDate(cert.expires_at)}</span>
                      </>
                    )}
                    
                    <span className="text-gray-500">Network:</span>
                    <span className="capitalize">{cert.network}</span>
                  </div>
                  
                  {cert.metadata.canvas_id && (
                    <div className="pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full text-xs"
                        onClick={() => window.open(`/canvas/${cert.metadata.canvas_id}`, '_blank')}
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        View Content
                      </Button>
                    </div>
                  )}
                  
                  {cert.transaction_id && (
                    <div className="pt-1">
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full text-xs"
                        onClick={() => {
                          const explorerUrl = getExplorerUrl(cert.network, cert.transaction_id!);
                          window.open(explorerUrl, '_blank');
                        }}
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        View on Blockchain
                      </Button>
                    </div>
                  )}
                  
                  {showTransferForm === cert.id ? (
                    <div className="pt-4 border-t border-gray-100 mt-3">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Recipient Address or Email
                      </label>
                      <input
                        type="text"
                        value={recipient}
                        onChange={(e) => setRecipient(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary text-sm"
                        placeholder="0x... or email@example.com"
                      />
                      <div className="flex space-x-2 mt-3">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => {
                            setShowTransferForm(null);
                            setRecipient('');
                          }}
                        >
                          Cancel
                        </Button>
                        <Button
                          size="sm"
                          className="flex-1"
                          onClick={() => handleTransfer(cert.id)}
                          disabled={transferring === cert.id || !recipient.trim()}
                        >
                          {transferring === cert.id ? (
                            <>
                              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                              Transferring...
                            </>
                          ) : (
                            'Transfer'
                          )}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="pt-1">
                      <Button
                        variant="default"
                        size="sm"
                        className="w-full text-xs"
                        onClick={() => setShowTransferForm(cert.id)}
                      >
                        Transfer Certificate
                      </Button>
                    </div>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </CardContent>
    </Card>
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