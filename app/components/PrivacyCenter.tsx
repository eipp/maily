import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Switch,
  FormGroup,
  FormControlLabel,
  Button,
  Divider,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Grid,
  Card,
  CardContent,
  CardActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip
} from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { privacyApi } from '../../frontend/services/privacyApi';
import { format } from 'date-fns';

interface ConsentPreferences {
  essential: boolean;
  functional: boolean;
  analytics: boolean;
  marketing: boolean;
  notification_preferences: {
    email_updates: boolean;
    product_news: boolean;
  };
}

interface ConsentLog {
  id: string;
  timestamp: string;
  action: string;
  preferences_before: Partial<ConsentPreferences>;
  preferences_after: ConsentPreferences;
}

export const PrivacyCenter: React.FC = () => {
  const { user } = useAuth();
  const [preferences, setPreferences] = useState<ConsentPreferences>({
    essential: true,
    functional: false,
    analytics: false,
    marketing: false,
    notification_preferences: {
      email_updates: false,
      product_news: false
    }
  });
  const [consentHistory, setConsentHistory] = useState<ConsentLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [exportStatus, setExportStatus] = useState<{ url?: string; status: string }>({ status: 'idle' });
  const [deleteStatus, setDeleteStatus] = useState<{ status: string }>({ status: 'idle' });

  useEffect(() => {
    loadPreferences();
    loadConsentHistory();
  }, []);

  const loadPreferences = async () => {
    try {
      const response = await privacyApi.getConsentPreferences();
      setPreferences(response);
    } catch (error) {
      showSnackbar('Error loading preferences', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadConsentHistory = async () => {
    try {
      const history = await privacyApi.getConsentHistory();
      setConsentHistory(history);
    } catch (error) {
      showSnackbar('Error loading consent history', 'error');
    }
  };

  const handlePreferenceChange = async (key: keyof ConsentPreferences) => {
    if (key === 'essential') return; // Essential cookies cannot be disabled
    
    const newPreferences = {
      ...preferences,
      [key]: !preferences[key]
    };
    
    try {
      setSaving(true);
      await privacyApi.updateConsentPreferences(newPreferences);
      setPreferences(newPreferences);
      showSnackbar('Preferences updated successfully', 'success');
      loadConsentHistory(); // Refresh history
    } catch (error) {
      showSnackbar('Error updating preferences', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleNotificationPreferenceChange = async (key: string) => {
    const newPreferences = {
      ...preferences,
      notification_preferences: {
        ...preferences.notification_preferences,
        [key]: !preferences.notification_preferences[key]
      }
    };
    
    try {
      setSaving(true);
      await privacyApi.updateConsentPreferences(newPreferences);
      setPreferences(newPreferences);
      showSnackbar('Notification preferences updated', 'success');
      loadConsentHistory();
    } catch (error) {
      showSnackbar('Error updating notification preferences', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDataDeletion = async () => {
    try {
      setDeleteStatus({ status: 'pending' });
      await privacyApi.requestDataDeletion();
      setDeleteDialogOpen(false);
      showSnackbar('Data deletion request submitted. This will be processed in 30 days.', 'success');
      setDeleteStatus({ status: 'requested' });
    } catch (error) {
      showSnackbar('Error requesting data deletion', 'error');
      setDeleteStatus({ status: 'error' });
    }
  };

  const handleDataExport = async () => {
    try {
      setExportStatus({ status: 'pending' });
      const response = await privacyApi.requestDataExport();
      setExportDialogOpen(false);
      showSnackbar('Data export request submitted. You will be notified when ready.', 'success');
      setExportStatus({ status: 'processing', url: response.download_url });
    } catch (error) {
      showSnackbar('Error requesting data export', 'error');
      setExportStatus({ status: 'error' });
    }
  };

  const handleAnonymizeAccount = async () => {
    try {
      await privacyApi.anonymizeAccount();
      showSnackbar('Account anonymization requested', 'success');
    } catch (error) {
      showSnackbar('Error requesting account anonymization', 'error');
    }
  };

  const handleDeleteCookies = async () => {
    try {
      await privacyApi.deleteCookies();
      showSnackbar('Non-essential cookies deleted', 'success');
      loadPreferences(); // Refresh preferences
    } catch (error) {
      showSnackbar('Error deleting cookies', 'error');
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Privacy Center
      </Typography>
      
      <Grid container spacing={4}>
        {/* Cookie Preferences */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cookie Preferences
              </Typography>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.essential}
                      disabled
                    />
                  }
                  label={
                    <Box>
                      <Typography>Essential Cookies</Typography>
                      <Typography variant="caption" color="textSecondary">
                        Required for basic site functionality
                      </Typography>
                    </Box>
                  }
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.functional}
                      onChange={() => handlePreferenceChange('functional')}
                      disabled={saving}
                    />
                  }
                  label={
                    <Box>
                      <Typography>Functional Cookies</Typography>
                      <Typography variant="caption" color="textSecondary">
                        Enhance site functionality and personalization
                      </Typography>
                    </Box>
                  }
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.analytics}
                      onChange={() => handlePreferenceChange('analytics')}
                      disabled={saving}
                    />
                  }
                  label={
                    <Box>
                      <Typography>Analytics Cookies</Typography>
                      <Typography variant="caption" color="textSecondary">
                        Help us understand how you use our site
                      </Typography>
                    </Box>
                  }
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.marketing}
                      onChange={() => handlePreferenceChange('marketing')}
                      disabled={saving}
                    />
                  }
                  label={
                    <Box>
                      <Typography>Marketing Cookies</Typography>
                      <Typography variant="caption" color="textSecondary">
                        Used for targeted advertising
                      </Typography>
                    </Box>
                  }
                />
              </FormGroup>
            </CardContent>
            <CardActions>
              <Button
                onClick={handleDeleteCookies}
                color="secondary"
                disabled={saving}
              >
                Delete Non-Essential Cookies
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Notification Preferences */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notification Preferences
              </Typography>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notification_preferences.email_updates}
                      onChange={() => handleNotificationPreferenceChange('email_updates')}
                      disabled={saving}
                    />
                  }
                  label="Email Updates"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notification_preferences.product_news}
                      onChange={() => handleNotificationPreferenceChange('product_news')}
                      disabled={saving}
                    />
                  }
                  label="Product News"
                />
              </FormGroup>
            </CardContent>
          </Card>
        </Grid>

        {/* Data Management */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Management
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Button
                    variant="outlined"
                    color="primary"
                    fullWidth
                    onClick={() => setExportDialogOpen(true)}
                    disabled={exportStatus.status === 'pending'}
                  >
                    Export My Data
                  </Button>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Button
                    variant="outlined"
                    color="warning"
                    fullWidth
                    onClick={() => setDeleteDialogOpen(true)}
                    disabled={deleteStatus.status === 'pending'}
                  >
                    Delete My Data
                  </Button>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Button
                    variant="outlined"
                    color="secondary"
                    fullWidth
                    onClick={handleAnonymizeAccount}
                  >
                    Anonymize Account
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Consent History */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Consent History
              </Typography>
              <List>
                {consentHistory.map((log) => (
                  <ListItem key={log.id}>
                    <ListItemText
                      primary={`${log.action.charAt(0).toUpperCase() + log.action.slice(1)} consent preferences`}
                      secondary={format(new Date(log.timestamp), 'PPpp')}
                    />
                    <ListItemSecondaryAction>
                      <Chip
                        size="small"
                        label={format(new Date(log.timestamp), 'PP')}
                        color="primary"
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Data Export Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>Export Your Data</DialogTitle>
        <DialogContent>
          <Typography>
            You will receive a downloadable file containing all your personal data. This process may take a few minutes.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDataExport}
            color="primary"
            disabled={exportStatus.status === 'pending'}
          >
            {exportStatus.status === 'pending' ? 'Processing...' : 'Export'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Data Deletion Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Your Data</DialogTitle>
        <DialogContent>
          <Typography color="error" paragraph>
            Warning: This action cannot be undone.
          </Typography>
          <Typography>
            Your data will be permanently deleted after a 30-day cooling period. During this time, you can cancel the deletion request.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDataDeletion}
            color="error"
            disabled={deleteStatus.status === 'pending'}
          >
            {deleteStatus.status === 'pending' ? 'Processing...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity as 'success' | 'error'}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}; 