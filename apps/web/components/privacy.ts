export interface NotificationPreferences {
  email_updates: boolean;
  product_news: boolean;
}

export interface ConsentPreferences {
  user_id: string;
  essential: boolean;
  functional: boolean;
  analytics: boolean;
  marketing: boolean;
  notification_preferences: NotificationPreferences;
  last_updated: string;
  ip_address?: string;
  user_agent?: string;
}

export type RequestStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface DataDeletionRequest {
  id: string;
  user_id: string;
  status: RequestStatus;
  request_date: string;
  execution_date: string;
  completed_date?: string;
  reason?: string;
  data_categories: string[];
}

export interface DataExportRequest {
  id: string;
  user_id: string;
  status: RequestStatus;
  request_date: string;
  completed_date?: string;
  download_url?: string;
  expiry_date?: string;
  format: string;
  data_categories: string[];
}

export interface ConsentLog {
  id: string;
  user_id: string;
  timestamp: string;
  action: string;
  preferences_before?: Partial<ConsentPreferences>;
  preferences_after: ConsentPreferences;
  ip_address?: string;
  user_agent?: string;
}

export interface PrivacySettings {
  consentPreferences: ConsentPreferences;
  consentHistory: ConsentLog[];
  deletionRequests: DataDeletionRequest[];
  exportRequests: DataExportRequest[];
}

export interface PrivacyState extends PrivacySettings {
  loading: boolean;
  saving: boolean;
  error?: string;
}

export interface PrivacyContextType extends PrivacyState {
  updateConsentPreferences: (preferences: Partial<ConsentPreferences>) => Promise<void>;
  requestDataDeletion: () => Promise<void>;
  requestDataExport: () => Promise<void>;
  anonymizeAccount: () => Promise<void>;
  deleteCookies: () => Promise<void>;
  refreshPrivacyData: () => Promise<void>;
}
