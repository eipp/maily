import { executeQuery } from '@/lib/apollo-server';
import { GET_SUBSCRIBER_FILTERS } from '@/graphql/queries';
import { Button } from '@/components/ui/button';
import { RefreshCwIcon } from 'lucide-react';

interface FilterCount {
  id: string;
  name: string;
  count: number;
}

interface FilterData {
  status: FilterCount[];
  sources: FilterCount[];
  segments: FilterCount[];
  activity: FilterCount[];
}

interface FilterResponse {
  subscriberFilters: FilterData;
}

export async function SubscribersFilter() {
  try {
    const data = await executeQuery<FilterResponse>(GET_SUBSCRIBER_FILTERS);
    const filters = data.subscriberFilters;

    if (!filters) {
      return (
        <div className="text-center py-4">
          <p className="text-muted-foreground text-sm">Unable to load filters</p>
          <Button variant="outline" size="sm" className="mt-2">
            <RefreshCwIcon className="mr-2 h-3 w-3" />
            Retry
          </Button>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {/* Status Filters */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Status</p>
          {filters.status.map((item) => (
            <div key={item.id} className="flex items-center">
              <input type="checkbox" id={`status-${item.id}`} className="mr-2" />
              <label htmlFor={`status-${item.id}`} className="text-sm">{item.name}</label>
              <span className="ml-auto text-xs text-muted-foreground">{item.count}</span>
            </div>
          ))}
        </div>

        {/* Sources Filters */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Source</p>
          {filters.sources.map((item) => (
            <div key={item.id} className="flex items-center">
              <input type="checkbox" id={`source-${item.id}`} className="mr-2" />
              <label htmlFor={`source-${item.id}`} className="text-sm">{item.name}</label>
              <span className="ml-auto text-xs text-muted-foreground">{item.count}</span>
            </div>
          ))}
        </div>

        {/* Segments Filters */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Segments</p>
          {filters.segments.map((item) => (
            <div key={item.id} className="flex items-center">
              <input type="checkbox" id={`segment-${item.id}`} className="mr-2" />
              <label htmlFor={`segment-${item.id}`} className="text-sm">{item.name}</label>
              <span className="ml-auto text-xs text-muted-foreground">{item.count}</span>
            </div>
          ))}
        </div>

        {/* Activity Filters */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Activity</p>
          {filters.activity.map((item) => (
            <div key={item.id} className="flex items-center">
              <input type="checkbox" id={`activity-${item.id}`} className="mr-2" />
              <label htmlFor={`activity-${item.id}`} className="text-sm">{item.name}</label>
              <span className="ml-auto text-xs text-muted-foreground">{item.count}</span>
            </div>
          ))}
        </div>

        <div className="pt-2 flex justify-between">
          <Button variant="outline" size="sm">
            Reset Filters
          </Button>
          <Button size="sm">
            Apply
          </Button>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Failed to fetch filter data:', error);
    return (
      <div className="text-center py-4">
        <p className="text-destructive text-sm">Error loading filters</p>
        <Button variant="outline" size="sm" className="mt-2">
          <RefreshCwIcon className="mr-2 h-3 w-3" />
          Retry
        </Button>
      </div>
    );
  }
}
