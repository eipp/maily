import React, { useState } from 'react';
import { Card, Button, Spinner } from '../ui';

interface ValidationResult {
  valid: boolean;
  score: number;
  reason: string;
  suggested_correction?: string;
  sources?: string[];
  pattern?: string;
  cluster_size?: number;
}

interface MultiSignalValidationResults {
  email_syntax: ValidationResult;
  domain_reputation: ValidationResult;
  smtp_validation: ValidationResult;
  cross_platform: ValidationResult;
  behavioral_patterns: ValidationResult;
  network_validation: ValidationResult;
  overall_validity: boolean;
  confidence_score: number;
}

interface MultiSignalValidationProps {
  contactId: string;
  contactEmail: string;
  onValidationComplete?: (results: MultiSignalValidationResults) => void;
  initialResults?: MultiSignalValidationResults;
}

export const MultiSignalValidation: React.FC<MultiSignalValidationProps> = ({
  contactId,
  contactEmail,
  onValidationComplete,
  initialResults
}) => {
  const [results, setResults] = useState<MultiSignalValidationResults | null>(initialResults || null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const performValidation = async () => {
    setIsValidating(true);
    setError(null);

    try {
      // This would be a real API call in production
      const response = await fetch(`/api/contacts/${contactId}/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to validate contact');
      }

      const data = await response.json();
      setResults(data.validation_results);

      if (onValidationComplete) {
        onValidationComplete(data.validation_results);
      }
    } catch (err) {
      setError('Error validating contact: ' + (err as Error).message);
      console.error('Error validating contact:', err);
    } finally {
      setIsValidating(false);
    }
  };

  const getValidationStatusIcon = (valid: boolean, score: number) => {
    if (valid && score > 0.7) {
      return <span className="text-green-600 text-xl">✓</span>;
    } else if (valid && score > 0.4) {
      return <span className="text-yellow-500 text-xl">⚠</span>;
    } else {
      return <span className="text-red-600 text-xl">✗</span>;
    }
  };

  const getStatusColor = (score: number) => {
    if (score > 0.7) return 'bg-green-100 text-green-800';
    if (score > 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getSignalStrengthBars = (score: number) => {
    // Display signal strength as bars
    const maxBars = 5;
    const filledBars = Math.round(score * maxBars);

    return (
      <div className="flex space-x-1">
        {[...Array(maxBars)].map((_, i) => (
          <div
            key={i}
            className={`w-1.5 h-5 rounded-sm ${i < filledBars ? 'bg-blue-600' : 'bg-gray-200'}`}
          ></div>
        ))}
      </div>
    );
  };

  // Render validation signals
  const renderValidationSignal = (name: string, result: ValidationResult) => (
    <div className="border-b border-gray-200 pb-4 mb-4 last:border-b-0 last:mb-0 last:pb-0">
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center">
          {getValidationStatusIcon(result.valid, result.score)}
          <h4 className="ml-2 font-medium text-gray-900">{name}</h4>
        </div>
        {getSignalStrengthBars(result.score)}
      </div>
      <p className="text-sm text-gray-600 mb-2">{result.reason}</p>

      {/* Additional details by signal type */}
      {name === 'Email Syntax' && result.suggested_correction && (
        <div className="text-sm bg-blue-50 p-2 rounded">
          <span className="font-medium">Suggested correction:</span> {result.suggested_correction}
        </div>
      )}

      {name === 'Cross-Platform' && result.sources && result.sources.length > 0 && (
        <div className="text-sm">
          <span className="font-medium">Verified sources:</span>{' '}
          {result.sources.map((source, index) => (
            <span
              key={source}
              className="inline-flex items-center mr-2 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
            >
              {source}
            </span>
          ))}
        </div>
      )}

      {name === 'Behavioral Patterns' && result.pattern && (
        <div className="text-sm">
          <span className="font-medium">Detected pattern:</span>{' '}
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
            result.pattern === 'active_engagement' ? 'bg-green-100 text-green-800' :
            result.pattern === 'zero_engagement' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
          }`}>
            {result.pattern}
          </span>
        </div>
      )}

      {name === 'Network Validation' && result.cluster_size && (
        <div className="text-sm">
          <span className="font-medium">Network cluster size:</span> {result.cluster_size}
        </div>
      )}
    </div>
  );

  return (
    <Card className="overflow-hidden">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Multi-Signal Validation Matrix</h3>
            <p className="text-sm text-gray-500">{contactEmail}</p>
          </div>
          <Button
            onClick={performValidation}
            disabled={isValidating}
            size="sm"
          >
            {isValidating ? <Spinner size="sm" className="mr-2" /> : null}
            {isValidating ? 'Validating...' : 'Validate Now'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 text-sm">
          {error}
        </div>
      )}

      {isValidating && !results && (
        <div className="p-6 flex justify-center">
          <div className="text-center">
            <Spinner size="lg" className="mb-4" />
            <p className="text-gray-500">Validating contact across multiple channels...</p>
          </div>
        </div>
      )}

      {results && (
        <div>
          {/* Overall confidence score */}
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-medium text-gray-900">Overall Confidence</h4>
                <p className="text-sm text-gray-500">Based on cross-signal validation</p>
              </div>
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(results.confidence_score)}`}>
                {(results.confidence_score * 100).toFixed(0)}% {results.overall_validity ? 'Valid' : 'Invalid'}
              </div>
            </div>

            {/* Progress bar for confidence score */}
            <div className="mt-3">
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full ${
                    results.confidence_score > 0.7 ? 'bg-green-500' :
                    results.confidence_score > 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${results.confidence_score * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Individual validation signals */}
          <div className="p-6">
            {renderValidationSignal('Email Syntax', results.email_syntax)}
            {renderValidationSignal('Domain Reputation', results.domain_reputation)}
            {renderValidationSignal('SMTP Validation', results.smtp_validation)}
            {renderValidationSignal('Cross-Platform', results.cross_platform)}
            {renderValidationSignal('Behavioral Patterns', results.behavioral_patterns)}
            {renderValidationSignal('Network Validation', results.network_validation)}
          </div>
        </div>
      )}

      {!results && !isValidating && (
        <div className="p-6 text-center">
          <p className="text-gray-500 mb-4">No validation data available. Click the button to validate this contact.</p>
          <Button onClick={performValidation}>Validate Contact</Button>
        </div>
      )}
    </Card>
  );
};

export default MultiSignalValidation;
