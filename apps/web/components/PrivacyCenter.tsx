'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/Button';
import { usePrivacy } from '@/components/PrivacyContext';
import { Shield, Info, Check, X } from 'lucide-react';
import { analyticsService } from '@/services/analytics';
import { cn } from '@/lib/utils';

interface PrivacyCategory {
  key: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  required?: boolean;
}

const privacyCategories: PrivacyCategory[] = [
  {
    key: 'essential',
    label: 'Essential',
    description: 'Required for the website to function properly. These cookies cannot be disabled.',
    icon: <Shield className="size-5 text-blue-600" />,
    required: true,
  },
  {
    key: 'functional',
    label: 'Functional',
    description: 'Enable enhanced functionality and personalization features.',
    icon: <Shield className="size-5 text-blue-600" />,
  },
  {
    key: 'analytics',
    label: 'Analytics',
    description: 'Help us understand how visitors interact with our website.',
    icon: <Info className="size-5 text-yellow-600" />,
  },
  {
    key: 'marketing',
    label: 'Marketing',
    description: 'Used for targeted advertising and marketing purposes.',
    icon: <Info className="size-5 text-green-600" />,
  },
];

export function PrivacyCenter() {
  const { preferences, setPreferences } = usePrivacy();
  const [showToast, setShowToast] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 500));
        setLoading(false);
      } catch (err) {
        setError('Failed to load privacy preferences');
        setLoading(false);
      }
    };

    void loadPreferences();
  }, []);

  const handlePreferenceChange = (key: string, value: boolean) => {
    if (key === 'essential') return;

    setPreferences({
      ...preferences,
      [key]: value,
    });

    // Track preference change
    analyticsService.trackEvent('privacy_preference_changed', {
      category: key,
      value,
    });
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Show success toast
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);

      // Track successful save
      analyticsService.trackEvent('privacy_preferences_saved', preferences);
    } catch (err) {
      setError('Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="size-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-center text-red-800">
        <p>{error}</p>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setError(null)}
          className="mt-4"
        >
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Privacy Preferences</h2>
        <p className="mt-2 text-sm text-gray-600">
          Manage your privacy preferences and cookie settings. Some features are essential for the
          website to function and cannot be disabled.
        </p>
      </div>

      <div className="space-y-6">
        {privacyCategories.map(({ key, label, description, icon, required }) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              'rounded-lg border p-4 transition-colors',
              preferences[key as keyof typeof preferences]
                ? 'border-blue-100 bg-blue-50'
                : 'border-gray-200 bg-white'
            )}
          >
            <div className="flex items-start space-x-4">
              <div className="shrink-0">{icon}</div>
              <div className="grow">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">{label}</h3>
                  <label className="relative inline-flex cursor-pointer items-center">
                    <input
                      type="checkbox"
                      checked={preferences[key as keyof typeof preferences]}
                      onChange={e => handlePreferenceChange(key, e.target.checked)}
                      disabled={required}
                      className="peer sr-only"
                    />
                    <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:size-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 peer-disabled:cursor-not-allowed peer-disabled:opacity-50" />
                  </label>
                </div>
                <p className="mt-1 text-sm text-gray-600">{description}</p>
                {required && (
                  <p className="mt-2 text-xs text-gray-500">
                    This setting cannot be disabled as it is required for basic functionality.
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="flex justify-end space-x-4">
        <Button
          variant="secondary"
          onClick={() => window.history.back()}
        >
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleSave}
          isLoading={loading}
          leftIcon={loading ? undefined : <Check className="size-4" />}
        >
          Save Preferences
        </Button>
      </div>

      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-4 right-4 z-50 flex items-center space-x-2 rounded-lg bg-green-600 px-4 py-2 text-white shadow-lg"
          >
            <Check className="size-5" />
            <span>Preferences saved successfully</span>
            <button
              onClick={() => setShowToast(false)}
              className="ml-2 rounded-full p-1 hover:bg-green-700"
            >
              <X className="size-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
