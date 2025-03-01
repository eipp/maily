import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

export function SubscriberDetailSkeleton() {
  return (
    <>
      <div className="bg-background rounded-lg border p-6">
        <div className="flex flex-col md:flex-row justify-between gap-6">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Skeleton className="h-16 w-16 rounded-full" />
              <div>
                <Skeleton className="h-8 w-[200px]" />
                <Skeleton className="h-5 w-[220px] mt-1" />
              </div>
            </div>

            <div className="flex flex-wrap gap-2 mt-3">
              <Skeleton className="h-6 w-[80px] rounded-full" />
              <Skeleton className="h-6 w-[120px] rounded-full" />
              <Skeleton className="h-6 w-[100px] rounded-full" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
              <Skeleton className="h-5 w-[180px]" />
              <Skeleton className="h-5 w-[150px]" />
              <Skeleton className="h-5 w-[200px]" />
              <Skeleton className="h-5 w-[160px]" />
            </div>
          </div>

          <div className="flex flex-col gap-2 min-w-[8rem]">
            <Skeleton className="h-10 w-[100px]" />
            <Skeleton className="h-10 w-[100px]" />
            <Skeleton className="h-10 w-[100px]" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="bg-background rounded-lg border p-6">
            <Skeleton className="h-6 w-[120px]" />
            <Skeleton className="h-7 w-[80px] mt-1" />
            <Skeleton className="h-4 w-full mt-1" />
          </div>
        ))}
      </div>
    </>
  );
}
