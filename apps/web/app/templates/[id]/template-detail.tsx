import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ClockIcon, FileTextIcon, CodeIcon, BarChart2Icon } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import { getTemplate } from '@/services/graphql-templates';

interface TemplateDetailProps {
  id: string;
}

export async function TemplateDetail({ id }: TemplateDetailProps) {
  try {
    // Use the service instead of direct executeQuery
    const template = await getTemplate(id);

    if (!template) {
      return (
        <div className="text-center py-12">
          <p className="text-destructive">Template not found</p>
        </div>
      );
    }

    return (
      <>
        <div className="bg-background rounded-lg border p-6">
          <div className="flex flex-col md:flex-row justify-between gap-6">
            <div className="space-y-4">
              <div>
                <h1 className="text-2xl font-bold">
                  {template.name}
                </h1>
                <div className="flex items-center gap-2 text-muted-foreground mt-1">
                  <ClockIcon className="h-4 w-4" />
                  <span>Created {formatDate(template.createdAt)}</span>
                </div>
              </div>

              <p className="text-muted-foreground">
                {template.description || "No description provided."}
              </p>

              <div>
                <Badge variant="outline">
                  {template.category || "Uncategorized"}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        <Tabs defaultValue="preview" className="mt-6">
          <TabsList className="mb-6">
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="html">HTML</TabsTrigger>
            <TabsTrigger value="stats">Usage Stats</TabsTrigger>
          </TabsList>

          <TabsContent value="preview" className="bg-background rounded-lg border p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium">Preview</h2>
              <Button variant="outline" size="sm">Test Send</Button>
            </div>

            <div className="border rounded-md">
              <div className="bg-muted p-2 border-b flex items-center justify-between">
                <div className="text-sm font-medium">Email Preview</div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm">Mobile</Button>
                  <Button variant="ghost" size="sm">Desktop</Button>
                </div>
              </div>
              <div className="p-4 min-h-[400px] flex items-center justify-center">
                {/* This would be an iframe or rendered HTML preview */}
                <div className="text-center text-muted-foreground">
                  <FileTextIcon className="h-12 w-12 mx-auto mb-2" />
                  <p>Email preview would render here</p>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="html" className="bg-background rounded-lg border p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium">HTML Source</h2>
              <Button variant="outline" size="sm">Copy HTML</Button>
            </div>

            <div className="bg-muted rounded-md p-4 max-h-[500px] overflow-auto">
              <pre className="text-sm">
                <code>{template.content || "<p>No content available</p>"}</code>
              </pre>
            </div>
          </TabsContent>

          <TabsContent value="stats" className="bg-background rounded-lg border p-6">
            <h2 className="text-lg font-medium mb-4">Usage Statistics</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="border rounded-md p-4">
                <p className="text-sm text-muted-foreground">Campaigns Used In</p>
                <p className="text-2xl font-bold mt-1">3</p>
              </div>
              <div className="border rounded-md p-4">
                <p className="text-sm text-muted-foreground">Total Sends</p>
                <p className="text-2xl font-bold mt-1">2,547</p>
              </div>
              <div className="border rounded-md p-4">
                <p className="text-sm text-muted-foreground">Average Open Rate</p>
                <p className="text-2xl font-bold mt-1">24.8%</p>
              </div>
            </div>

            <div className="mt-6">
              <h3 className="text-md font-medium mb-3">Campaigns</h3>
              <div className="border rounded-md divide-y">
                <div className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium">Monthly Newsletter - February</p>
                    <p className="text-sm text-muted-foreground">Sent on Feb 15, 2025</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">1,245 sends</p>
                    <p className="text-sm text-green-600">26.7% open rate</p>
                  </div>
                </div>
                <div className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium">Product Update Announcement</p>
                    <p className="text-sm text-muted-foreground">Sent on Jan 22, 2025</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">892 sends</p>
                    <p className="text-sm text-green-600">31.2% open rate</p>
                  </div>
                </div>
                <div className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium">Year-end Summary</p>
                    <p className="text-sm text-muted-foreground">Sent on Dec 28, 2024</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">410 sends</p>
                    <p className="text-sm text-amber-600">18.7% open rate</p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </>
    );
  } catch (error) {
    console.error('Failed to fetch template:', error);
    return (
      <div className="text-center py-8">
        <p className="text-destructive">Error loading template details. Please try again later.</p>
        <Button variant="outline" className="mt-4">
          Retry
        </Button>
      </div>
    );
  }
}
