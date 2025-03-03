"use client"

import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { 
  Send, Paperclip, Sparkles, Bot, User, 
  ChevronDown, ChevronUp, MoreVertical, 
  Trash, Copy, Bookmark, Share, Download
} from 'lucide-react';

// Types
interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  attachments?: {
    id: string;
    name: string;
    type: string;
    url: string;
  }[];
  isCode?: boolean;
}

interface ChatInterfaceProps {
  className?: string;
  messages?: Message[];
  activeAgent?: {
    name: string;
    color: string;
  };
  onSendMessage?: (message: string, attachments?: File[]) => void;
  onClearChat?: () => void;
}

export function ChatInterface({
  className,
  messages = [],
  activeAgent = { name: 'Content Assistant', color: 'rgb(239, 68, 68)' },
  onSendMessage,
  onClearChat,
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Default messages if none provided
  const defaultMessages: Message[] = [
    {
      id: '1',
      content: `Hi there! I'm your ${activeAgent.name}. How can I help you today?`,
      sender: 'agent',
      timestamp: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
    },
    {
      id: '2',
      content: 'I need help creating an email campaign for our new product launch.',
      sender: 'user',
      timestamp: new Date(Date.now() - 55 * 60 * 1000), // 55 minutes ago
    },
    {
      id: '3',
      content: 'I can definitely help with that! What kind of product are you launching, and who is your target audience?',
      sender: 'agent',
      timestamp: new Date(Date.now() - 54 * 60 * 1000), // 54 minutes ago
    },
    {
      id: '4',
      content: "It's a new fitness tracker with advanced sleep monitoring. Target audience is health-conscious professionals aged 25-45.",
      sender: 'user',
      timestamp: new Date(Date.now() - 50 * 60 * 1000), // 50 minutes ago
    },
    {
      id: '5',
      content: `Great! Here's a code example for a responsive email template you could use:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>New Fitness Tracker Launch</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
    <tr>
      <td style="padding: 20px 0; text-align: center; background-color: #f8f9fa;">
        <img src="logo.png" alt="Company Logo" width="200">
      </td>
    </tr>
    <tr>
      <td style="padding: 20px; background-color: #ffffff;">
        <h1 style="color: #333333; margin-top: 0;">Introducing SleepTrack Pro</h1>
        <p>The fitness tracker that changes everything about how you sleep.</p>
      </td>
    </tr>
  </table>
</body>
</html>
\`\`\``,
      sender: 'agent',
      timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
      isCode: true,
    },
  ];
  
  const displayMessages = messages.length > 0 ? messages : defaultMessages;
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [displayMessages]);
  
  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };
  
  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachments(prev => [...prev, ...Array.from(e.target.files!)]);
    }
  };
  
  // Handle file button click
  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };
  
  // Handle remove attachment
  const handleRemoveAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };
  
  // Handle send message
  const handleSendMessage = () => {
    if (inputValue.trim() || attachments.length > 0) {
      onSendMessage?.(inputValue, attachments);
      setInputValue('');
      setAttachments([]);
      setIsTyping(true);
      
      // Simulate agent typing
      setTimeout(() => {
        setIsTyping(false);
      }, 2000);
    }
  };
  
  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Format timestamp
  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Toggle options menu
  const toggleOptions = () => {
    setShowOptions(!showOptions);
  };
  
  // Handle clear chat
  const handleClearChat = () => {
    onClearChat?.();
    setShowOptions(false);
  };

  return (
    <div className={cn("flex flex-col h-full bg-card border border-border rounded-lg overflow-hidden", className)}>
      {/* Header */}
      <div 
        className="px-4 py-3 border-b border-border flex items-center justify-between"
        style={{ backgroundColor: `${activeAgent.color}10` }}
      >
        <div className="flex items-center">
          <div 
            className="w-8 h-8 rounded-full flex items-center justify-center mr-3 text-white"
            style={{ backgroundColor: activeAgent.color }}
          >
            <Bot className="w-4 h-4" />
          </div>
          <h2 className="font-medium text-sm">{activeAgent.name}</h2>
        </div>
        
        <div className="relative">
          <button 
            className="p-1 rounded hover:bg-muted"
            onClick={toggleOptions}
          >
            <MoreVertical className="w-4 h-4" />
          </button>
          
          {showOptions && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-card border border-border rounded-md shadow-md z-10">
              <ul className="py-1">
                <li>
                  <button 
                    className="w-full px-4 py-2 text-sm text-left flex items-center hover:bg-muted"
                    onClick={handleClearChat}
                  >
                    <Trash className="w-4 h-4 mr-2" />
                    Clear conversation
                  </button>
                </li>
                <li>
                  <button className="w-full px-4 py-2 text-sm text-left flex items-center hover:bg-muted">
                    <Copy className="w-4 h-4 mr-2" />
                    Copy conversation
                  </button>
                </li>
                <li>
                  <button className="w-full px-4 py-2 text-sm text-left flex items-center hover:bg-muted">
                    <Bookmark className="w-4 h-4 mr-2" />
                    Save conversation
                  </button>
                </li>
                <li>
                  <button className="w-full px-4 py-2 text-sm text-left flex items-center hover:bg-muted">
                    <Download className="w-4 h-4 mr-2" />
                    Export as PDF
                  </button>
                </li>
              </ul>
            </div>
          )}
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {displayMessages.map((message) => (
          <div 
            key={message.id}
            className={cn(
              "flex",
              message.sender === 'user' ? "justify-end" : "justify-start"
            )}
          >
            <div 
              className={cn(
                "max-w-[80%] rounded-lg p-3",
                message.sender === 'user' 
                  ? "bg-primary text-primary-foreground rounded-tr-none" 
                  : "bg-muted rounded-tl-none"
              )}
            >
              {message.isCode ? (
                <div className="text-sm">
                  <div className="mb-1">{message.content.split('```')[0]}</div>
                  <pre className="bg-black/10 p-3 rounded overflow-x-auto text-xs">
                    <code>{message.content.split('```')[1].split('```')[0].replace(/^html\n/, '')}</code>
                  </pre>
                </div>
              ) : (
                <div className="text-sm">{message.content}</div>
              )}
              
              {message.attachments && message.attachments.length > 0 && (
                <div className="mt-2 space-y-1">
                  {message.attachments.map(attachment => (
                    <div 
                      key={attachment.id}
                      className="text-xs bg-black/5 rounded p-1 flex items-center"
                    >
                      <Paperclip className="w-3 h-3 mr-1" />
                      <span>{attachment.name}</span>
                    </div>
                  ))}
                </div>
              )}
              
              <div className="mt-1 text-xs opacity-70 text-right">
                {formatTimestamp(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg rounded-tl-none p-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <div className="p-4 border-t border-border">
        {attachments.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {attachments.map((file, index) => (
              <div 
                key={index}
                className="bg-muted text-xs rounded-full px-3 py-1 flex items-center"
              >
                <Paperclip className="w-3 h-3 mr-1" />
                <span className="truncate max-w-[100px]">{file.name}</span>
                <button 
                  className="ml-1 text-muted-foreground hover:text-foreground"
                  onClick={() => handleRemoveAttachment(index)}
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        )}
        
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              className="w-full border border-border rounded-lg px-3 py-2 min-h-[80px] max-h-[200px] resize-none focus:outline-none focus:ring-1 focus:ring-primary"
              placeholder="Type your message..."
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyPress}
            />
            
            <button 
              className="absolute right-2 bottom-2 p-1 rounded-full bg-muted hover:bg-muted/80"
              onClick={handleFileButtonClick}
            >
              <Paperclip className="w-4 h-4" />
            </button>
            
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              multiple 
              onChange={handleFileSelect}
            />
          </div>
          
          <button 
            className="p-3 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 flex-none"
            onClick={handleSendMessage}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        
        <div className="mt-2 flex justify-center">
          <button className="text-xs text-muted-foreground hover:text-foreground flex items-center">
            <Sparkles className="w-3 h-3 mr-1" />
            Generate with AI
          </button>
        </div>
      </div>
    </div>
  );
}
