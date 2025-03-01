'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { analyticsService } from '@/services/analytics';

interface PrivacyPreferences {
  essential: boolean;
  functional: boolean;
  analytics: boolean;
  marketing: boolean;
}

interface PrivacyContextType {
  preferences: PrivacyPreferences;
  setPreferences: (prefs: PrivacyPreferences) => void;
  resetPreferences: () => void;
  hasConsented: boolean;
  setHasConsented: (value: boolean) => void;
  isLoading: boolean;
  error: string | null;
}

const defaultPreferences: PrivacyPreferences = {
  essential: true, // Always required
  functional: true,
  analytics: false,
  marketing: false,
};

const PrivacyContext = createContext<PrivacyContextType | undefined>(undefined);

export function usePrivacy() {
  const context = useContext(PrivacyContext);
  if (!context) {
    throw new Error('usePrivacy must be used within PrivacyProvider');
  }
  return context;
}

interface PrivacyProviderProps {
  children: React.ReactNode;
}

export function PrivacyProvider({ children }: PrivacyProviderProps) {
  const [preferences, setPreferencesState] = useState<PrivacyPreferences>(defaultPreferences);
  const [hasConsented, setHasConsented] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load preferences from localStorage on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setIsLoading(true);
        const savedPreferences = localStorage.getItem('privacy-preferences');
        const savedConsent = localStorage.getItem('privacy-consent');

        if (savedPreferences) {
          const parsedPreferences = JSON.parse(savedPreferences);
          setPreferencesState({
            ...defaultPreferences,
            ...parsedPreferences,
            essential: true, // Always true
          });
        }

        if (savedConsent) {
          setHasConsented(true);
        }

        // Apply preferences to analytics service
        if (parsedPreferences?.analytics) {
          analyticsService.init();
        }

        setIsLoading(false);
      } catch (err) {
        setError('Failed to load privacy preferences');
        setIsLoading(false);
      }
    };

    void loadPreferences();
  }, []);

  // Save preferences to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('privacy-preferences', JSON.stringify(preferences));

      // Update analytics service based on preferences
      if (preferences.analytics) {
        analyticsService.init();
      } else {
        analyticsService.reset();
      }

      // Track preference changes if analytics is enabled
      if (preferences.analytics) {
        analyticsService.trackEvent('privacy_preferences_updated', {
          preferences,
          timestamp: new Date().toISOString(),
        });
      }
    } catch (err) {
      console.error('Failed to save privacy preferences:', err);
    }
  }, [preferences]);

  const setPreferences = (newPreferences: PrivacyPreferences) => {
    setPreferencesState({
      ...newPreferences,
      essential: true, // Always true
    });
  };

  const resetPreferences = () => {
    setPreferencesState(defaultPreferences);
    setHasConsented(false);
    localStorage.removeItem('privacy-preferences');
    localStorage.removeItem('privacy-consent');

    // Track reset if analytics is enabled
    if (preferences.analytics) {
      analyticsService.trackEvent('privacy_preferences_reset', {
        timestamp: new Date().toISOString(),
      });
    }
  };

  const value: PrivacyContextType = {
    preferences,
    setPreferences,
    resetPreferences,
    hasConsented,
    setHasConsented,
    isLoading,
    error,
  };

  return (
    <PrivacyContext.Provider value={value}>
      {children}
    </PrivacyContext.Provider>
  );
}
