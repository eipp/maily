import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function TemplateDetailSkeleton() {
  return (
    <>
      <div className="bg-background rounded-lg border p-6">
        <div className="flex flex-col md:flex-row justify-between gap-6">
          <div className="space-y-4">
            <div>
              <Skeleton className="h-8 w-[300px]" />
              <Skeleton className="h-5 w-[200px] mt-1" />
            </div>

            <Skeleton className="h-4 w-full max-w-[500px]" />
            <Skeleton className="h-4 w-3/4 max-w-[400px]" />

            <div>
              <Skeleton className="h-6 w-[100px] rounded-full" />
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
            <Skeleton className="h-6 w-[120px]" />
            <Skeleton className="h-9 w-[100px]" />
          </div>

          <div className="border rounded-md">
            <div className="bg-muted p-2 border-b flex items-center justify-between">
              <Skeleton className="h-5 w-[120px]" />
              <div className="flex gap-2">
                <Skeleton className="h-9 w-[80px]" />
                <Skeleton className="h-9 w-[80px]" />
              </div>
            </div>
            <div className="p-4 min-h-[400px]">
              <Skeleton className="h-full w-full" />
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </>
  );
}
