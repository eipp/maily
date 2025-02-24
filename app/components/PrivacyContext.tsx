import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { privacyApi } from '../../frontend/services/privacyApi';
import type {
  PrivacyContextType,
  ConsentPreferences,
  ConsentLog,
  DataDeletionRequest,
  DataExportRequest
} from './privacy';

const defaultState: PrivacyContextType = {
  consentPreferences: {
    user_id: '',
    essential: true,
    functional: false,
    analytics: false,
    marketing: false,
    notification_preferences: {
      email_updates: false,
      product_news: false
    },
    last_updated: new Date().toISOString()
  },
  consentHistory: [],
  deletionRequests: [],
  exportRequests: [],
  loading: true,
  saving: false,
  updateConsentPreferences: async () => {},
  requestDataDeletion: async () => {},
  requestDataExport: async () => {},
  anonymizeAccount: async () => {},
  deleteCookies: async () => {},
  refreshPrivacyData: async () => {}
};

const PrivacyContext = createContext<PrivacyContextType>(defaultState);

export const usePrivacy = () => {
  const context = useContext(PrivacyContext);
  if (!context) {
    throw new Error('usePrivacy must be used within a PrivacyProvider');
  }
  return context;
};

interface PrivacyProviderProps {
  children: React.ReactNode;
}

export const PrivacyProvider: React.FC<PrivacyProviderProps> = ({ children }) => {
  const [state, setState] = useState<PrivacyContextType>(defaultState);

  const setLoading = (loading: boolean) => {
    setState(prev => ({ ...prev, loading }));
  };

  const setSaving = (saving: boolean) => {
    setState(prev => ({ ...prev, saving }));
  };

  const setError = (error?: string) => {
    setState(prev => ({ ...prev, error }));
  };

  const refreshPrivacyData = useCallback(async () => {
    try {
      setLoading(true);
      setError(undefined);

      const [preferences, history] = await Promise.all([
        privacyApi.getConsentPreferences(),
        privacyApi.getConsentHistory()
      ]);

      setState(prev => ({
        ...prev,
        consentPreferences: preferences,
        consentHistory: history,
        loading: false
      }));
    } catch (error) {
      setError('Failed to load privacy data');
      console.error('Error loading privacy data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConsentPreferences = async (preferences: Partial<ConsentPreferences>) => {
    try {
      setSaving(true);
      setError(undefined);

      const updatedPreferences = await privacyApi.updateConsentPreferences(preferences);
      
      setState(prev => ({
        ...prev,
        consentPreferences: updatedPreferences
      }));

      // Refresh consent history after update
      const history = await privacyApi.getConsentHistory();
      setState(prev => ({
        ...prev,
        consentHistory: history
      }));
    } catch (error) {
      setError('Failed to update preferences');
      console.error('Error updating preferences:', error);
      throw error;
    } finally {
      setSaving(false);
    }
  };

  const requestDataDeletion = async () => {
    try {
      setSaving(true);
      setError(undefined);

      const request = await privacyApi.requestDataDeletion();
      
      setState(prev => ({
        ...prev,
        deletionRequests: [...prev.deletionRequests, request]
      }));
    } catch (error) {
      setError('Failed to request data deletion');
      console.error('Error requesting data deletion:', error);
      throw error;
    } finally {
      setSaving(false);
    }
  };

  const requestDataExport = async () => {
    try {
      setSaving(true);
      setError(undefined);

      const request = await privacyApi.requestDataExport();
      
      setState(prev => ({
        ...prev,
        exportRequests: [...prev.exportRequests, request]
      }));
    } catch (error) {
      setError('Failed to request data export');
      console.error('Error requesting data export:', error);
      throw error;
    } finally {
      setSaving(false);
    }
  };

  const anonymizeAccount = async () => {
    try {
      setSaving(true);
      setError(undefined);

      await privacyApi.anonymizeAccount();
      await refreshPrivacyData(); // Refresh all privacy data after anonymization
    } catch (error) {
      setError('Failed to anonymize account');
      console.error('Error anonymizing account:', error);
      throw error;
    } finally {
      setSaving(false);
    }
  };

  const deleteCookies = async () => {
    try {
      setSaving(true);
      setError(undefined);

      await privacyApi.deleteCookies();
      await refreshPrivacyData(); // Refresh privacy data after cookie deletion
    } catch (error) {
      setError('Failed to delete cookies');
      console.error('Error deleting cookies:', error);
      throw error;
    } finally {
      setSaving(false);
    }
  };

  // Load initial privacy data
  useEffect(() => {
    refreshPrivacyData();
  }, [refreshPrivacyData]);

  const value: PrivacyContextType = {
    ...state,
    updateConsentPreferences,
    requestDataDeletion,
    requestDataExport,
    anonymizeAccount,
    deleteCookies,
    refreshPrivacyData
  };

  return (
    <PrivacyContext.Provider value={value}>
      {children}
    </PrivacyContext.Provider>
  );
}; 