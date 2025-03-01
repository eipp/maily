import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  IconButton,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  TextField,
  Typography,
  Alert,
  Paper
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

interface OptimizationResult {
  scores: Record<string, number>;
  best_subject: string;
  model_version: string;
  timestamp: string;
}

interface SubjectLineOptimizerProps {
  campaignId?: string;
  initialSubjects?: string[];
  audienceSegments?: string[];
  onOptimizationComplete?: (bestSubject: string, scores: Record<string, number>) => void;
}

const fetchOptimization = async (
  subjectLines: string[],
  audienceSegment: string,
  campaignId?: string
) => {
  const response = await axios.post('/api/ai/optimize-subject', {
    subject_lines: subjectLines,
    audience_segment: audienceSegment,
    campaign_id: campaignId
  });
  return response.data as OptimizationResult;
};

const SubjectLineOptimizer: React.FC<SubjectLineOptimizerProps> = ({
  campaignId,
  initialSubjects = [],
  audienceSegments = ['General', 'New Users', 'Active Users', 'Dormant Users'],
  onOptimizationComplete
}) => {
  const [subjectLines, setSubjectLines] = useState<string[]>(
    initialSubjects.length > 0 ? initialSubjects : ['']
  );
  const [audienceSegment, setAudienceSegment] = useState<string>(audienceSegments[0]);
  const [showResults, setShowResults] = useState<boolean>(false);

  const { mutate, isLoading, data, error, isError } = useMutation({
    mutationFn: (params: { subjects: string[], segment: string }) =>
      fetchOptimization(params.subjects, params.segment, campaignId),
    onSuccess: (data) => {
      setShowResults(true);
      if (onOptimizationComplete) {
        onOptimizationComplete(data.best_subject, data.scores);
      }
    }
  });

  const handleAddSubjectLine = () => {
    setSubjectLines([...subjectLines, '']);
  };

  const handleRemoveSubjectLine = (index: number) => {
    if (subjectLines.length > 1) {
      const newSubjectLines = [...subjectLines];
      newSubjectLines.splice(index, 1);
      setSubjectLines(newSubjectLines);
    }
  };

  const handleSubjectLineChange = (index: number, value: string) => {
    const newSubjectLines = [...subjectLines];
    newSubjectLines[index] = value;
    setSubjectLines(newSubjectLines);
  };

  const handleOptimize = () => {
    // Filter out empty subject lines
    const validSubjects = subjectLines.filter(subject => subject.trim() !== '');

    if (validSubjects.length > 0) {
      mutate({ subjects: validSubjects, segment: audienceSegment });
    }
  };

  const isOptimizeDisabled = () => {
    return subjectLines.filter(subject => subject.trim() !== '').length < 1 || isLoading;
  };

  return (
    <Card variant="outlined" sx={{ maxWidth: 800, mx: 'auto', my: 2 }}>
      <CardHeader
        title="Subject Line Optimizer"
        subheader="Find the most engaging subject line for your audience"
      />
      <Divider />
      <CardContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Enter multiple subject line options to compare
          </Typography>

          <Box sx={{ mb: 3 }}>
            {subjectLines.map((subject, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  mb: 1,
                  gap: 1
                }}
              >
                <TextField
                  label={`Subject Line ${index + 1}`}
                  variant="outlined"
                  size="small"
                  fullWidth
                  value={subject}
                  onChange={(e) => handleSubjectLineChange(index, e.target.value)}
                />
                <IconButton
                  onClick={() => handleRemoveSubjectLine(index)}
                  disabled={subjectLines.length <= 1}
                  size="small"
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            ))}

            <Button
              startIcon={<AddIcon />}
              onClick={handleAddSubjectLine}
              sx={{ mt: 1 }}
            >
              Add Another Subject Line
            </Button>
          </Box>

          <FormControl fullWidth size="small" sx={{ mb: 3 }}>
            <InputLabel>Target Audience Segment</InputLabel>
            <Select
              value={audienceSegment}
              label="Target Audience Segment"
              onChange={(e) => setAudienceSegment(e.target.value)}
            >
              {audienceSegments.map((segment) => (
                <MenuItem key={segment} value={segment}>
                  {segment}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="contained"
            color="primary"
            fullWidth
            disabled={isOptimizeDisabled()}
            onClick={handleOptimize}
            startIcon={isLoading ? <CircularProgress size={20} /> : null}
          >
            {isLoading ? 'Optimizing...' : 'Optimize Subject Lines'}
          </Button>
        </Box>

        {isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Error: {(error as any)?.message || 'Failed to optimize subject lines'}
          </Alert>
        )}

        {showResults && data && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Optimization Results
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
              Model: {data.model_version} | Audience: {audienceSegment}
            </Typography>

            <Paper
              variant="outlined"
              sx={{
                p: 2,
                mb: 3,
                bgcolor: 'success.light',
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <CheckCircleIcon color="success" />
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Recommended Subject Line:
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  {data.best_subject}
                </Typography>
              </Box>
            </Paper>

            <Typography variant="subtitle2" gutterBottom>
              All Subject Lines Ranked:
            </Typography>

            <Box sx={{ mt: 2 }}>
              {Object.entries(data.scores)
                .sort((a, b) => b[1] - a[1])
                .map(([subject, score], index) => (
                  <Box
                    key={index}
                    sx={{
                      mb: 2,
                      p: 1,
                      borderLeft: '4px solid',
                      borderColor: subject === data.best_subject ? 'success.main' : 'divider',
                      bgcolor: subject === data.best_subject ? 'success.50' : 'background.paper'
                    }}
                  >
                    <Typography variant="body2" fontWeight={subject === data.best_subject ? 'bold' : 'normal'}>
                      {subject}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                      <Box sx={{ flexGrow: 1, mr: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={score * 100}
                          color={subject === data.best_subject ? "success" : "primary"}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {(score * 100).toFixed(1)}%
                      </Typography>
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

export default SubjectLineOptimizer;
