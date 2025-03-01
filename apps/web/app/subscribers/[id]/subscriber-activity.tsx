import { executeQuery } from '@/lib/apollo-server';
import { GET_SUBSCRIBER_ACTIVITY } from '@/graphql/queries';
import { formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  MailIcon,
  MousePointerClickIcon,
  EyeIcon,
  UserIcon,
  TagIcon,
  CheckIcon,
  XIcon,
  UserPlusIcon,
  RefreshCwIcon,
} from 'lucide-react';

interface SubscriberActivityProps {
  id: string;
}

interface ActivityItem {
  id: string;
  type: string;
  timestamp: string;
  details: {
    campaignId?: string;
    campaignName?: string;
    linkUrl?: string;
    tagId?: string;
    tagName?: string;
    fieldName?: string;
    oldValue?: string;
    newValue?: string;
    source?: string;
  };
}

interface ActivityData {
  subscriberActivity: ActivityItem[];
}

export async function SubscriberActivity({ id }: SubscriberActivityProps) {
  try {
    const data = await executeQuery<ActivityData>(GET_SUBSCRIBER_ACTIVITY, { id });
    const activities = data.subscriberActivity;

    if (!activities || activities.length === 0) {
      return (
        <div className="text-center py-6">
          <p className="text-muted-foreground">No activity recorded yet</p>
        </div>
      );
    }

    const getActivityIcon = (type: string) => {
      switch (type) {
        case 'EMAIL_RECEIVED':
          return <MailIcon className="h-4 w-4" />;
        case 'EMAIL_OPENED':
          return <EyeIcon className="h-4 w-4" />;
        case 'EMAIL_CLICKED':
          return <MousePointerClickIcon className="h-4 w-4" />;
        case 'PROFILE_UPDATED':
          return <UserIcon className="h-4 w-4" />;
        case 'TAG_ADDED':
          return <TagIcon className="h-4 w-4" />;
        case 'TAG_REMOVED':
          return <XIcon className="h-4 w-4" />;
        case 'SUBSCRIBED':
          return <CheckIcon className="h-4 w-4" />;
        case 'UNSUBSCRIBED':
          return <XIcon className="h-4 w-4" />;
        case 'SIGNED_UP':
          return <UserPlusIcon className="h-4 w-4" />;
        default:
          return <RefreshCwIcon className="h-4 w-4" />;
      }
    };

    const getActivityText = (activity: ActivityItem) => {
      const { type, details } = activity;

      switch (type) {
        case 'EMAIL_RECEIVED':
          return `Received email "${details.campaignName}"`;
        case 'EMAIL_OPENED':
          return `Opened email "${details.campaignName}"`;
        case 'EMAIL_CLICKED':
          return `Clicked link in "${details.campaignName}": ${details.linkUrl}`;
        case 'PROFILE_UPDATED':
          return `Updated profile field "${details.fieldName}" from "${details.oldValue}" to "${details.newValue}"`;
        case 'TAG_ADDED':
          return `Added to tag "${details.tagName}"`;
        case 'TAG_REMOVED':
          return `Removed from tag "${details.tagName}"`;
        case 'SUBSCRIBED':
          return 'Subscribed to emails';
        case 'UNSUBSCRIBED':
          return 'Unsubscribed from emails';
        case 'SIGNED_UP':
          return `Signed up via ${details.source}`;
        default:
          return 'Unknown activity';
      }
    };

    const getActivityColor = (type: string) => {
      switch (type) {
        case 'EMAIL_OPENED':
        case 'EMAIL_CLICKED':
        case 'SUBSCRIBED':
        case 'SIGNED_UP':
        case 'TAG_ADDED':
          return 'bg-green-500';
        case 'UNSUBSCRIBED':
        case 'TAG_REMOVED':
          return 'bg-red-500';
        case 'EMAIL_RECEIVED':
        case 'PROFILE_UPDATED':
          return 'bg-blue-500';
        default:
          return 'bg-gray-500';
      }
    };

    return (
      <div className="bg-background rounded-lg border p-6">
        <h3 className="text-lg font-medium mb-6">Activity History</h3>

        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-2.5 top-0 bottom-0 w-px bg-border"></div>

          <div className="space-y-6">
            {activities.map((activity) => (
              <div key={activity.id} className="relative flex gap-4">
                <div className={`h-5 w-5 rounded-full ${getActivityColor(activity.type)} flex items-center justify-center flex-shrink-0 z-10`}>
                  <div className="text-white">
                    {getActivityIcon(activity.type)}
                  </div>
                </div>
                <div className="flex-1 pt-0.5">
                  <p className="text-sm font-medium">{getActivityText(activity)}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatDate(activity.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 text-center">
          <Button variant="outline" size="sm">
            Load More Activity
          </Button>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Failed to fetch subscriber activity:', error);
    return (
      <div className="text-center py-8">
        <p className="text-destructive">Error loading activity history. Please try again later.</p>
        <Button variant="outline" className="mt-4">
          Retry
        </Button>
      </div>
    );
  }
}
