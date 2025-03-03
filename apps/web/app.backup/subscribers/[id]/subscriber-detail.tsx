import { executeQuery } from '@/lib/apollo-server';
import { GET_SUBSCRIBER } from '@/graphql/queries';
import Link from 'next/link';
import { formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MailIcon,
  PhoneIcon,
  MapPinIcon,
  CalendarIcon,
  BarChart2Icon,
  LockIcon,
  UnlockIcon,
  EditIcon,
  TrashIcon,
} from 'lucide-react';

interface SubscriberDetailProps {
  id: string;
}

interface SubscriberTag {
  id: string;
  name: string;
}

interface Subscriber {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  phone: string | null;
  address: {
    street: string | null;
    city: string | null;
    state: string | null;
    country: string | null;
    zipCode: string | null;
  } | null;
  isActive: boolean;
  joinedAt: string;
  lastActivity: string;
  source: string;
  tags: SubscriberTag[];
  engagementScore: number;
  emailsSent: number;
  emailsOpened: number;
  emailsClicked: number;
}

interface SubscriberData {
  subscriber: Subscriber;
}

export async function SubscriberDetail({ id }: SubscriberDetailProps) {
  try {
    const data = await executeQuery<SubscriberData>(GET_SUBSCRIBER, { id });
    const subscriber = data.subscriber;

    if (!subscriber) {
      return (
        <div className="text-center py-12">
          <p className="text-destructive">Subscriber not found</p>
        </div>
      );
    }

    const openRate = subscriber.emailsSent > 0
      ? ((subscriber.emailsOpened / subscriber.emailsSent) * 100).toFixed(1)
      : '0';

    const clickRate = subscriber.emailsSent > 0
      ? ((subscriber.emailsClicked / subscriber.emailsSent) * 100).toFixed(1)
      : '0';

    const getEngagementColor = (score: number) => {
      if (score >= 80) return 'text-green-600';
      if (score >= 50) return 'text-amber-600';
      return 'text-red-600';
    };

    return (
      <>
        <div className="bg-background rounded-lg border p-6">
          <div className="flex flex-col md:flex-row justify-between gap-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center text-2xl font-semibold text-primary">
                  {subscriber.firstName.charAt(0)}{subscriber.lastName.charAt(0)}
                </div>
                <div>
                  <h1 className="text-2xl font-bold">
                    {subscriber.firstName} {subscriber.lastName}
                  </h1>
                  <div className="flex items-center gap-2 text-muted-foreground mt-1">
                    <MailIcon className="h-4 w-4" />
                    <a href={`mailto:${subscriber.email}`} className="hover:underline">
                      {subscriber.email}
                    </a>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mt-3">
                {subscriber.tags.map((tag) => (
                  <Badge key={tag.id} variant="outline">
                    {tag.name}
                  </Badge>
                ))}
                <Button variant="outline" size="sm" className="h-6 text-xs px-2 gap-1">
                  <span>+</span> Add Tag
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                {subscriber.phone && (
                  <div className="flex items-center text-muted-foreground">
                    <PhoneIcon className="h-4 w-4 mr-2" />
                    <span>{subscriber.phone}</span>
                  </div>
                )}
                {subscriber.address && (
                  <div className="flex items-center text-muted-foreground">
                    <MapPinIcon className="h-4 w-4 mr-2" />
                    <span>
                      {[
                        subscriber.address.city,
                        subscriber.address.state,
                        subscriber.address.country
                      ].filter(Boolean).join(', ')}
                    </span>
                  </div>
                )}
                <div className="flex items-center text-muted-foreground">
                  <CalendarIcon className="h-4 w-4 mr-2" />
                  <span>Joined {formatDate(subscriber.joinedAt)}</span>
                </div>
                <div className="flex items-center text-muted-foreground">
                  <BarChart2Icon className="h-4 w-4 mr-2" />
                  <span>
                    Engagement:
                    <span className={`font-medium ml-1 ${getEngagementColor(subscriber.engagementScore)}`}>
                      {subscriber.engagementScore}%
                    </span>
                  </span>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-2 min-w-[8rem]">
              <Button asChild>
                <Link href={`/subscribers/${id}/edit`}>
                  <EditIcon className="mr-2 h-4 w-4" />
                  Edit
                </Link>
              </Button>
              <Button variant="outline" className="text-destructive hover:text-destructive">
                <TrashIcon className="mr-2 h-4 w-4" />
                Delete
              </Button>
              {subscriber.isActive ? (
                <Button variant="outline">
                  <LockIcon className="mr-2 h-4 w-4" />
                  Unsubscribe
                </Button>
              ) : (
                <Button variant="outline">
                  <UnlockIcon className="mr-2 h-4 w-4" />
                  Resubscribe
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-background rounded-lg border p-6">
            <h3 className="text-lg font-medium mb-1">Status</h3>
            <div className={`text-lg font-bold ${subscriber.isActive ? 'text-green-600' : 'text-red-600'}`}>
              {subscriber.isActive ? 'Active' : 'Inactive'}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {subscriber.isActive
                ? 'Receiving emails and updates'
                : 'Not receiving emails or updates'}
            </p>
          </div>

          <div className="bg-background rounded-lg border p-6">
            <h3 className="text-lg font-medium mb-1">Source</h3>
            <div className="text-lg font-bold">{subscriber.source}</div>
            <p className="text-sm text-muted-foreground mt-1">
              Joined on {formatDate(subscriber.joinedAt)}
            </p>
          </div>

          <div className="bg-background rounded-lg border p-6">
            <h3 className="text-lg font-medium mb-1">Engagement Score</h3>
            <div className={`text-lg font-bold ${getEngagementColor(subscriber.engagementScore)}`}>
              {subscriber.engagementScore}%
            </div>
            <div className="w-full h-2 bg-gray-100 rounded-full mt-2">
              <div
                className={`h-full rounded-full ${
                  subscriber.engagementScore >= 80
                    ? 'bg-green-500'
                    : subscriber.engagementScore >= 50
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                }`}
                style={{ width: `${subscriber.engagementScore}%` }}
              />
            </div>
          </div>

          <div className="bg-background rounded-lg border p-6">
            <h3 className="text-lg font-medium mb-1">Opens</h3>
            <div className="text-lg font-bold">{subscriber.emailsOpened} / {subscriber.emailsSent}</div>
            <p className="text-sm text-muted-foreground mt-1">
              Open rate: {openRate}%
            </p>
          </div>

          <div className="bg-background rounded-lg border p-6">
            <h3 className="text-lg font-medium mb-1">Clicks</h3>
            <div className="text-lg font-bold">{subscriber.emailsClicked} / {subscriber.emailsSent}</div>
            <p className="text-sm text-muted-foreground mt-1">
              Click rate: {clickRate}%
            </p>
          </div>

          <div className="bg-background rounded-lg border p-6">
            <h3 className="text-lg font-medium mb-1">Activity</h3>
            <div className="text-lg font-bold">
              {new Date(subscriber.lastActivity) > new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
                ? 'Active'
                : 'Inactive'}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Last active {formatDate(subscriber.lastActivity)}
            </p>
          </div>
        </div>
      </>
    );
  } catch (error) {
    console.error('Failed to fetch subscriber:', error);
    return (
      <div className="text-center py-8">
        <p className="text-destructive">Error loading subscriber details. Please try again later.</p>
        <Button variant="outline" className="mt-4">
          Retry
        </Button>
      </div>
    );
  }
}
