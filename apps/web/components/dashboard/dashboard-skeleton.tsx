import { Skeleton } from '@/components/ui/skeleton';

interface DashboardSkeletonProps {
  type: 'stats' | 'chart' | 'campaigns';
}

export function DashboardSkeleton({ type }: DashboardSkeletonProps) {
  if (type === 'stats') {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border bg-card p-6 shadow-sm">
            <Skeleton className="mb-2 h-4 w-[120px]" />
            <Skeleton className="mb-4 h-8 w-[80px]" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="mt-1 h-3 w-[80%]" />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'chart') {
    return (
      <div className="rounded-lg border bg-card p-6 shadow-sm">
        <Skeleton className="mb-4 h-6 w-[150px]" />
        <Skeleton className="h-[200px] w-full" />
      </div>
    );
  }

  // Campaigns
  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <Skeleton className="mb-4 h-6 w-[200px]" />
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-12 w-12 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-[200px]" />
              <Skeleton className="h-3 w-[300px]" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
