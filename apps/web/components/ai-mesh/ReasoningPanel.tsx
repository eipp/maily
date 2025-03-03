/**
 * ReasoningPanel Component
 * 
 * This component displays the reasoning process of an AI agent,
 * including thought steps, confidence scores, and references.
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Brain, X, ChevronDown, ChevronRight, ExternalLink, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Agent, ThoughtProcess, Reference } from '@/types/ai-mesh';

// Define the props
export interface ReasoningPanelProps {
  agent: Agent;
  onClose: () => void;
}

/**
 * ReasoningPanel component
 * 
 * @param props Component props
 * @returns ReasoningPanel component
 */
export const ReasoningPanel: React.FC<ReasoningPanelProps> = ({
  agent,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<string>('thoughts');
  const [expandedThoughts, setExpandedThoughts] = useState<Set<string>>(new Set());
  
  // Toggle thought expansion
  const toggleThought = (thoughtId: string) => {
    const newExpandedThoughts = new Set(expandedThoughts);
    
    if (newExpandedThoughts.has(thoughtId)) {
      newExpandedThoughts.delete(thoughtId);
    } else {
      newExpandedThoughts.add(thoughtId);
    }
    
    setExpandedThoughts(newExpandedThoughts);
  };
  
  // Format confidence as percentage
  const formatConfidence = (confidence: number): string => {
    return `${(confidence * 100).toFixed(0)}%`;
  };
  
  // Get confidence color based on value
  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.5) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  return (
    <Card className="m-2 shadow-lg">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Brain className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">{agent.name}</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>
          <div className="flex items-center space-x-2">
            <span>Confidence:</span>
            <Progress
              value={agent.confidence * 100}
              className="h-2 w-24"
              indicatorClassName={getConfidenceColor(agent.confidence)}
            />
            <span className="text-sm font-medium">
              {formatConfidence(agent.confidence)}
            </span>
          </div>
        </CardDescription>
      </CardHeader>
      
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="w-full"
      >
        <div className="px-4">
          <TabsList className="w-full">
            <TabsTrigger value="thoughts" className="flex-1">
              Thoughts
            </TabsTrigger>
            <TabsTrigger value="references" className="flex-1">
              References
            </TabsTrigger>
            <TabsTrigger value="specializations" className="flex-1">
              Specializations
            </TabsTrigger>
          </TabsList>
        </div>
        
        {/* Thoughts tab */}
        <TabsContent value="thoughts" className="m-0">
          <ScrollArea className="h-[300px] px-4">
            {agent.thoughtProcess && agent.thoughtProcess.length > 0 ? (
              <div className="space-y-2 py-2">
                {agent.thoughtProcess.map((thought, index) => (
                  <Collapsible
                    key={thought.id}
                    open={expandedThoughts.has(thought.id)}
                    onOpenChange={() => toggleThought(thought.id)}
                    className="border rounded-md"
                  >
                    <div className="flex items-center p-2">
                      <CollapsibleTrigger asChild>
                        <Button variant="ghost" size="sm" className="p-1 h-auto">
                          {expandedThoughts.has(thought.id) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </Button>
                      </CollapsibleTrigger>
                      
                      <div className="flex-1 flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs">
                          Step {index + 1}
                        </Badge>
                        <span className="font-medium text-sm truncate">
                          {thought.summary}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <Badge
                          className={`text-xs ${
                            thought.confidence >= 0.8
                              ? 'bg-green-100 text-green-800'
                              : thought.confidence >= 0.5
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {formatConfidence(thought.confidence)}
                        </Badge>
                      </div>
                    </div>
                    
                    <CollapsibleContent className="p-2 pt-0 border-t">
                      <div className="text-sm whitespace-pre-wrap">
                        {thought.content}
                      </div>
                      
                      {thought.references && thought.references.length > 0 && (
                        <div className="mt-2">
                          <h4 className="text-xs font-semibold text-muted-foreground mb-1">
                            References:
                          </h4>
                          <ul className="text-xs space-y-1">
                            {thought.references.map((reference) => (
                              <li key={reference.id} className="flex items-center">
                                <ExternalLink className="h-3 w-3 mr-1 text-muted-foreground" />
                                <a
                                  href={reference.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary hover:underline truncate"
                                >
                                  {reference.title}
                                </a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CollapsibleContent>
                  </Collapsible>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-muted-foreground">
                  No thought process available
                </p>
              </div>
            )}
          </ScrollArea>
        </TabsContent>
        
        {/* References tab */}
        <TabsContent value="references" className="m-0">
          <ScrollArea className="h-[300px] px-4">
            {agent.references && agent.references.length > 0 ? (
              <div className="space-y-2 py-2">
                {agent.references.map((reference) => (
                  <Card key={reference.id} className="p-3">
                    <div className="flex items-start space-x-3">
                      <div className="flex-1">
                        <h3 className="text-sm font-medium">
                          <a
                            href={reference.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline flex items-center"
                          >
                            {reference.title}
                            <ExternalLink className="h-3 w-3 ml-1" />
                          </a>
                        </h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          {reference.description}
                        </p>
                      </div>
                      <Badge
                        className={`text-xs ${
                          reference.relevance >= 0.8
                            ? 'bg-green-100 text-green-800'
                            : reference.relevance >= 0.5
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {formatConfidence(reference.relevance)}
                      </Badge>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-muted-foreground">
                  No references available
                </p>
              </div>
            )}
          </ScrollArea>
        </TabsContent>
        
        {/* Specializations tab */}
        <TabsContent value="specializations" className="m-0">
          <ScrollArea className="h-[300px] px-4">
            <div className="space-y-4 py-4">
              {agent.specializations.map((specialization) => (
                <div key={specialization} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium">{specialization}</h3>
                    <Badge
                      className={`text-xs ${
                        agent.specializationScores?.[specialization] >= 0.8
                          ? 'bg-green-100 text-green-800'
                          : agent.specializationScores?.[specialization] >= 0.5
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {formatConfidence(agent.specializationScores?.[specialization] || 0)}
                    </Badge>
                  </div>
                  <Progress
                    value={(agent.specializationScores?.[specialization] || 0) * 100}
                    className="h-2"
                    indicatorClassName={getConfidenceColor(
                      agent.specializationScores?.[specialization] || 0
                    )}
                  />
                </div>
              ))}
              
              {agent.specializations.length === 0 && (
                <div className="flex items-center justify-center h-full">
                  <p className="text-muted-foreground">
                    No specializations available
                  </p>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
      
      <CardFooter className="flex justify-between pt-2 pb-3">
        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
          <span>Agent ID:</span>
          <code className="bg-muted px-1 rounded text-xs">{agent.id.substring(0, 8)}</code>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            className="h-8 w-8 p-0"
            title="Helpful"
          >
            <ThumbsUp className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8 w-8 p-0"
            title="Not helpful"
          >
            <ThumbsDown className="h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default ReasoningPanel;
