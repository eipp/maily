'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Loader2,
  Wand2,
  LayoutTemplate,
  ExternalLink,
  Star
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import { aiService } from '@/lib/ai/ai-service';
import { getTemplates, Template } from '@/services/graphql-templates';
import Image from 'next/image';
import Link from 'next/link';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';

interface TemplateRecommenderProps {
  campaignName?: string;
  campaignSubject?: string;
  campaignContent?: string;
  campaignGoals?: string[];
  onSelectTemplate: (templateId: string) => void;
}

interface TemplateSuggestion {
  templateId: string;
  score: number;
  reason: string;
}

export function TemplateRecommender({
  campaignName = '',
  campaignSubject = '',
  campaignContent = '',
  campaignGoals = [],
  onSelectTemplate
}: TemplateRecommenderProps) {
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [recommendedTemplates, setRecommendedTemplates] = useState<(Template & {score: number, reason: string})[]>([]);

  // Fetch available templates
  useEffect(() => {
    async function fetchTemplates() {
      try {
        const result = await getTemplates(1, 20);
        setTemplates(result);
      } catch (error) {
        console.error('Error fetching templates:', error);
      }
    }

    fetchTemplates();
  }, []);

  // Generate template recommendations based on campaign details
  const generateRecommendations = async () => {
    if (!campaignSubject && !campaignContent && campaignGoals.length === 0) {
      toast({
        title: 'Insufficient information',
        description: 'Please add more details to your campaign for better recommendations.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    setAnalyzing(true);

    try {
      // Create a context string from available campaign information
      const context = [
        campaignName && `Campaign name: ${campaignName}`,
        campaignSubject && `Subject line: ${campaignSubject}`,
        campaignContent && `Content preview: ${campaignContent.substring(0, 200)}...`,
        campaignGoals.length > 0 && `Goals: ${campaignGoals.join(', ')}`
      ].filter(Boolean).join('\n');

      // In a real implementation, we would use the AI service to analyze the context
      // and provide recommendations based on template characteristics
      // For demonstration, we'll simulate this by getting random scores

      // Create a mock API response (in production this would come from aiService)
      const mockResponse = await new Promise<TemplateSuggestion[]>(resolve => {
        setTimeout(() => {
          const suggestions = templates.slice(0, 5).map(template => ({
            templateId: template.id,
            score: Math.random() * 100,
            reason: getRandomReason(template, campaignGoals)
          }));

          // Sort by score descending
          suggestions.sort((a, b) => b.score - a.score);

          resolve(suggestions);
        }, 1500);
      });

      // Match recommendation data with template details
      const enrichedRecommendations = mockResponse.map(rec => {
        const template = templates.find(t => t.id === rec.templateId);
        if (!template) return null;

        return {
          ...template,
          score: rec.score,
          reason: rec.reason
        };
      }).filter(Boolean) as (Template & {score: number, reason: string})[];

      setRecommendedTemplates(enrichedRecommendations);

      toast({
        title: 'Analysis complete',
        description: 'View recommended templates based on your campaign goals',
      });
    } catch (error) {
      console.error('Error generating template recommendations:', error);
      toast({
        title: 'Error',
        description: 'Failed to generate recommendations. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Helper function to generate random reasons for recommendations
  const getRandomReason = (template: Template, goals: string[]): string => {
    const reasons = [
      `Well suited for ${goals[0] || 'marketing'} campaigns`,
      `Has a design style that aligns with your campaign's tone`,
      `Proven high engagement rate with similar content`,
      `Layout optimized for the type of content in your campaign`,
      `Color scheme and typography match your brand's style`,
      `Mobile-responsive design ideal for your target audience`,
      `Call-to-action placement aligned with your campaign goals`
    ];

    return reasons[Math.floor(Math.random() * reasons.length)];
  };

  // Format score as percentage
  const formatScore = (score: number): string => {
    return `${Math.round(score)}%`;
  };

  // Handle template selection
  const handleSelectTemplate = (templateId: string) => {
    onSelectTemplate(templateId);
    toast({
      title: 'Template selected',
      description: 'The template has been applied to your campaign',
    });
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Wand2 className="h-4 w-4" />
          AI Recommendations
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LayoutTemplate className="h-5 w-5" />
            AI Template Recommendations
          </DialogTitle>
          <DialogDescription>
            Get AI-powered template suggestions based on your campaign goals
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {!analyzing ? (
            <div className="flex flex-col items-center gap-4">
              <p className="text-sm text-center text-muted-foreground max-w-md">
                Our AI will analyze your campaign details and recommend the best templates
                for your specific goals and content.
              </p>
              <Button
                onClick={generateRecommendations}
                className="gap-2"
                disabled={loading || templates.length === 0}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Wand2 className="h-4 w-4" />
                    Get Recommendations
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
                    Analyzing campaign details and finding the best templates...
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 gap-4">
                    {recommendedTemplates.length > 0 ? (
                      recommendedTemplates.map((template, index) => (
                        <div
                          key={template.id}
                          className={`flex flex-col md:flex-row gap-4 p-4 rounded-lg border ${
                            index === 0 ? "border-primary/50 bg-primary/5" : ""
                          }`}
                        >
                          <div className="relative w-full md:w-32 h-24 bg-muted rounded-md overflow-hidden">
                            {template.thumbnail ? (
                              <Image
                                src={template.thumbnail}
                                alt={template.name}
                                fill
                                className="object-cover"
                              />
                            ) : (
                              <div className="absolute inset-0 flex items-center justify-center bg-primary/10">
                                <LayoutTemplate className="h-6 w-6 text-primary/60" />
                              </div>
                            )}
                            {index === 0 && (
                              <div className="absolute top-1 left-1">
                                <Badge className="bg-amber-500 hover:bg-amber-600 flex items-center gap-1 text-xs">
                                  <Star className="h-3 w-3" />
                                  Best Match
                                </Badge>
                              </div>
                            )}
                          </div>

                          <div className="flex-1 space-y-2">
                            <div className="flex justify-between items-start">
                              <div>
                                <h3 className="font-medium">{template.name}</h3>
                                <p className="text-sm text-muted-foreground">{template.description}</p>
                              </div>
                              <Badge variant="outline" className="whitespace-nowrap">
                                Match: {formatScore(template.score)}
                              </Badge>
                            </div>

                            <p className="text-sm bg-muted/30 p-2 rounded-md">
                              <span className="font-medium">Why this works:</span> {template.reason}
                            </p>

                            <div className="flex justify-between gap-2 pt-1">
                              <Link
                                href={`/templates/${template.id}/preview`}
                                target="_blank"
                                className="text-sm flex items-center text-muted-foreground hover:text-primary"
                              >
                                <ExternalLink className="h-3.5 w-3.5 mr-1" />
                                Preview
                              </Link>

                              <Button
                                size="sm"
                                onClick={() => handleSelectTemplate(template.id)}
                              >
                                Apply Template
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-center text-muted-foreground py-6">
                        No recommendations available. Try adding more details to your campaign.
                      </p>
                    )}
                  </div>

                  <div className="flex justify-between pt-4">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setAnalyzing(false);
                        setRecommendedTemplates([]);
                      }}
                    >
                      Reset
                    </Button>
                    <Button
                      onClick={generateRecommendations}
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Reanalyzing...
                        </>
                      ) : (
                        'Regenerate'
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
