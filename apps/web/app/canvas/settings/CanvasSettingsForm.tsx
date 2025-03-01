'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Save, Check } from 'lucide-react';
import { toast } from 'sonner';

interface CanvasSettings {
  defaultCanvasWidth: number;
  defaultCanvasHeight: number;
  autosave: boolean;
  autosaveInterval: number;
  theme: 'system' | 'light' | 'dark';
  gridEnabled: boolean;
  snapToGrid: boolean;
  gridSize: number;
}

export default function CanvasSettingsForm() {
  const [settings, setSettings] = useState<CanvasSettings>({
    defaultCanvasWidth: 1920,
    defaultCanvasHeight: 1080,
    autosave: true,
    autosaveInterval: 30,
    theme: 'system',
    gridEnabled: true,
    snapToGrid: true,
    gridSize: 20
  });

  const [isSaving, setIsSaving] = useState(false);

  const handleSaveSettings = async () => {
    setIsSaving(true);

    try {
      // In a real app, this would save to a backend
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Simulate API call
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/user/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          canvasSettings: settings
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save settings');
      }

      toast.success('Settings saved successfully!', {
        icon: <Check className="h-4 w-4" />,
      });
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Failed to save settings. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="theme">Theme</Label>
            <Select
              value={settings.theme}
              onValueChange={(value) => setSettings({...settings, theme: value as any})}
            >
              <SelectTrigger id="theme" className="w-full mt-1">
                <SelectValue placeholder="Select theme" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="system">System</SelectItem>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="autosave">Autosave</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically save canvas changes
                </p>
              </div>
              <Switch
                id="autosave"
                checked={settings.autosave}
                onCheckedChange={(checked) => setSettings({...settings, autosave: checked})}
              />
            </div>

            {settings.autosave && (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label htmlFor="autosaveInterval">Autosave Interval (seconds)</Label>
                  <span className="text-sm font-medium">{settings.autosaveInterval}s</span>
                </div>
                <Slider
                  id="autosaveInterval"
                  min={5}
                  max={120}
                  step={5}
                  value={[settings.autosaveInterval]}
                  onValueChange={(value) => setSettings({...settings, autosaveInterval: value[0]})}
                />
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <Label>Default Canvas Size</Label>
            <div className="grid grid-cols-2 gap-2 mt-1">
              <div>
                <Label htmlFor="width" className="text-xs text-muted-foreground">Width (px)</Label>
                <Select
                  value={settings.defaultCanvasWidth.toString()}
                  onValueChange={(value) => setSettings({...settings, defaultCanvasWidth: parseInt(value)})}
                >
                  <SelectTrigger id="width">
                    <SelectValue placeholder="Width" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1280">1280</SelectItem>
                    <SelectItem value="1920">1920</SelectItem>
                    <SelectItem value="2560">2560</SelectItem>
                    <SelectItem value="3840">3840</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="height" className="text-xs text-muted-foreground">Height (px)</Label>
                <Select
                  value={settings.defaultCanvasHeight.toString()}
                  onValueChange={(value) => setSettings({...settings, defaultCanvasHeight: parseInt(value)})}
                >
                  <SelectTrigger id="height">
                    <SelectValue placeholder="Height" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="720">720</SelectItem>
                    <SelectItem value="1080">1080</SelectItem>
                    <SelectItem value="1440">1440</SelectItem>
                    <SelectItem value="2160">2160</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="grid">Show Grid</Label>
                <p className="text-sm text-muted-foreground">
                  Display a grid in the canvas background
                </p>
              </div>
              <Switch
                id="grid"
                checked={settings.gridEnabled}
                onCheckedChange={(checked) => setSettings({...settings, gridEnabled: checked})}
              />
            </div>

            {settings.gridEnabled && (
              <>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="snapToGrid">Snap to Grid</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically align elements to grid
                    </p>
                  </div>
                  <Switch
                    id="snapToGrid"
                    checked={settings.snapToGrid}
                    onCheckedChange={(checked) => setSettings({...settings, snapToGrid: checked})}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <Label htmlFor="gridSize">Grid Size (px)</Label>
                    <span className="text-sm font-medium">{settings.gridSize}px</span>
                  </div>
                  <Slider
                    id="gridSize"
                    min={5}
                    max={50}
                    step={5}
                    value={[settings.gridSize]}
                    onValueChange={(value) => setSettings({...settings, gridSize: value[0]})}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="pt-4 border-t">
        <Button
          onClick={handleSaveSettings}
          disabled={isSaving}
          className="w-full"
        >
          {isSaving ? (
            <span className="flex items-center justify-center">
              <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
              Saving...
            </span>
          ) : (
            <span className="flex items-center justify-center">
              <Save className="mr-2 h-4 w-4" />
              Save Settings
            </span>
          )}
        </Button>
      </div>
    </div>
  );
}
