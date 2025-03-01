import { api } from './api';
import type {
  ConsentPreferences,
  DataDeletionRequest,
  DataExportRequest,
  ConsentLog,
} from '../types/privacy';

class PrivacyApi {
  /**
   * Get the current user's consent preferences
   */
  async getConsentPreferences(): Promise<ConsentPreferences> {
    const response = await api.get('/privacy/consent');
    return response.data;
  }

  /**
   * Update the user's consent preferences
   */
  async updateConsentPreferences(
    preferences: Partial<ConsentPreferences>
  ): Promise<ConsentPreferences> {
    const response = await api.put('/privacy/consent', preferences);
    return response.data;
  }

  /**
   * Request deletion of all user data
   */
  async requestDataDeletion(): Promise<DataDeletionRequest> {
    const response = await api.post('/privacy/data/delete');
    return response.data;
  }

  /**
   * Check the status of a data deletion request
   */
  async getDeletionStatus(requestId: string): Promise<DataDeletionRequest> {
    const response = await api.get(`/privacy/data/delete/${requestId}`);
    return response.data;
  }

  /**
   * Request export of all user data
   */
  async requestDataExport(): Promise<DataExportRequest> {
    const response = await api.post('/privacy/data/export');
    return response.data;
  }

  /**
   * Check the status of a data export request
   */
  async getExportStatus(requestId: string): Promise<DataExportRequest> {
    const response = await api.get(`/privacy/data/export/${requestId}`);
    return response.data;
  }

  /**
   * Get the history of consent preference changes
   */
  async getConsentHistory(): Promise<ConsentLog[]> {
    const response = await api.get('/privacy/consent/log');
    return response.data;
  }

  /**
   * Anonymize the user's account
   */
  async anonymizeAccount(): Promise<{ message: string; status: string }> {
    const response = await api.post('/privacy/data/anonymize');
    return response.data;
  }

  /**
   * Delete all non-essential cookies
   */
  async deleteCookies(): Promise<{ message: string; status: string }> {
    const response = await api.delete('/privacy/data/cookies');
    return response.data;
  }
}

export const privacyApi = new PrivacyApi();
