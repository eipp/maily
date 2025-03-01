'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { Button } from '@/components/Button';
import { cn } from '@/lib/utils';

export interface CookiePreferences {
  essential: boolean;
  functional: boolean;
  analytics: boolean;
  marketing: boolean;
}

const defaultPreferences: CookiePreferences = {
  essential: true,
  functional: true,
  analytics: true,
  marketing: false,
};

interface CookieCategory {
  key: keyof CookiePreferences;
  label: string;
  description: string;
  disabled?: boolean;
}

const cookieCategories: CookieCategory[] = [
  {
    key: 'essential',
    label: 'Essential',
    description: 'Required for the website to function properly. Cannot be disabled.',
    disabled: true,
  },
  {
    key: 'functional',
    label: 'Functional',
    description: 'Enables enhanced functionality and personalization.',
  },
  {
    key: 'analytics',
    label: 'Analytics',
    description: 'Helps us understand how visitors interact with the website.',
  },
  {
    key: 'marketing',
    label: 'Marketing',
    description: 'Used for targeted advertising and marketing purposes.',
  },
];

export function CookieConsent() {
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>(defaultPreferences);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const savedPreferences = localStorage.getItem('cookie-preferences');
    const hasConsented = localStorage.getItem('cookie-consent');

    if (savedPreferences) {
      setPreferences(JSON.parse(savedPreferences));
      setIsVisible(false);
    }

    if (hasConsented) {
      setIsVisible(false);
    }
  }, []);

  const applyPreferences = (prefs: CookiePreferences) => {
    // Save preferences
    localStorage.setItem('cookie-preferences', JSON.stringify(prefs));
    localStorage.setItem('cookie-consent', 'true');

    // Apply cookie settings
    if (!prefs.analytics) {
      deleteCookies(['_ga', '_gid', '_gat']);
    }
    if (!prefs.marketing) {
      deleteCookies(['_fbp', '_gcl_au']);
    }
    if (!prefs.functional) {
      deleteCookies(['_preferences', '_session']);
    }

    setIsVisible(false);
  };

  const deleteCookies = (cookieNames: string[]) => {
    cookieNames.forEach(name => {
      document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;`;
    });
  };

  const handleAcceptAll = () => {
    const allEnabled = {
      ...preferences,
      functional: true,
      analytics: true,
      marketing: true,
    };
    setPreferences(allEnabled);
    applyPreferences(allEnabled);
  };

  const handleRejectAll = () => {
    const allDisabled = {
      ...defaultPreferences,
      functional: false,
      analytics: false,
      marketing: false,
    };
    setPreferences(allDisabled);
    applyPreferences(allDisabled);
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          className={cn(
            'fixed inset-x-0 bottom-0 z-50',
            'bg-white dark:bg-gray-800',
            'border-t border-gray-200 dark:border-gray-700',
            'p-4 md:p-6'
          )}
        >
          <div className="mx-auto max-w-7xl">
            <div className="flex flex-col items-start gap-4 md:flex-row md:items-center md:justify-between">
              <div className="flex-1 space-y-2">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Cookie Preferences</h2>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  We use cookies to enhance your browsing experience and analyze our traffic.
                </p>
              </div>
              <div className="flex flex-shrink-0 space-x-4">
                <Button
                  variant="outline"
                  onClick={() => setShowPreferences(true)}
                  className="text-sm"
                >
                  Customize
                </Button>
                <Button
                  variant="primary"
                  onClick={handleAcceptAll}
                  className="text-sm"
                >
                  Accept All
                </Button>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      <AnimatePresence>
        {showPreferences && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-60 flex items-center justify-center bg-black/50 p-4"
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="w-full max-h-[90vh] max-w-2xl overflow-auto rounded-lg bg-white shadow-xl"
            >
              <div className="p-6">
                <h2 className="text-xl font-bold text-gray-900">Cookie Preferences</h2>
                <p className="mt-2 text-sm text-gray-600">
                  Manage your cookie preferences below. Essential cookies cannot be disabled as they are
                  required for the website to function properly.
                </p>

                <div className="mt-6 space-y-6">
                  {cookieCategories.map(({ key, label, description, disabled }) => (
                    <div
                      key={key}
                      className={cn(
                        'flex items-start space-x-4 rounded-lg p-4',
                        preferences[key] ? 'bg-blue-50' : 'bg-gray-50'
                      )}
                    >
                      <div className="flex-1">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={preferences[key]}
                            onChange={(e) =>
                              setPreferences({ ...preferences, [key]: e.target.checked })
                            }
                            disabled={disabled}
                            className="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-3 font-medium text-gray-900">{label}</span>
                        </label>
                        <p className="ml-7 mt-1 text-sm text-gray-600">{description}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-8 flex justify-end gap-3">
                  <Button
                    variant="secondary"
                    onClick={() => setShowPreferences(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => {
                      applyPreferences(preferences);
                      setShowPreferences(false);
                    }}
                  >
                    Save Preferences
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </AnimatePresence>
  );
}
