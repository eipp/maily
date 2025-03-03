"use client"

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  Bell, Settings, User, ChevronDown, 
  Save, Download, Share, MoreHorizontal,
  Edit, Mail, BarChart, Users, 
  CheckCircle, Clock, AlertTriangle
} from 'lucide-react';
import { OperationalMode } from '@/components/modes/ModeController';

// Types
interface CampaignInfo {
  id: string;
  name: string;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'archived';
}

interface ActiveUser {
  id: string;
  name: string;
  status: 'online' | 'away' | 'offline';
  avatar?: string;
}

interface TopNavigationProps {
  className?: string;
  campaignInfo?: CampaignInfo;
  activeUsers?: ActiveUser[];
  activeMode?: OperationalMode;
  onModeChange?: () => void;
  hasUnsavedChanges?: boolean;
  notifications?: number;
}

export function TopNavigation({
  className,
  campaignInfo = { id: 'camp-123', name: 'Untitled Campaign', status: 'draft' },
  activeUsers = [],
  activeMode = 'content',
  onModeChange,
  hasUnsavedChanges = false,
  notifications = 0,
}: TopNavigationProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [campaignName, setCampaignName] = useState(campaignInfo.name);
  
  // Mode icons and colors
  const modeConfig: Record<OperationalMode, { icon: React.ReactNode; color: string; label: string }> = {
    content: { 
      icon: <Edit className="w-4 h-4" />, 
      color: 'text-blue-600',
      label: 'Content',
    },
    campaign: { 
      icon: <Mail className="w-4 h-4" />, 
      color: 'text-purple-600',
      label: 'Campaign',
    },
    analytics: { 
      icon: <BarChart className="w-4 h-4" />, 
      color: 'text-green-600',
      label: 'Analytics',
    },
    audience: { 
      icon: <Users className="w-4 h-4" />, 
      color: 'text-orange-600',
      label: 'Audience',
    },
  };
  
  // Status icons and colors
  const statusConfig: Record<CampaignInfo['status'], { icon: React.ReactNode; color: string; label: string }> = {
    draft: { 
      icon: <Edit className="w-4 h-4" />, 
      color: 'text-gray-500',
      label: 'Draft',
    },
    scheduled: { 
      icon: <Clock className="w-4 h-4" />, 
      color: 'text-blue-500',
      label: 'Scheduled',
    },
    sending: { 
      icon: <Mail className="w-4 h-4" />, 
      color: 'text-yellow-500',
      label: 'Sending',
    },
    sent: { 
      icon: <CheckCircle className="w-4 h-4" />, 
      color: 'text-green-500',
      label: 'Sent',
    },
    archived: { 
      icon: <AlertTriangle className="w-4 h-4" />, 
      color: 'text-red-500',
      label: 'Archived',
    },
  };
  
  // Toggle user menu
  const toggleUserMenu = () => {
    setShowUserMenu(!showUserMenu);
  };
  
  // Toggle notifications
  const toggleNotifications = () => {
    setShowNotifications(!showNotifications);
  };
  
  // Handle campaign name edit
  const handleNameEdit = () => {
    setIsEditingName(true);
  };
  
  // Handle campaign name change
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCampaignName(e.target.value);
  };
  
  // Handle campaign name save
  const handleNameSave = () => {
    setIsEditingName(false);
    // In a real app, this would save the name to the server
  };
  
  // Handle key press for campaign name
  const handleNameKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleNameSave();
    }
  };

  return (
    <div className={cn("h-14 px-4 flex items-center justify-between", className)}>
      {/* Left Section - Campaign Info */}
      <div className="flex items-center">
        {isEditingName ? (
          <div className="flex items-center">
            <input
              type="text"
              className="border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              value={campaignName}
              onChange={handleNameChange}
              onKeyDown={handleNameKeyPress}
              onBlur={handleNameSave}
              autoFocus
            />
          </div>
        ) : (
          <div className="flex items-center cursor-pointer" onClick={handleNameEdit}>
            <h1 className="font-medium text-lg mr-2">{campaignName}</h1>
            <Edit className="w-3.5 h-3.5 text-muted-foreground" />
          </div>
        )}
        
        <div className={cn("ml-3 px-2 py-0.5 rounded-full text-xs flex items-center", statusConfig[campaignInfo.status].color)}>
          {statusConfig[campaignInfo.status].icon}
          <span className="ml-1">{statusConfig[campaignInfo.status].label}</span>
        </div>
        
        {hasUnsavedChanges && (
          <div className="ml-3 text-xs text-muted-foreground">
            Unsaved changes
          </div>
        )}
      </div>
      
      {/* Center Section - Mode Selector */}
      <div className="absolute left-1/2 transform -translate-x-1/2">
        <div 
          className="flex items-center bg-muted/30 rounded-lg p-1 cursor-pointer"
          onClick={onModeChange}
        >
          <div className={cn(
            "flex items-center px-3 py-1.5 rounded-md",
            `bg-${activeMode === 'content' ? 'blue' : 
                  activeMode === 'campaign' ? 'purple' : 
                  activeMode === 'analytics' ? 'green' : 
                  'orange'}-50`,
            modeConfig[activeMode].color
          )}>
            {modeConfig[activeMode].icon}
            <span className="ml-1.5 text-sm font-medium">{modeConfig[activeMode].label}</span>
            <ChevronDown className="w-4 h-4 ml-1" />
          </div>
        </div>
      </div>
      
      {/* Right Section - Actions & User */}
      <div className="flex items-center space-x-2">
        {/* Action Buttons */}
        <button className="p-2 rounded hover:bg-muted">
          <Save className="w-4 h-4" />
        </button>
        
        <button className="p-2 rounded hover:bg-muted">
          <Download className="w-4 h-4" />
        </button>
        
        <button className="p-2 rounded hover:bg-muted">
          <Share className="w-4 h-4" />
        </button>
        
        <button className="p-2 rounded hover:bg-muted">
          <MoreHorizontal className="w-4 h-4" />
        </button>
        
        <div className="h-6 w-px bg-border mx-1" />
        
        {/* Active Users */}
        {activeUsers.length > 0 && (
          <div className="flex -space-x-2 mr-2">
            {activeUsers.slice(0, 3).map(user => (
              <div 
                key={user.id}
                className="w-8 h-8 rounded-full border-2 border-background bg-primary flex items-center justify-center text-primary-foreground text-xs font-medium"
                title={user.name}
              >
                {user.avatar ? (
                  <img 
                    src={user.avatar} 
                    alt={user.name} 
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  user.name.charAt(0)
                )}
              </div>
            ))}
            
            {activeUsers.length > 3 && (
              <div 
                className="w-8 h-8 rounded-full border-2 border-background bg-muted flex items-center justify-center text-xs font-medium"
                title={`${activeUsers.length - 3} more users`}
              >
                +{activeUsers.length - 3}
              </div>
            )}
          </div>
        )}
        
        {/* Notifications */}
        <div className="relative">
          <button 
            className="p-2 rounded hover:bg-muted relative"
            onClick={toggleNotifications}
          >
            <Bell className="w-4 h-4" />
            {notifications > 0 && (
              <span className="absolute top-1 right-1 w-3 h-3 bg-red-500 rounded-full flex items-center justify-center text-[10px] text-white">
                {notifications > 9 ? '9+' : notifications}
              </span>
            )}
          </button>
          
          {showNotifications && (
            <div className="absolute right-0 mt-1 w-80 bg-card border border-border rounded-md shadow-md z-10">
              <div className="p-3 border-b border-border">
                <h3 className="font-medium text-sm">Notifications</h3>
              </div>
              
              <div className="max-h-80 overflow-y-auto">
                {notifications > 0 ? (
                  <div className="p-3 border-b border-border">
                    <div className="flex items-start">
                      <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mr-3">
                        <Mail className="w-4 h-4" />
                      </div>
                      
                      <div>
                        <p className="text-sm">Your campaign "Spring Sale" has been sent to 1,245 recipients.</p>
                        <p className="text-xs text-muted-foreground mt-1">2 hours ago</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-6 text-center text-muted-foreground">
                    <p className="text-sm">No new notifications</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* Settings */}
        <button className="p-2 rounded hover:bg-muted">
          <Settings className="w-4 h-4" />
        </button>
        
        {/* User Menu */}
        <div className="relative">
          <button 
            className="flex items-center space-x-1 p-1 rounded hover:bg-muted"
            onClick={toggleUserMenu}
          >
            <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
              <User className="w-4 h-4" />
            </div>
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          </button>
          
          {showUserMenu && (
            <div className="absolute right-0 mt-1 w-48 bg-card border border-border rounded-md shadow-md z-10">
              <div className="p-3 border-b border-border">
                <div className="font-medium">John Doe</div>
                <div className="text-xs text-muted-foreground">john.doe@example.com</div>
              </div>
              
              <ul className="py-1">
                <li>
                  <button className="w-full px-4 py-2 text-sm text-left hover:bg-muted">
                    Profile Settings
                  </button>
                </li>
                <li>
                  <button className="w-full px-4 py-2 text-sm text-left hover:bg-muted">
                    Team Management
                  </button>
                </li>
                <li>
                  <button className="w-full px-4 py-2 text-sm text-left hover:bg-muted">
                    Billing & Plans
                  </button>
                </li>
                <li className="border-t border-border">
                  <button className="w-full px-4 py-2 text-sm text-left hover:bg-muted">
                    Sign Out
                  </button>
                </li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
