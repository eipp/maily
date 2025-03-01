import React, { useState, useEffect } from 'react';
import { Card, Spinner, Button } from '../ui';

interface BlockchainVerification {
  id: string;
  contactId: string;
  timestamp: string;
  transaction_hash: string;
  block_number: number;
  network: string;
  verification_type: 'initial' | 'update' | 'consent' | 'validation';
  status: 'pending' | 'confirmed' | 'failed';
  data_hash: string;
  explorer_url?: string;
  verification_details: {
    consent_recorded?: boolean;
    consent_source?: string;
    consent_date?: string;
    contact_data_verified?: boolean;
    validation_score?: number;
  };
}

interface BlockchainVerificationProps {
  contactId: string;
  contactEmail: string;
  onVerificationComplete?: (verification: BlockchainVerification) => void;
}

export const BlockchainVerification: React.FC<BlockchainVerificationProps> = ({
  contactId,
  contactEmail,
  onVerificationComplete
}) => {
  const [verifications, setVerifications] = useState<BlockchainVerification[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);

  useEffect(() => {
    fetchVerifications();
  }, [contactId]);

  const fetchVerifications = async () => {
    setLoading(true);
    setError(null);

    try {
      // This would be a real API call in production
      const response = await fetch(`/api/contacts/${contactId}/blockchain-verifications`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch blockchain verifications');
      }

      const data = await response.json();
      setVerifications(data.verifications);
    } catch (err) {
      setError('Error fetching verifications: ' + (err as Error).message);
      console.error('Error fetching verifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const verifyOnBlockchain = async () => {
    setIsVerifying(true);
    setError(null);

    try {
      // This would be a real API call in production
      const response = await fetch(`/api/contacts/${contactId}/verify-blockchain`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          verification_type: 'validation',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to initiate blockchain verification');
      }

      const data = await response.json();

      // Add new verification to the list
      setVerifications(prev => [...prev, data.verification]);

      if (onVerificationComplete) {
        onVerificationComplete(data.verification);
      }
    } catch (err) {
      setError('Error creating verification: ' + (err as Error).message);
      console.error('Error creating verification:', err);
    } finally {
      setIsVerifying(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const shortenHash = (hash: string) => {
    if (!hash) return '';
    return `${hash.substring(0, 6)}...${hash.substring(hash.length - 4)}`;
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getVerificationTypeLabel = (type: string) => {
    switch (type) {
      case 'initial':
        return 'Initial Registration';
      case 'update':
        return 'Data Update';
      case 'consent':
        return 'Consent Recording';
      case 'validation':
        return 'Contact Validation';
      default:
        return type;
    }
  };

  // Visual indicator for blockchain trust level
  const renderTrustLevel = () => {
    if (verifications.length === 0) {
      return (
        <div className="text-center mb-6">
          <div className="text-gray-400 mb-2">No blockchain verification</div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div className="bg-gray-400 h-2.5 rounded-full" style={{ width: '0%' }}></div>
          </div>
        </div>
      );
    }

    // Count confirmed verifications
    const confirmedCount = verifications.filter(v => v.status === 'confirmed').length;
    const trustPercentage = Math.min(100, (confirmedCount / 4) * 100); // Max trust at 4 verifications

    let trustColor = 'bg-red-500';
    let trustText = 'Low Trust';

    if (trustPercentage >= 75) {
      trustColor = 'bg-green-500';
      trustText = 'High Trust';
    } else if (trustPercentage >= 50) {
      trustColor = 'bg-yellow-500';
      trustText = 'Medium Trust';
    } else if (trustPercentage >= 25) {
      trustColor = 'bg-orange-500';
      trustText = 'Basic Trust';
    }

    return (
      <div className="text-center mb-6">
        <div className="flex justify-between mb-1">
          <span className="text-sm text-gray-700">Blockchain Trust Level</span>
          <span className="text-sm text-gray-700">{trustText}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div className={`${trustColor} h-2.5 rounded-full`} style={{ width: `${trustPercentage}%` }}></div>
        </div>
      </div>
    );
  };

  // Compact summary of the latest verification
  const renderLatestVerification = () => {
    if (verifications.length === 0) return null;

    // Sort by timestamp descending
    const latestVerification = [...verifications].sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )[0];

    return (
      <div className="bg-gray-50 p-4 mb-6 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-900">Latest Verification</h4>
          <span className={`px-2.5 py-0.5 text-xs font-medium rounded-full ${getStatusBadgeClass(latestVerification.status)}`}>
            {latestVerification.status}
          </span>
        </div>

        <div className="text-xs text-gray-600 grid grid-cols-2 gap-2">
          <div>Verification Type:</div>
          <div className="font-medium">{getVerificationTypeLabel(latestVerification.verification_type)}</div>

          <div>Timestamp:</div>
          <div className="font-medium">{formatDate(latestVerification.timestamp)}</div>

          <div>Transaction:</div>
          <div className="font-medium">
            {latestVerification.explorer_url ? (
              <a
                href={latestVerification.explorer_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                {shortenHash(latestVerification.transaction_hash)}
              </a>
            ) : (
              shortenHash(latestVerification.transaction_hash)
            )}
          </div>

          <div>Network:</div>
          <div className="font-medium">{latestVerification.network}</div>
        </div>
      </div>
    );
  };

  return (
    <Card className="overflow-hidden">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Blockchain Verification</h3>
            <p className="text-sm text-gray-500">{contactEmail}</p>
          </div>
          <Button
            onClick={verifyOnBlockchain}
            disabled={isVerifying}
            size="sm"
          >
            {isVerifying ? <Spinner size="sm" className="mr-2" /> : null}
            {isVerifying ? 'Verifying...' : 'Verify on Blockchain'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 text-sm">
          {error}
        </div>
      )}

      <div className="p-6">
        {loading && verifications.length === 0 ? (
          <div className="flex justify-center">
            <Spinner size="lg" />
          </div>
        ) : (
          <>
            {renderTrustLevel()}
            {renderLatestVerification()}

            <h4 className="font-medium text-gray-900 mb-4">Verification History</h4>

            {verifications.length === 0 ? (
              <div className="text-center py-6 bg-gray-50 rounded-lg">
                <p className="text-gray-500">No blockchain verifications available for this contact.</p>
                <p className="text-sm text-gray-400 mt-1">Verify this contact to create an immutable record.</p>
              </div>
            ) : (
              <div className="bg-white shadow overflow-hidden rounded-lg">
                <ul className="divide-y divide-gray-200">
                  {[...verifications]
                    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                    .map((verification) => (
                      <li key={verification.id} className="px-4 py-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className={`mr-3 w-2 h-2 rounded-full ${
                              verification.status === 'confirmed' ? 'bg-green-500' :
                              verification.status === 'pending' ? 'bg-yellow-500' : 'bg-red-500'
                            }`}></div>
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {getVerificationTypeLabel(verification.verification_type)}
                              </p>
                              <p className="text-xs text-gray-500">
                                {formatDate(verification.timestamp)}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              getStatusBadgeClass(verification.status)
                            }`}>
                              {verification.status}
                            </span>
                            <p className="text-xs text-gray-500 mt-1">
                              Block: {verification.block_number || 'Pending'}
                            </p>
                          </div>
                        </div>

                        <div className="mt-2 text-xs text-gray-600">
                          <div className="flex space-x-1 items-center">
                            <span>Tx:</span>
                            {verification.explorer_url ? (
                              <a
                                href={verification.explorer_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                              >
                                {shortenHash(verification.transaction_hash)}
                              </a>
                            ) : (
                              <span>{shortenHash(verification.transaction_hash)}</span>
                            )}
                          </div>

                          {/* Verification details */}
                          {verification.verification_details && (
                            <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-2 pt-2 border-t border-gray-100">
                              {verification.verification_details.consent_recorded !== undefined && (
                                <>
                                  <div>Consent recorded:</div>
                                  <div className="font-medium">
                                    {verification.verification_details.consent_recorded ? 'Yes' : 'No'}
                                  </div>
                                </>
                              )}

                              {verification.verification_details.consent_source && (
                                <>
                                  <div>Consent source:</div>
                                  <div className="font-medium">
                                    {verification.verification_details.consent_source}
                                  </div>
                                </>
                              )}

                              {verification.verification_details.validation_score !== undefined && (
                                <>
                                  <div>Validation score:</div>
                                  <div className="font-medium">
                                    {verification.verification_details.validation_score}%
                                  </div>
                                </>
                              )}
                            </div>
                          )}
                        </div>
                      </li>
                    ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </Card>
  );
};

export default BlockchainVerification;
