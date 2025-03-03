import { Skeleton } from '@/components/ui/skeleton';

export default function DashboardLoading() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-8 flex flex-col gap-2">
        <Skeleton className="h-10 w-[250px]" />
        <Skeleton className="h-4 w-[350px]" />
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {/* Stats card skeletons */}
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border p-6 shadow-sm">
            <Skeleton className="mb-2 h-4 w-[120px]" />
            <Skeleton className="mb-4 h-8 w-[80px]" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="mt-1 h-3 w-[80%]" />
          </div>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Chart skeletons */}
        <div className="rounded-lg border p-6 shadow-sm">
          <Skeleton className="mb-4 h-6 w-[150px]" />
          <Skeleton className="h-[200px] w-full" />
        </div>

        <div className="rounded-lg border p-6 shadow-sm">
          <Skeleton className="mb-4 h-6 w-[180px]" />
          <Skeleton className="h-[200px] w-full" />
        </div>
      </div>

      <div className="mt-8 rounded-lg border p-6 shadow-sm">
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
    </div>
  );
}
