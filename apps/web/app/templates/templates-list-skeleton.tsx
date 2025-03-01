import { Skeleton } from '@/components/ui/skeleton';

export function TemplatesListSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="border rounded-lg overflow-hidden bg-background"
        >
          <div className="relative aspect-video bg-muted">
            <Skeleton className="absolute inset-0" />
          </div>

          <div className="p-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2 w-full">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </div>
              <Skeleton className="h-8 w-8 rounded-md flex-shrink-0" />
            </div>

            <div className="flex items-center justify-between mt-4">
              <Skeleton className="h-5 w-[80px] rounded-full" />
              <Skeleton className="h-4 w-[100px]" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
