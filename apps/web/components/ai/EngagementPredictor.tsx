import React, { useState } from 'react';
import { Button, Card, CardContent, CardHeader, Chip, CircularProgress, Divider, FormControl, InputLabel, MenuItem, Select, TextField, Typography, Box, Alert } from '@mui/material';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';

interface PredictionResult {
  predictions: Record<string, number>;
  model_version: string;
  timestamp: string;
}

interface EngagementPredictorProps {
  campaignId?: string;
  emailIds?: string[];
  onPredictionComplete?: (predictions: Record<string, number>) => void;
}

const fetchPredictions = async (emailIds: string[], campaignId?: string) => {
  const response = await axios.post('/api/ai/predict-engagement', {
    email_ids: emailIds,
    campaign_id: campaignId
  });
  return response.data as PredictionResult;
};

const EngagementPredictor: React.FC<EngagementPredictorProps> = ({
  campaignId,
  emailIds: initialEmailIds = [],
  onPredictionComplete
}) => {
  const [emailIds, setEmailIds] = useState<string[]>(initialEmailIds);
  const [emailIdInput, setEmailIdInput] = useState<string>('');
  const [showResults, setShowResults] = useState<boolean>(false);

  const { mutate, isLoading, data, error, isError } = useMutation({
    mutationFn: (ids: string[]) => fetchPredictions(ids, campaignId),
    onSuccess: (data) => {
      setShowResults(true);
      if (onPredictionComplete) {
        onPredictionComplete(data.predictions);
      }
    }
  });

  const handleAddEmailId = () => {
    if (emailIdInput.trim()) {
      setEmailIds([...emailIds, emailIdInput.trim()]);
      setEmailIdInput('');
    }
  };

  const handleRemoveEmailId = (index: number) => {
    const newEmailIds = [...emailIds];
    newEmailIds.splice(index, 1);
    setEmailIds(newEmailIds);
  };

  const handlePredict = () => {
    if (emailIds.length > 0) {
      mutate(emailIds);
    }
  };

  const getEngagementLabel = (score: number): string => {
    if (score >= 0.7) return 'High';
    if (score >= 0.4) return 'Medium';
    return 'Low';
  };

  const getEngagementColor = (score: number): string => {
    if (score >= 0.7) return 'success';
    if (score >= 0.4) return 'warning';
    return 'error';
  };

  return (
    <Card variant="outlined" sx={{ maxWidth: 800, mx: 'auto', my: 2 }}>
      <CardHeader
        title="Email Engagement Predictor"
        subheader="Predict how likely recipients are to engage with your emails"
      />
      <Divider />
      <CardContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Add email IDs to predict engagement probability
          </Typography>

          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <TextField
              label="Email ID"
              variant="outlined"
              size="small"
              fullWidth
              value={emailIdInput}
              onChange={(e) => setEmailIdInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddEmailId()}
            />
            <Button
              variant="contained"
              onClick={handleAddEmailId}
              disabled={!emailIdInput.trim()}
            >
              Add
            </Button>
          </Box>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            {emailIds.map((id, index) => (
              <Chip
                key={index}
                label={id}
                onDelete={() => handleRemoveEmailId(index)}
              />
            ))}
          </Box>

          <Button
            variant="contained"
            color="primary"
            fullWidth
            disabled={emailIds.length === 0 || isLoading}
            onClick={handlePredict}
            startIcon={isLoading ? <CircularProgress size={20} /> : null}
          >
            {isLoading ? 'Predicting...' : 'Predict Engagement'}
          </Button>
        </Box>

        {isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Error: {(error as any)?.message || 'Failed to predict engagement'}
          </Alert>
        )}

        {showResults && data && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Prediction Results
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
              Model: {data.model_version}
            </Typography>

            <Box sx={{ mt: 2 }}>
              {Object.entries(data.predictions).map(([emailId, score]) => (
                <Box
                  key={emailId}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 1,
                    borderBottom: '1px solid',
                    borderColor: 'divider'
                  }}
                >
                  <Typography variant="body2">{emailId}</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2">{(score * 100).toFixed(1)}%</Typography>
                    <Chip
                      size="small"
                      label={getEngagementLabel(score)}
                      color={getEngagementColor(score) as any}
                    />
                  </Box>
                </Box>
              ))}
            </Box>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={() => setShowResults(false)}
              >
                Hide Results
              </Button>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default EngagementPredictor;
