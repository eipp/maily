import { Skeleton } from '@/components/ui/skeleton';

export function SubscriberActivitySkeleton() {
  return (
    <div className="bg-background rounded-lg border p-6">
      <Skeleton className="h-6 w-[180px] mb-6" />

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-2.5 top-0 bottom-6 w-px bg-border"></div>

        <div className="space-y-6">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="relative flex gap-4">
              <Skeleton className="h-5 w-5 rounded-full flex-shrink-0 z-10" />
              <div className="flex-1 pt-0.5">
                <Skeleton className="h-4 w-[80%]" />
                <Skeleton className="h-3 w-[40%] mt-1" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 text-center">
        <Skeleton className="h-9 w-[120px] mx-auto" />
      </div>
    </div>
  );
}
