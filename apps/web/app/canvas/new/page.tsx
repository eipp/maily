import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';
import CanvasLayout from '@/components/Canvas/CanvasLayout';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import NewCanvasForm from './NewCanvasForm';

export default async function NewCanvasPage() {
  const session = await getSession();

  if (!session?.user) {
    redirect('/login?callbackUrl=/canvas/new');
  }

  return (
    <CanvasLayout
      title="Create New Canvas"
      description="Set up a new collaborative canvas"
      showBackButton
      backButtonUrl="/canvas/dashboard"
      backButtonText="Back to Canvas Dashboard"
      activeNavItem="new"
    >
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>New Canvas Details</CardTitle>
          <CardDescription>
            Fill out the information below to create your new canvas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <NewCanvasForm />
        </CardContent>
      </Card>
    </CanvasLayout>
  );
}
