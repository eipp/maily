'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Loader2,
  Wand2,
  BarChart,
  CheckCircle,
  AlertTriangle,
  XCircle
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
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface ContentOptimizerProps {
  content: string;
  onApplySuggestion: (newContent: string) => void;
}

type OptimizationScore = 'good' | 'warning' | 'poor';
type SuggestionCategory = 'engagement' | 'clarity' | 'personalization' | 'cta' | 'length';

interface Suggestion {
  category: SuggestionCategory;
  title: string;
  description: string;
  suggestedContent?: string;
  score: OptimizationScore;
}

export function ContentOptimizer({
  content,
  onApplySuggestion
}: ContentOptimizerProps) {
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [overallScore, setOverallScore] = useState<OptimizationScore | null>(null);

  // Analyze email content and provide suggestions
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
    setIsAnalyzing(true);

    try {
      // Call AI service to optimize the content
      const optimizationResult = await aiService.optimizeEmailContent(content);

      // For demonstration purposes, we'll create a simulated response format
      // In production, the AI service should return properly structured data

      // Parse the optimization results
      const parsedSuggestions: Suggestion[] = [];

      // Process suggestions from optimization result
      // This is a simplified example - in real implementation,
      // the AI service should return structured data
      if (typeof optimizationResult === 'string') {
        // Attempt to extract structured data from text response
        const engagementMatch = optimizationResult.match(/Engagement:(.*?)(?=Clarity:|$)/s);
        if (engagementMatch) {
          parsedSuggestions.push({
            category: 'engagement',
            title: 'Improve engagement',
            description: engagementMatch[1].trim(),
            score: optimizationResult.includes('good engagement') ? 'good' : 'warning'
          });
        }

        const clarityMatch = optimizationResult.match(/Clarity:(.*?)(?=Personalization:|$)/s);
        if (clarityMatch) {
          parsedSuggestions.push({
            category: 'clarity',
            title: 'Enhance clarity',
            description: clarityMatch[1].trim(),
            score: optimizationResult.includes('clear message') ? 'good' : 'warning'
          });
        }

        const personalizationMatch = optimizationResult.match(/Personalization:(.*?)(?=CTA:|$)/s);
        if (personalizationMatch) {
          parsedSuggestions.push({
            category: 'personalization',
            title: 'Add personalization',
            description: personalizationMatch[1].trim(),
            score: optimizationResult.includes('well personalized') ? 'good' : 'warning'
          });
        }

        const ctaMatch = optimizationResult.match(/CTA:(.*?)(?=Length:|$)/s);
        if (ctaMatch) {
          parsedSuggestions.push({
            category: 'cta',
            title: 'Strengthen call-to-action',
            description: ctaMatch[1].trim(),
            score: optimizationResult.includes('strong CTA') ? 'good' : 'warning'
          });
        }

        const lengthMatch = optimizationResult.match(/Length:(.*?)(?=$)/s);
        if (lengthMatch) {
          parsedSuggestions.push({
            category: 'length',
            title: 'Optimize length',
            description: lengthMatch[1].trim(),
            score: optimizationResult.includes('appropriate length') ? 'good' : 'warning'
          });
        }
      }

      // If we couldn't parse structured data, provide a fallback
      if (parsedSuggestions.length === 0) {
        parsedSuggestions.push({
          category: 'engagement',
          title: 'General optimization',
          description: typeof optimizationResult === 'string'
            ? optimizationResult
            : 'Consider reviewing your email for clarity, engagement, and a strong call-to-action.',
          score: 'warning'
        });
      }

      setSuggestions(parsedSuggestions);

      // Calculate overall score based on individual scores
      const scores = parsedSuggestions.map(s => s.score);
      if (scores.every(s => s === 'good')) {
        setOverallScore('good');
      } else if (scores.some(s => s === 'poor')) {
        setOverallScore('poor');
      } else {
        setOverallScore('warning');
      }

      toast({
        title: 'Analysis complete',
        description: 'Review the suggestions to improve your email content',
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

  // Apply the suggested content from a specific suggestion
  const applySuggestion = (suggestedContent: string) => {
    onApplySuggestion(suggestedContent);
    toast({
      title: 'Suggestion applied',
      description: 'The content has been updated with the suggestion',
    });
  };

  // Get icon for score
  const getScoreIcon = (score: OptimizationScore) => {
    switch (score) {
      case 'good':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'poor':
        return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2" disabled={!content || content.trim().length < 20}>
          <Wand2 className="h-4 w-4" />
          Optimize Content
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wand2 className="h-5 w-5" />
            AI Content Optimization
          </DialogTitle>
          <DialogDescription>
            Get AI-powered suggestions to improve your email content
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {!isAnalyzing ? (
            <div className="flex justify-center">
              <Button
                onClick={analyzeContent}
                className="gap-2"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <BarChart className="h-4 w-4" />
                    Analyze Content
                  </>
                )}
              </Button>
            </div>
          ) : (
            <>
              {loading ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                  <p className="text-center text-muted-foreground">
                    Analyzing your email content...
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {overallScore && (
                    <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border">
                      <div className="flex items-center gap-2">
                        <BarChart className="h-5 w-5 text-primary" />
                        <span className="font-medium">Overall Assessment</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {getScoreIcon(overallScore)}
                        <span className="capitalize">{overallScore}</span>
                      </div>
                    </div>
                  )}

                  {suggestions.length > 0 ? (
                    <Accordion type="single" collapsible className="space-y-2">
                      {suggestions.map((suggestion, index) => (
                        <AccordionItem key={index} value={`item-${index}`} className="border rounded-lg">
                          <AccordionTrigger className="px-4 hover:no-underline hover:bg-muted/20">
                            <div className="flex items-center justify-between w-full pr-4">
                              <span className="flex items-center gap-2">
                                {getScoreIcon(suggestion.score)}
                                {suggestion.title}
                              </span>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent className="px-4 pb-4 pt-2">
                            <div className="space-y-3">
                              <p className="text-sm">{suggestion.description}</p>
                              {suggestion.suggestedContent && (
                                <div className="pt-2">
                                  <Label className="mb-2 block">Suggested content:</Label>
                                  <div className="bg-muted/20 p-3 rounded-md text-sm mb-2 border">
                                    {suggestion.suggestedContent}
                                  </div>
                                  <Button
                                    size="sm"
                                    onClick={() => applySuggestion(suggestion.suggestedContent!)}
                                  >
                                    Apply Suggestion
                                  </Button>
                                </div>
                              )}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  ) : (
                    <p className="text-center text-muted-foreground">
                      No suggestions to display. Try analyzing your content again.
                    </p>
                  )}

                  <div className="flex justify-between pt-4">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setIsAnalyzing(false);
                        setSuggestions([]);
                        setOverallScore(null);
                      }}
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
                </div>
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
