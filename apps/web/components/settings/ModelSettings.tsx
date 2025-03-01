import React, { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2 } from 'lucide-react';

interface ModelOption {
  id: string;
  name: string;
  requiresApiKey: boolean;
  description: string;
}

interface AgentConfig {
  id: string;
  name: string;
  description: string;
  availableModels: ModelOption[];
  currentModelId: string;
  apiKey?: string;
}

const defaultAgents: AgentConfig[] = [
  {
    id: 'email-writer',
    name: 'Email Writer',
    description: 'AI agent that helps write and optimize email content',
    availableModels: [
      { id: 'default-model-1', name: 'Default Model 1', requiresApiKey: false, description: 'Standard model for email writing (No API Key Needed)' },
      { id: 'default-model-2', name: 'Default Model 2', requiresApiKey: false, description: 'Enhanced model for email writing (No API Key Needed)' },
      { id: 'openai-gpt4', name: 'OpenAI GPT-4', requiresApiKey: true, description: 'Premium model for advanced email writing (BYOK)' },
      { id: 'anthropic-claude', name: 'Anthropic Claude', requiresApiKey: true, description: 'Alternative premium model with different strengths (BYOK)' },
    ],
    currentModelId: 'default-model-1',
  },
  {
    id: 'subject-optimizer',
    name: 'Subject Line Optimizer',
    description: 'AI agent that optimizes email subject lines for better open rates',
    availableModels: [
      { id: 'default-model-1', name: 'Default Model 1', requiresApiKey: false, description: 'Standard model for subject optimization (No API Key Needed)' },
      { id: 'openai-gpt4', name: 'OpenAI GPT-4', requiresApiKey: true, description: 'Premium model for advanced subject optimization (BYOK)' },
      { id: 'anthropic-claude', name: 'Anthropic Claude', requiresApiKey: true, description: 'Alternative premium model with different strengths (BYOK)' },
    ],
    currentModelId: 'default-model-1',
  },
  {
    id: 'audience-segmenter',
    name: 'Audience Segmenter',
    description: 'AI agent that helps segment your audience for targeted campaigns',
    availableModels: [
      { id: 'default-model-1', name: 'Default Model 1', requiresApiKey: false, description: 'Standard model for audience segmentation (No API Key Needed)' },
      { id: 'openai-gpt4', name: 'OpenAI GPT-4', requiresApiKey: true, description: 'Premium model for advanced audience segmentation (BYOK)' },
    ],
    currentModelId: 'default-model-1',
  },
];

export default function ModelSettings() {
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('email-writer');
  const { toast } = useToast();

  // Fetch user's current settings
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        // In a real app, this would be an API call
        // const response = await fetch('/api/settings/models');
        // const data = await response.json();

        // For demo, we'll use the default settings with a delay to simulate API call
        setTimeout(() => {
          setAgents(defaultAgents);
          setLoading(false);
        }, 500);
      } catch (error) {
        console.error('Failed to fetch settings:', error);
        setAgents(defaultAgents);
        setLoading(false);
        toast({
          title: 'Error',
          description: 'Failed to load settings. Please try again.',
          variant: 'destructive',
        });
      }
    };

    fetchSettings();
  }, [toast]);

  const handleModelChange = (agentId: string, modelId: string) => {
    setAgents(prevAgents =>
      prevAgents.map(agent =>
        agent.id === agentId
          ? { ...agent, currentModelId: modelId }
          : agent
      )
    );
  };

  const handleApiKeyChange = (agentId: string, apiKey: string) => {
    setAgents(prevAgents =>
      prevAgents.map(agent =>
        agent.id === agentId
          ? { ...agent, apiKey }
          : agent
      )
    );
  };

  const validateApiKey = async (modelId: string, apiKey: string): Promise<boolean> => {
    // In a real app, this would validate the API key with the provider
    // For demo purposes, we'll just check if it's not empty and has a valid format

    if (!apiKey.trim()) return false;

    // Simple validation patterns (these would be more sophisticated in a real app)
    if (modelId === 'openai-gpt4' && !apiKey.startsWith('sk-')) {
      return false;
    }

    if (modelId === 'anthropic-claude' && !apiKey.startsWith('sk-ant-')) {
      return false;
    }

    return true;
  };

  const saveSettings = async () => {
    setSaving(true);

    try {
      // Validate API keys for models that require them
      for (const agent of agents) {
        const selectedModel = agent.availableModels.find(m => m.id === agent.currentModelId);

        if (selectedModel?.requiresApiKey) {
          const isValid = await validateApiKey(agent.currentModelId, agent.apiKey || '');

          if (!isValid) {
            toast({
              title: 'Invalid API Key',
              description: `Please provide a valid API key for ${selectedModel.name} in ${agent.name}.`,
              variant: 'destructive',
            });
            setSaving(false);
            return;
          }
        }
      }

      // In a real app, this would be an API call to save settings
      // await fetch('/api/settings/models', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ agents }),
      // });

      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      toast({
        title: 'Settings Saved',
        description: 'Your AI model preferences have been updated successfully.',
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast({
        title: 'Error',
        description: 'Failed to save settings. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2">Loading settings...</span>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">AI Model Settings</h1>
      <p className="text-muted-foreground mb-8">
        Configure which AI models to use for different features. Some premium models require your own API key (BYOK).
      </p>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-8">
          {agents.map(agent => (
            <TabsTrigger key={agent.id} value={agent.id}>
              {agent.name}
            </TabsTrigger>
          ))}
        </TabsList>

        {agents.map(agent => (
          <TabsContent key={agent.id} value={agent.id}>
            <Card>
              <CardHeader>
                <CardTitle>{agent.name}</CardTitle>
                <CardDescription>{agent.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor={`${agent.id}-model`}>Select AI Model</Label>
                  <Select
                    value={agent.currentModelId}
                    onValueChange={(value) => handleModelChange(agent.id, value)}
                  >
                    <SelectTrigger id={`${agent.id}-model`}>
                      <SelectValue placeholder="Select a model" />
                    </SelectTrigger>
                    <SelectContent>
                      {agent.availableModels.map(model => (
                        <SelectItem key={model.id} value={model.id}>
                          {model.name} {model.requiresApiKey ? '(BYOK)' : '(No API Key Needed)'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground mt-1">
                    {agent.availableModels.find(m => m.id === agent.currentModelId)?.description}
                  </p>
                </div>

                {agent.availableModels.find(m => m.id === agent.currentModelId)?.requiresApiKey && (
                  <div className="space-y-2">
                    <Label htmlFor={`${agent.id}-api-key`}>API Key</Label>
                    <Input
                      id={`${agent.id}-api-key`}
                      type="password"
                      placeholder="Enter your API key"
                      value={agent.apiKey || ''}
                      onChange={(e) => handleApiKeyChange(agent.id, e.target.value)}
                    />
                    <p className="text-sm text-muted-foreground">
                      Your API key is stored securely and never shared. We only use it to make requests to the AI provider on your behalf.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      <div className="mt-8 flex justify-end">
        <Button onClick={saveSettings} disabled={saving}>
          {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>
    </div>
  );
}
