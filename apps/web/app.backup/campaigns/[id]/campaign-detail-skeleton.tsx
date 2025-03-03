import { Skeleton } from '@/components/ui/skeleton';

export function CampaignDetailSkeleton() {
  return (
    <>
      <div className="bg-background rounded-lg border p-6">
        <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4">
          <div className="space-y-4 w-full md:w-2/3">
            <div className="flex items-center gap-2">
              <Skeleton className="h-8 w-[200px]" />
              <Skeleton className="h-6 w-[80px] rounded-full" />
            </div>
            <Skeleton className="h-5 w-[350px]" />
            <Skeleton className="h-5 w-[300px]" />
            <div className="flex flex-wrap gap-4">
              <Skeleton className="h-5 w-[150px]" />
              <Skeleton className="h-5 w-[180px]" />
            </div>
          </div>

          <div className="flex gap-2">
            <Skeleton className="h-10 w-[120px] rounded-md" />
            <Skeleton className="h-10 w-[120px] rounded-md" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="bg-background rounded-lg border p-6">
            <div className="flex items-center justify-between">
              <Skeleton className="h-6 w-[100px]" />
              <Skeleton className="h-5 w-5 rounded-full" />
            </div>
            <Skeleton className="h-10 w-[80px] mt-2" />
            <Skeleton className="h-4 w-[120px] mt-2" />
          </div>
        ))}
      </div>
    </>
  );
}
