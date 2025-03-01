import React, { useState, useEffect } from 'react'
import { Button, Spinner, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui'
import { LightBulbIcon, SparklesIcon, PaintBrushIcon, DocumentTextIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { motion, AnimatePresence } from 'framer-motion'
import { apiClient } from '@/lib/api'

interface Suggestion {
  id: string;
  type: 'content' | 'design';
  content: string;
  preview?: string;
  position?: [number, number];
  changes?: any[];
}

interface AiAssistantPanelProps {
  contentSuggestions: Suggestion[];
  designSuggestions: Suggestion[];
  isGenerating: boolean;
  onRequestSuggestion: () => void;
  onApplySuggestion: (suggestion: Suggestion) => void;
  campaignId: string;
}

/**
 * AI Assistant Panel for the Email Canvas
 * Provides content and design suggestions for email campaigns
 */
export const AiAssistantPanel: React.FC<AiAssistantPanelProps> = ({
  contentSuggestions,
  designSuggestions,
  isGenerating,
  onRequestSuggestion,
  onApplySuggestion,
  campaignId
}) => {
  const [activeTab, setActiveTab] = useState<string>('content')
  const [audience, setAudience] = useState<string>('')
  const [goal, setGoal] = useState<string>('')
  const [loadingMetadata, setLoadingMetadata] = useState<boolean>(false)

  // Load campaign metadata when panel is opened
  useEffect(() => {
    const loadCampaignMetadata = async () => {
      setLoadingMetadata(true)
      try {
        const response = await apiClient.get(`/api/campaigns/${campaignId}/metadata`)
        if (response.data?.data) {
          setAudience(response.data.data.audience || '')
          setGoal(response.data.data.goal || '')
        }
      } catch (error) {
        console.error('Failed to load campaign metadata:', error)
      } finally {
        setLoadingMetadata(false)
      }
    }

    loadCampaignMetadata()
  }, [campaignId])

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center">
          <LightBulbIcon className="h-5 w-5 text-primary mr-2" />
          <h3 className="font-medium">AI Assistant</h3>
        </div>
      </div>

      <div className="p-4 bg-muted/40 border-b">
        <h4 className="text-sm font-medium mb-2">Campaign Context</h4>
        {loadingMetadata ? (
          <div className="flex items-center justify-center py-4">
            <Spinner size="sm" />
            <span className="ml-2 text-sm text-muted-foreground">Loading metadata...</span>
          </div>
        ) : (
          <>
            <div className="mb-3">
              <label className="block text-xs text-muted-foreground mb-1">Target Audience</label>
              <input
                type="text"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
                className="w-full px-3 py-1 text-sm rounded-md border bg-background"
                placeholder="Describe your audience..."
              />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Campaign Goal</label>
              <input
                type="text"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                className="w-full px-3 py-1 text-sm rounded-md border bg-background"
                placeholder="What's your goal?"
              />
            </div>
          </>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="px-4 pt-4 bg-transparent justify-start border-b rounded-none gap-4">
          <TabsTrigger value="content" className="flex items-center">
            <DocumentTextIcon className="h-4 w-4 mr-1" />
            Content
          </TabsTrigger>
          <TabsTrigger value="design" className="flex items-center">
            <PaintBrushIcon className="h-4 w-4 mr-1" />
            Design
          </TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-auto">
          <TabsContent value="content" className="p-4 m-0 h-full">
            <div className="mb-4">
              <Button
                onClick={onRequestSuggestion}
                disabled={isGenerating}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Generating ideas...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="h-4 w-4 mr-2" />
                    Generate content ideas
                  </>
                )}
              </Button>
              <p className="text-xs text-muted-foreground mt-2">
                Generate content suggestions based on your canvas and campaign goal.
              </p>
            </div>

            <div className="space-y-3">
              <AnimatePresence>
                {contentSuggestions.length === 0 && !isGenerating ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="p-4 rounded-md border border-dashed flex flex-col items-center justify-center text-muted-foreground"
                  >
                    <DocumentTextIcon className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm text-center">No content suggestions yet. Generate some ideas!</p>
                  </motion.div>
                ) : (
                  contentSuggestions.map((suggestion) => (
                    <motion.div
                      key={suggestion.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="rounded-md border bg-card shadow-sm overflow-hidden"
                    >
                      <div className="p-3">
                        <p className="text-sm whitespace-pre-wrap">{suggestion.content}</p>
                      </div>
                      <div className="p-2 bg-muted/30 flex items-center justify-end border-t">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onApplySuggestion(suggestion)}
                        >
                          Apply to canvas
                        </Button>
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </TabsContent>

          <TabsContent value="design" className="p-4 m-0 h-full">
            <div className="mb-4">
              <Button
                onClick={onRequestSuggestion}
                disabled={isGenerating}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Analyzing design...
                  </>
                ) : (
                  <>
                    <PaintBrushIcon className="h-4 w-4 mr-2" />
                    Get design suggestions
                  </>
                )}
              </Button>
              <p className="text-xs text-muted-foreground mt-2">
                Get suggestions to improve your email design and layout.
              </p>
            </div>

            <div className="space-y-3">
              <AnimatePresence>
                {designSuggestions.length === 0 && !isGenerating ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="p-4 rounded-md border border-dashed flex flex-col items-center justify-center text-muted-foreground"
                  >
                    <PaintBrushIcon className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm text-center">No design suggestions yet. Get some ideas!</p>
                  </motion.div>
                ) : (
                  designSuggestions.map((suggestion) => (
                    <motion.div
                      key={suggestion.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="rounded-md border bg-card shadow-sm overflow-hidden"
                    >
                      {suggestion.preview && (
                        <div className="aspect-video overflow-hidden relative border-b">
                          <img
                            src={suggestion.preview}
                            alt="Design suggestion preview"
                            className="w-full h-full object-cover"
                          />
                        </div>
                      )}
                      <div className="p-3">
                        <p className="text-sm whitespace-pre-wrap">{suggestion.content}</p>
                      </div>
                      <div className="p-2 bg-muted/30 flex items-center justify-end border-t">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onApplySuggestion(suggestion)}
                        >
                          Apply changes
                        </Button>
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </TabsContent>
        </div>
      </Tabs>

      <div className="p-4 bg-muted/40 border-t text-xs text-muted-foreground">
        <p>AI suggestions are based on your canvas content and campaign information. Results may vary.</p>
      </div>
    </div>
  )
}
