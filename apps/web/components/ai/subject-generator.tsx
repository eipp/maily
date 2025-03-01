'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, Wand2 } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import { aiService } from '@/lib/ai/ai-service';

interface SubjectGeneratorProps {
  campaignName?: string;
  productName?: string;
  campaignType?: string;
  onSelectSubject: (subject: string) => void;
}

export function SubjectGenerator({
  campaignName = '',
  productName = '',
  campaignType = 'marketing',
  onSelectSubject
}: SubjectGeneratorProps) {
  const [loading, setLoading] = useState(false);
  const [generatedSubjects, setGeneratedSubjects] = useState<string[]>([]);
  const [prompt, setPrompt] = useState('');

  // Generate subject lines based on provided context
  const generateSubjects = async () => {
    setLoading(true);

    try {
      // Build context from available information
      const context = [
        campaignName && `Campaign name: ${campaignName}`,
        productName && `Product name: ${productName}`,
        campaignType && `Campaign type: ${campaignType}`,
        prompt && `Additional context: ${prompt}`
      ].filter(Boolean).join(', ');

      // Generate 3 subject line variations
      const results = await aiService.generateSubjectLineVariations(
        context || 'Marketing email',
        3
      );

      setGeneratedSubjects(results);

      toast({
        title: 'Success',
        description: 'Generated new subject line options',
      });
    } catch (error) {
      console.error('Error generating subject lines:', error);
      toast({
        title: 'Error',
        description: 'Failed to generate subject lines. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle selection of a subject line
  const handleSelectSubject = (subject: string) => {
    onSelectSubject(subject);
    toast({
      title: 'Subject line selected',
      description: 'The subject line has been applied to your campaign',
    });
  };

  return (
    <div className="bg-muted/30 rounded-lg p-4 space-y-4 border">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Wand2 className="h-4 w-4" />
            AI Subject Generator
          </h3>
          <p className="text-sm text-muted-foreground">
            Get AI-powered subject line suggestions for your campaign
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="prompt">Additional context (optional)</Label>
        <div className="flex gap-2">
          <Input
            id="prompt"
            placeholder="E.g. Spring sale, 20% discount, urgency"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={loading}
          />
          <Button
            onClick={generateSubjects}
            disabled={loading}
            variant="secondary"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              'Generate'
            )}
          </Button>
        </div>
      </div>

      {generatedSubjects.length > 0 && (
        <div className="space-y-3">
          <Label>Subject line suggestions</Label>
          <ul className="space-y-2">
            {generatedSubjects.map((subject, index) => (
              <li key={index} className="flex items-center justify-between p-2 bg-background rounded border hover:border-primary transition-colors">
                <span className="text-sm">{subject}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleSelectSubject(subject)}
                >
                  Use
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
