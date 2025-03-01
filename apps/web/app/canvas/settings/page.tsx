import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';
import CanvasLayout from '@/components/Canvas/CanvasLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import CanvasSettingsForm from './CanvasSettingsForm';

export default async function CanvasSettingsPage() {
  const session = await getSession();

  if (!session?.user) {
    redirect('/login?callbackUrl=/canvas/settings');
  }

  return (
    <CanvasLayout
      title="Canvas Settings"
      description="Configure your canvas preferences"
      showBackButton
      backButtonUrl="/canvas/dashboard"
      backButtonText="Back to Canvas Dashboard"
      activeNavItem="settings"
    >
      <div className="max-w-3xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Canvas Preferences</CardTitle>
            <CardDescription>
              Configure default settings for all your canvases
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CanvasSettingsForm />
          </CardContent>
        </Card>
      </div>
    </CanvasLayout>
  );
}
