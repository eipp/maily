import { ApolloError } from '@apollo/client';
import {
  GET_SUBSCRIBERS,
  GET_SUBSCRIBER,
  GET_SUBSCRIBER_ACTIVITY,
  GET_SUBSCRIBER_FILTERS
} from '@/graphql/queries';
import {
  CREATE_SUBSCRIBER,
  UPDATE_SUBSCRIBER,
  DELETE_SUBSCRIBER,
  ADD_TAG_TO_SUBSCRIBER,
  REMOVE_TAG_FROM_SUBSCRIBER,
  UNSUBSCRIBE_SUBSCRIBER,
  RESUBSCRIBE_SUBSCRIBER
} from '@/graphql/mutations';
import { executeQuery, executeMutation } from '@/lib/apollo-server';

/**
 * Subscribers GraphQL Service
 * Provides functions for interacting with subscriber data through GraphQL
 */

// Interfaces
export interface Address {
  street?: string;
  city?: string;
  state?: string;
  country?: string;
  zipCode?: string;
}

export interface Tag {
  id: string;
  name: string;
}

export interface Subscriber {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  address?: Address;
  isActive: boolean;
  joinedAt: string;
  lastActivity?: string;
  source?: string;
  tags: Tag[];
  engagementScore: number;
  emailsSent?: number;
  emailsOpened?: number;
  emailsClicked?: number;
}

export interface ActivityDetails {
  campaignId?: string;
  campaignName?: string;
  linkUrl?: string;
  tagId?: string;
  tagName?: string;
  fieldName?: string;
  oldValue?: string;
  newValue?: string;
  source?: string;
}

export interface SubscriberActivity {
  id: string;
  type: string;
  timestamp: string;
  details: ActivityDetails;
}

export interface SubscriberFiltersOption {
  id: string;
  name: string;
  count: number;
}

export interface SubscriberFilters {
  status: SubscriberFiltersOption[];
  sources: SubscriberFiltersOption[];
  segments: SubscriberFiltersOption[];
  activity: SubscriberFiltersOption[];
}

export interface SubscriberFiltersInput {
  status?: string[];
  source?: string[];
  segment?: string[];
  tag?: string[];
  activity?: string[];
  searchQuery?: string;
  dateFrom?: string;
  dateTo?: string;
}

// Response interfaces
export interface SubscribersData {
  subscribers: Subscriber[];
}

export interface SubscriberData {
  subscriber: Subscriber;
}

export interface SubscriberActivityData {
  subscriberActivity: SubscriberActivity[];
}

export interface SubscriberFiltersData {
  subscriberFilters: SubscriberFilters;
}

// Input interfaces
export interface SubscriberInput {
  email: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  address?: Address;
  isActive?: boolean;
  source?: string;
  tags?: string[];
}

/**
 * Fetch subscribers list with optional filtering and pagination
 */
export async function getSubscribers(
  page: number = 1,
  pageSize: number = 10,
  filters?: SubscriberFiltersInput
): Promise<Subscriber[]> {
  try {
    const data = await executeQuery<SubscribersData>(GET_SUBSCRIBERS, {
      page,
      pageSize,
      filters
    });
    return data.subscribers;
  } catch (error) {
    console.error('Failed to fetch subscribers:', error);
    throw error;
  }
}

/**
 * Fetch a single subscriber by ID
 */
export async function getSubscriber(id: string): Promise<Subscriber | null> {
  try {
    const data = await executeQuery<SubscriberData>(GET_SUBSCRIBER, { id });
    return data.subscriber;
  } catch (error) {
    if (error instanceof ApolloError && error.message.includes('not found')) {
      return null;
    }
    console.error(`Failed to fetch subscriber ${id}:`, error);
    throw error;
  }
}

/**
 * Fetch activity history for a subscriber
 */
export async function getSubscriberActivity(
  id: string,
  limit: number = 20
): Promise<SubscriberActivity[]> {
  try {
    const data = await executeQuery<SubscriberActivityData>(GET_SUBSCRIBER_ACTIVITY, {
      id,
      limit
    });
    return data.subscriberActivity;
  } catch (error) {
    console.error(`Failed to fetch activity for subscriber ${id}:`, error);
    throw error;
  }
}

/**
 * Fetch available filters for subscribers
 */
export async function getSubscriberFilters(): Promise<SubscriberFilters> {
  try {
    const data = await executeQuery<SubscriberFiltersData>(GET_SUBSCRIBER_FILTERS);
    return data.subscriberFilters;
  } catch (error) {
    console.error('Failed to fetch subscriber filters:', error);
    throw error;
  }
}

/**
 * Create a new subscriber
 */
export async function createSubscriber(subscriber: SubscriberInput): Promise<Subscriber> {
  try {
    const response = await executeMutation<{ createSubscriber: Subscriber }>(
      CREATE_SUBSCRIBER,
      subscriber
    );
    return response.createSubscriber;
  } catch (error) {
    console.error('Failed to create subscriber:', error);
    throw error;
  }
}

/**
 * Update an existing subscriber
 */
export async function updateSubscriber(
  id: string,
  subscriber: Partial<SubscriberInput>
): Promise<Subscriber> {
  try {
    const response = await executeMutation<{ updateSubscriber: Subscriber }>(
      UPDATE_SUBSCRIBER,
      { id, ...subscriber }
    );
    return response.updateSubscriber;
  } catch (error) {
    console.error(`Failed to update subscriber ${id}:`, error);
    throw error;
  }
}

/**
 * Delete a subscriber
 */
export async function deleteSubscriber(id: string): Promise<{ success: boolean; message: string }> {
  try {
    const response = await executeMutation<{
      deleteSubscriber: { success: boolean; message: string }
    }>(DELETE_SUBSCRIBER, { id });
    return response.deleteSubscriber;
  } catch (error) {
    console.error(`Failed to delete subscriber ${id}:`, error);
    throw error;
  }
}

/**
 * Add a tag to a subscriber
 */
export async function addTagToSubscriber(subscriberId: string, tagId: string): Promise<Subscriber> {
  try {
    const response = await executeMutation<{ addTagToSubscriber: Subscriber }>(
      ADD_TAG_TO_SUBSCRIBER,
      { subscriberId, tagId }
    );
    return response.addTagToSubscriber;
  } catch (error) {
    console.error(`Failed to add tag to subscriber ${subscriberId}:`, error);
    throw error;
  }
}

/**
 * Remove a tag from a subscriber
 */
export async function removeTagFromSubscriber(subscriberId: string, tagId: string): Promise<Subscriber> {
  try {
    const response = await executeMutation<{ removeTagFromSubscriber: Subscriber }>(
      REMOVE_TAG_FROM_SUBSCRIBER,
      { subscriberId, tagId }
    );
    return response.removeTagFromSubscriber;
  } catch (error) {
    console.error(`Failed to remove tag from subscriber ${subscriberId}:`, error);
    throw error;
  }
}

/**
 * Unsubscribe a subscriber
 */
export async function unsubscribeSubscriber(id: string): Promise<Subscriber> {
  try {
    const response = await executeMutation<{ unsubscribeSubscriber: Subscriber }>(
      UNSUBSCRIBE_SUBSCRIBER,
      { id }
    );
    return response.unsubscribeSubscriber;
  } catch (error) {
    console.error(`Failed to unsubscribe subscriber ${id}:`, error);
    throw error;
  }
}

/**
 * Resubscribe a subscriber
 */
export async function resubscribeSubscriber(id: string): Promise<Subscriber> {
  try {
    const response = await executeMutation<{ resubscribeSubscriber: Subscriber }>(
      RESUBSCRIBE_SUBSCRIBER,
      { id }
    );
    return response.resubscribeSubscriber;
  } catch (error) {
    console.error(`Failed to resubscribe subscriber ${id}:`, error);
    throw error;
  }
}
