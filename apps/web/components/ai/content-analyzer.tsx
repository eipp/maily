'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Loader2,
  BarChart3,
  Maximize2,
  ThumbsUp,
  AlertTriangle,
  Target,
  Eye,
  ShieldCheck,
  Gauge,
  BookOpen,
  ExternalLink,
  CornerRightDown
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import { aiService } from '@/lib/ai/ai-service';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';

interface ContentAnalyzerProps {
  content: string;
  subject?: string;
}

interface AnalysisScore {
  clarity: number;
  engagement: number;
  persuasion: number;
  readability: number;
  deliverability: number;
  accessibility: number;
  overall: number;
}

interface AnalysisIssue {
  type: 'warning' | 'suggestion' | 'critical';
  message: string;
  details: string;
  location?: {
    startIndex: number;
    endIndex: number;
  };
}

interface AnalysisResult {
  scores: AnalysisScore;
  issues: AnalysisIssue[];
  recommendations: string[];
  benchmarks: {
    industry: string;
    averageOpenRate: number;
    averageClickRate: number;
    readabilityLevel: string;
  };
}

export function ContentAnalyzer({
  content,
  subject = ''
}: ContentAnalyzerProps) {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Analyze email content
  const analyzeContent = async () => {
    if (!content || content.trim().length < 20) {
      toast({
        title: 'Not enough content',
        description: 'Please add more content to analyze.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);

    try {
      // In a real implementation, we would call the AI service to analyze the content
      // For demonstration purposes, we'll simulate the analysis with mock data

      await new Promise(resolve => setTimeout(resolve, 2000));

      // Create mock analysis results
      const mockResult: AnalysisResult = {
        scores: {
          clarity: Math.random() * 40 + 60, // 60-100
          engagement: Math.random() * 40 + 60,
          persuasion: Math.random() * 40 + 60,
          readability: Math.random() * 40 + 60,
          deliverability: Math.random() * 40 + 60,
          accessibility: Math.random() * 40 + 60,
          overall: 0 // Will be calculated
        },
        issues: [
          {
            type: 'warning',
            message: 'Long sentences may reduce readability',
            details: 'Consider breaking down sentences that are longer than 25 words to improve readability. We found 3 such sentences in your content.'
          },
          {
            type: 'suggestion',
            message: 'Limited use of personalization',
            details: 'Consider adding more personalization tokens like {{first_name}} or dynamic content based on subscriber preferences to increase engagement.'
          },
          {
            type: 'critical',
            message: 'Spam trigger words detected',
            details: 'Some phrases in your email might trigger spam filters. Consider replacing: "free offer", "guarantee", and "buy now".'
          },
          {
            type: 'suggestion',
            message: 'Weak call-to-action',
            details: 'Your call-to-action could be stronger. Consider using action-oriented and value-focused language.'
          }
        ],
        recommendations: [
          'Add a clear and compelling call-to-action button with action-oriented text',
          'Use shorter paragraphs (3-4 lines max) to improve scannability',
          'Add more visual elements to break up text and increase engagement',
          'Consider a more personalized subject line that creates curiosity',
          'Include social proof like testimonials or usage statistics'
        ],
        benchmarks: {
          industry: 'Marketing',
          averageOpenRate: 21.3,
          averageClickRate: 2.7,
          readabilityLevel: 'Grade 10 (Fairly Difficult)'
        }
      };

      // Calculate overall score as average of other scores
      const scores = mockResult.scores;
      scores.overall = Object.values(scores).reduce((sum, score) => sum + score, 0) / 6;

      setAnalysisResult(mockResult);

      toast({
        title: 'Analysis complete',
        description: 'Review the insights to improve your email content',
      });
    } catch (error) {
      console.error('Error analyzing content:', error);
      toast({
        title: 'Error',
        description: 'Failed to analyze content. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Get the appropriate icon and color for a score
  const getScoreIndicator = (score: number) => {
    if (score >= 80) {
      return { icon: <ThumbsUp className="h-4 w-4 text-green-500" />, color: 'text-green-500' };
    } else if (score >= 60) {
      return { icon: <AlertTriangle className="h-4 w-4 text-amber-500" />, color: 'text-amber-500' };
    } else {
      return { icon: <AlertTriangle className="h-4 w-4 text-red-500" />, color: 'text-red-500' };
    }
  };

  // Format score for display
  const formatScore = (score: number): string => {
    return score.toFixed(1);
  };

  // Get icon for issue type
  const getIssueIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'suggestion':
        return <CornerRightDown className="h-4 w-4 text-blue-500" />;
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4" />;
    }
  };

  // Get issue variant
  const getIssueVariant = (type: string) => {
    switch (type) {
      case 'warning':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'suggestion':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'critical':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <BarChart3 className="h-4 w-4" />
          Analyze Email
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Email Content Analysis
          </DialogTitle>
          <DialogDescription>
            Get AI-powered insights to improve your email content performance
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {!analysisResult ? (
            <div className="flex flex-col items-center gap-4 py-8">
              <p className="text-sm text-center text-muted-foreground max-w-md">
                Our AI will analyze your email content and provide insights on readability,
                engagement potential, and deliverability, with specific recommendations for improvement.
              </p>
              <Button
                onClick={analyzeContent}
                className="gap-2"
                disabled={loading || !content}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <BarChart3 className="h-4 w-4" />
                    Analyze Content
                  </>
                )}
              </Button>
            </div>
          ) : (
            <Tabs defaultValue={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid grid-cols-4 mb-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="issues">Issues ({analysisResult.issues.length})</TabsTrigger>
                <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
                <TabsTrigger value="benchmarks">Benchmarks</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-6">
                <div className="flex flex-col items-center py-2">
                  <div className="relative w-32 h-32">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-4xl font-bold">
                        {formatScore(analysisResult.scores.overall)}
                      </span>
                    </div>
                    <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        stroke="#e2e8f0"
                        strokeWidth="10"
                        fill="none"
                      />
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        stroke={
                          analysisResult.scores.overall >= 80 ? "#22c55e" :
                          analysisResult.scores.overall >= 60 ? "#f59e0b" :
                          "#ef4444"
                        }
                        strokeWidth="10"
                        fill="none"
                        strokeDasharray={`${Math.round(analysisResult.scores.overall * 2.51)} 251`}
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium mt-2">Overall Score</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <ScoreCard
                    title="Clarity"
                    score={analysisResult.scores.clarity}
                    icon={<BookOpen className="h-5 w-5" />}
                    description="How clear and understandable your message is"
                  />
                  <ScoreCard
                    title="Engagement"
                    score={analysisResult.scores.engagement}
                    icon={<Eye className="h-5 w-5" />}
                    description="Potential to capture and maintain attention"
                  />
                  <ScoreCard
                    title="Persuasion"
                    score={analysisResult.scores.persuasion}
                    icon={<Target className="h-5 w-5" />}
                    description="Effectiveness at driving desired actions"
                  />
                  <ScoreCard
                    title="Readability"
                    score={analysisResult.scores.readability}
                    icon={<BookOpen className="h-5 w-5" />}
                    description="Ease of reading for your audience"
                  />
                  <ScoreCard
                    title="Deliverability"
                    score={analysisResult.scores.deliverability}
                    icon={<ShieldCheck className="h-5 w-5" />}
                    description="Likelihood of reaching the inbox"
                  />
                  <ScoreCard
                    title="Accessibility"
                    score={analysisResult.scores.accessibility}
                    icon={<Maximize2 className="h-5 w-5" />}
                    description="Usability for all subscribers"
                  />
                </div>
              </TabsContent>

              <TabsContent value="issues" className="space-y-4">
                {analysisResult.issues.length > 0 ? (
                  <div className="space-y-3">
                    {analysisResult.issues.map((issue, index) => (
                      <div
                        key={index}
                        className={`p-4 rounded-lg border ${getIssueVariant(issue.type)}`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5">
                            {getIssueIcon(issue.type)}
                          </div>
                          <div className="space-y-1 flex-1">
                            <div className="flex items-center justify-between">
                              <h4 className="font-medium">{issue.message}</h4>
                              <Badge variant="outline" className="capitalize">
                                {issue.type}
                              </Badge>
                            </div>
                            <p className="text-sm">
                              {issue.details}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <ThumbsUp className="h-8 w-8 text-green-500 mx-auto mb-2" />
                    <p className="font-medium">No issues detected!</p>
                    <p className="text-sm text-muted-foreground">
                      Your email content looks great.
                    </p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="recommendations" className="space-y-4">
                <div className="space-y-3">
                  <h3 className="text-lg font-medium">Recommendations to Improve</h3>
                  <ul className="space-y-2">
                    {analysisResult.recommendations.map((recommendation, index) => (
                      <li key={index} className="flex items-start gap-2 p-3 border rounded-lg bg-muted/20">
                        <div className="mt-0.5">
                          <CornerRightDown className="h-4 w-4 text-primary" />
                        </div>
                        <span>{recommendation}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="pt-4">
                    <h3 className="text-lg font-medium mb-3">Resources</h3>
                    <ul className="space-y-2">
                      <li className="flex items-center gap-2">
                        <ExternalLink className="h-4 w-4 text-muted-foreground" />
                        <a href="#" className="text-sm text-primary hover:underline">
                          Guide: Writing high-converting email copy
                        </a>
                      </li>
                      <li className="flex items-center gap-2">
                        <ExternalLink className="h-4 w-4 text-muted-foreground" />
                        <a href="#" className="text-sm text-primary hover:underline">
                          Cheat sheet: Words and phrases that boost engagement
                        </a>
                      </li>
                      <li className="flex items-center gap-2">
                        <ExternalLink className="h-4 w-4 text-muted-foreground" />
                        <a href="#" className="text-sm text-primary hover:underline">
                          Template: High-performing email structures
                        </a>
                      </li>
                    </ul>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="benchmarks" className="space-y-6">
                <div className="space-y-4">
                  <div className="bg-muted/30 p-4 rounded-lg border">
                    <h3 className="text-lg font-medium mb-2">Industry Benchmarks - {analysisResult.benchmarks.industry}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm text-muted-foreground">Average Open Rate</p>
                          <span className="font-medium">{analysisResult.benchmarks.averageOpenRate}%</span>
                        </div>
                        <Progress value={analysisResult.benchmarks.averageOpenRate} className="h-2" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm text-muted-foreground">Average Click Rate</p>
                          <span className="font-medium">{analysisResult.benchmarks.averageClickRate}%</span>
                        </div>
                        <Progress value={analysisResult.benchmarks.averageClickRate * 5} className="h-2" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm text-muted-foreground">Readability Level</p>
                          <span className="font-medium">{analysisResult.benchmarks.readabilityLevel}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg border">
                    <h3 className="text-lg font-medium mb-3">Performance Prediction</h3>
                    <p className="text-sm mb-4">
                      Based on your content analysis, our AI predicts this email will perform:
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-3 rounded-lg bg-muted/20 border">
                        <p className="text-sm font-medium mb-1">Expected Open Rate</p>
                        <div className="flex items-center gap-2">
                          <Gauge className="h-5 w-5 text-primary" />
                          <span className="text-lg font-bold">
                            {Math.min(analysisResult.benchmarks.averageOpenRate * (analysisResult.scores.overall / 70), 40).toFixed(1)}%
                          </span>
                          <Badge variant="outline" className={
                            analysisResult.scores.overall >= 80 ? "text-green-600" :
                            analysisResult.scores.overall >= 60 ? "text-amber-600" :
                            "text-red-600"
                          }>
                            {analysisResult.scores.overall >= 80 ? "Above average" :
                             analysisResult.scores.overall >= 60 ? "Average" :
                             "Below average"}
                          </Badge>
                        </div>
                      </div>

                      <div className="p-3 rounded-lg bg-muted/20 border">
                        <p className="text-sm font-medium mb-1">Expected Click Rate</p>
                        <div className="flex items-center gap-2">
                          <Gauge className="h-5 w-5 text-primary" />
                          <span className="text-lg font-bold">
                            {Math.min(analysisResult.benchmarks.averageClickRate * (analysisResult.scores.overall / 70), 8).toFixed(1)}%
                          </span>
                          <Badge variant="outline" className={
                            analysisResult.scores.overall >= 80 ? "text-green-600" :
                            analysisResult.scores.overall >= 60 ? "text-amber-600" :
                            "text-red-600"
                          }>
                            {analysisResult.scores.overall >= 80 ? "Above average" :
                             analysisResult.scores.overall >= 60 ? "Average" :
                             "Below average"}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          )}

          {analysisResult && (
            <div className="flex justify-between pt-6 border-t mt-6">
              <Button
                variant="outline"
                onClick={() => setAnalysisResult(null)}
              >
                Reset
              </Button>
              <Button
                onClick={analyzeContent}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Reanalyzing...
                  </>
                ) : (
                  'Reanalyze'
                )}
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Helper component for score cards
function ScoreCard({
  title,
  score,
  icon,
  description
}: {
  title: string;
  score: number;
  icon: React.ReactNode;
  description: string;
}) {
  const { icon: scoreIcon, color } = getScoreIndicator(score);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="p-4 border rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {icon}
                <h3 className="font-medium">{title}</h3>
              </div>
              <div className="flex items-center gap-1">
                <span className={`font-bold ${color}`}>{score.toFixed(1)}</span>
                {scoreIcon}
              </div>
            </div>
            <Progress value={score} className="h-2" />
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p className="max-w-xs">{description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// Helper function
function getScoreIndicator(score: number) {
  if (score >= 80) {
    return { icon: <ThumbsUp className="h-4 w-4 text-green-500" />, color: 'text-green-500' };
  } else if (score >= 60) {
    return { icon: <AlertTriangle className="h-4 w-4 text-amber-500" />, color: 'text-amber-500' };
  } else {
    return { icon: <AlertTriangle className="h-4 w-4 text-red-500" />, color: 'text-red-500' };
  }
}
