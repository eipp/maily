import React from 'react';
import { Card } from '../ui';

interface HealthScore {
  overall: number;
  email_validity: number;
  engagement: number;
  deliverability: number;
  consent_level: string;
  domain_reputation: number;
  last_evaluated: string;
}

interface ContactHealthVisualizationProps {
  healthScore: HealthScore;
}

export const ContactHealthVisualization: React.FC<ContactHealthVisualizationProps> = ({
  healthScore
}) => {
  // Calculate the circumference and offset for SVG circular progress
  const calculateCircle = (score: number) => {
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    return { radius, circumference, offset };
  };

  const circle = calculateCircle(healthScore.overall);

  // Generate visual indicators for different health metrics
  const gaugeColors = {
    high: 'text-green-500',
    medium: 'text-yellow-500',
    low: 'text-red-500'
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return gaugeColors.high;
    if (score >= 40) return gaugeColors.medium;
    return gaugeColors.low;
  };

  const renderDetailedMetric = (label: string, score: number) => (
    <div className="flex flex-col items-center p-4">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="40"
            className="stroke-gray-200"
            strokeWidth="8"
            fill="transparent"
          />
          {/* Foreground circle */}
          <circle
            cx="50"
            cy="50"
            r="40"
            className={`${getScoreColor(score)} transition-all duration-500 ease-in-out`}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={2 * Math.PI * 40}
            strokeDashoffset={2 * Math.PI * 40 - (score / 100) * (2 * Math.PI * 40)}
            fill="transparent"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`${getScoreColor(score)} text-lg font-bold`}>{Math.round(score)}</span>
        </div>
      </div>
      <span className="text-sm font-medium text-gray-700 mt-2">{label}</span>
    </div>
  );

  // Determine consent level indicator
  const getConsentLevelIndicator = () => {
    switch (healthScore.consent_level) {
      case 'explicit':
        return (
          <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Explicit Consent
          </div>
        );
      case 'implied':
        return (
          <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            Implied Consent
          </div>
        );
      default:
        return (
          <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Unknown Consent
          </div>
        );
    }
  };

  return (
    <Card className="overflow-hidden">
      <div className="p-6">
        <h3 className="text-lg font-medium text-gray-900">Contact Health Visualization</h3>
        <p className="text-sm text-gray-500">
          Last evaluated: {new Date(healthScore.last_evaluated).toLocaleDateString()}
        </p>
      </div>

      {/* Main health score dial */}
      <div className="flex flex-col items-center p-6 border-t border-b border-gray-200">
        <div className="relative w-48 h-48 mb-4">
          <svg className="w-48 h-48 transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r={circle.radius}
              className="stroke-gray-200"
              strokeWidth="10"
              fill="transparent"
            />
            <circle
              cx="50"
              cy="50"
              r={circle.radius}
              className={`${getScoreColor(healthScore.overall)} transition-all duration-1000 ease-out`}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circle.circumference}
              strokeDashoffset={circle.offset}
              fill="transparent"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-3xl font-bold">{healthScore.overall}</span>
            <span className="text-sm font-medium text-gray-500">Overall Health</span>
          </div>
        </div>

        {/* Consent level indicator */}
        <div className="mt-2">
          {getConsentLevelIndicator()}
        </div>

        {/* Health score summary */}
        <div className="w-full max-w-md mt-6">
          <div className="grid grid-cols-3 gap-4">
            {renderDetailedMetric('Email Validity', healthScore.email_validity)}
            {renderDetailedMetric('Engagement', healthScore.engagement)}
            {renderDetailedMetric('Deliverability', healthScore.deliverability)}
          </div>
        </div>
      </div>

      {/* Domain reputation section */}
      <div className="p-6">
        <h4 className="font-medium text-gray-900 mb-2">Domain Reputation</h4>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full ${getScoreColor(healthScore.domain_reputation * 100)}`}
            style={{ width: `${healthScore.domain_reputation * 100}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Poor</span>
          <span>Moderate</span>
          <span>Excellent</span>
        </div>
      </div>

      {/* Recommendations */}
      <div className="p-6 bg-gray-50">
        <h4 className="font-medium text-gray-900 mb-2">Recommendations</h4>
        <ul className="space-y-2 text-sm">
          {healthScore.email_validity < 70 && (
            <li className="flex items-start">
              <svg className="h-5 w-5 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9z" clipRule="evenodd" />
              </svg>
              Verify email address with SMTP check
            </li>
          )}
          {healthScore.engagement < 50 && (
            <li className="flex items-start">
              <svg className="h-5 w-5 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9z" clipRule="evenodd" />
              </svg>
              Create re-engagement campaign
            </li>
          )}
          {healthScore.deliverability < 60 && (
            <li className="flex items-start">
              <svg className="h-5 w-5 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9z" clipRule="evenodd" />
              </svg>
              Check for bounce issues
            </li>
          )}
          {healthScore.consent_level !== 'explicit' && (
            <li className="flex items-start">
              <svg className="h-5 w-5 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9z" clipRule="evenodd" />
              </svg>
              Obtain explicit consent
            </li>
          )}
          {healthScore.domain_reputation < 0.7 && (
            <li className="flex items-start">
              <svg className="h-5 w-5 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9z" clipRule="evenodd" />
              </svg>
              Review domain reputation
            </li>
          )}
          {healthScore.overall >= 80 && (
            <li className="flex items-start">
              <svg className="h-5 w-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Contact is in good health
            </li>
          )}
        </ul>
      </div>
    </Card>
  );
};

export default ContactHealthVisualization;
