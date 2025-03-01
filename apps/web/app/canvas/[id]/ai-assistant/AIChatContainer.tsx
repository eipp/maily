'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Bot, Send, Loader2, Brain, User, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  thoughtId?: string;
}

interface AIChatContainerProps {
  canvasId: string;
}

export default function AIChatContainer({ canvasId }: AIChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsProcessing(true);

    try {
      // Call the AI orchestrator API
      const response = await fetch(`/api/v1/canvas/ai/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: input,
          canvas_id: canvasId,
          visualization: true
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }

      const data = await response.json();

      // Add AI response to chat
      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        thoughtId: data.thought_id
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error getting AI response:', error);
      toast.error('Failed to get AI response. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain size={20} />
          AI Assistant
        </CardTitle>
        <CardDescription>
          Ask questions about your canvas and get intelligent assistance
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-grow overflow-y-auto pb-0">
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Bot size={40} className="mx-auto mb-4 opacity-50" />
              <p>No messages yet. Start a conversation with the AI assistant.</p>
              <div className="mt-4 space-y-2">
                <Badge className="cursor-pointer" onClick={() => setInput("What are the main elements on this canvas?")}>
                  What are the main elements on this canvas?
                </Badge>
                <Badge className="cursor-pointer" onClick={() => setInput("Can you help me improve this design?")}>
                  Can you help me improve this design?
                </Badge>
                <Badge className="cursor-pointer" onClick={() => setInput("Explain how these components connect together")}>
                  Explain how these components connect
                </Badge>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`flex gap-3 ${message.role === 'assistant' ? 'items-start' : 'items-start justify-end'}`}>
                {message.role === 'assistant' && (
                  <Avatar>
                    <AvatarFallback>AI</AvatarFallback>
                    <AvatarImage src="/ai-avatar.png" />
                  </Avatar>
                )}

                <div className={`px-4 py-2 rounded-lg max-w-[80%] ${
                  message.role === 'assistant'
                    ? 'bg-secondary text-secondary-foreground'
                    : 'bg-primary text-primary-foreground'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <div className="text-xs opacity-70 mt-1 text-right">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>

                {message.role === 'user' && (
                  <Avatar>
                    <AvatarFallback>You</AvatarFallback>
                    <AvatarImage src="/user-avatar.png" />
                  </Avatar>
                )}
              </div>
            ))
          )}

          {isProcessing && (
            <div className="flex gap-3 items-start">
              <Avatar>
                <AvatarFallback>AI</AvatarFallback>
                <AvatarImage src="/ai-avatar.png" />
              </Avatar>

              <div className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground">
                <div className="flex items-center gap-2">
                  <Loader2 size={16} className="animate-spin" />
                  <p>Thinking...</p>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </CardContent>

      <CardFooter className="pt-4">
        <form
          className="flex w-full gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
        >
          <Textarea
            placeholder="Ask the AI assistant..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-grow min-h-[80px]"
            disabled={isProcessing}
          />
          <Button
            type="submit"
            size="icon"
            disabled={isProcessing || !input.trim()}
            className="h-auto"
          >
            <Send size={18} />
          </Button>
        </form>
      </CardFooter>
    </Card>
  );
}
