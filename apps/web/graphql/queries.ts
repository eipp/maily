import { gql } from '@apollo/client';

// User-related queries
export const CURRENT_USER = gql`
  query CurrentUser {
    currentUser {
      id
      email
      firstName
      lastName
      role
    }
  }
`;

// Campaign-related queries
export const GET_CAMPAIGNS = gql`
  query GetCampaigns($page: Int, $pageSize: Int) {
    campaigns(page: $page, pageSize: $pageSize) {
      id
      name
      subject
      status
      createdAt
      stats {
        sent
        opened
        clicked
      }
    }
  }
`;

export const GET_CAMPAIGN = gql`
  query GetCampaign($id: ID!) {
    campaign(id: $id) {
      id
      name
      subject
      previewText
      fromName
      fromEmail
      replyToEmail
      status
      createdAt
      scheduledFor
      sentAt
      trackOpens
      trackClicks
      template {
        id
        name
      }
      segment {
        id
        name
        count
      }
      stats {
        sent
        opened
        clicked
        bounced
        unsubscribed
      }
    }
  }
`;

export const GET_CAMPAIGN_STATS = gql`
  query GetCampaignStats($id: ID!) {
    campaignStats(id: $id) {
      dailyStats {
        date
        opens
        clicks
      }
      deviceStats {
        device
        count
      }
      locationStats {
        country
        count
      }
      linkStats {
        url
        clicks
      }
    }
  }
`;

// Subscriber-related queries
export const GET_SUBSCRIBERS = gql`
  query GetSubscribers($page: Int, $pageSize: Int, $filters: SubscriberFiltersInput) {
    subscribers(page: $page, pageSize: $pageSize, filters: $filters) {
      id
      email
      firstName
      lastName
      isActive
      joinedAt
      lastActivity
      tags {
        id
        name
      }
      engagementScore
    }
  }
`;

export const GET_SUBSCRIBER = gql`
  query GetSubscriber($id: ID!) {
    subscriber(id: $id) {
      id
      email
      firstName
      lastName
      phone
      address {
        street
        city
        state
        country
        zipCode
      }
      isActive
      joinedAt
      lastActivity
      source
      tags {
        id
        name
      }
      engagementScore
      emailsSent
      emailsOpened
      emailsClicked
    }
  }
`;

export const GET_SUBSCRIBER_ACTIVITY = gql`
  query GetSubscriberActivity($id: ID!, $limit: Int) {
    subscriberActivity(id: $id, limit: $limit) {
      id
      type
      timestamp
      details {
        campaignId
        campaignName
        linkUrl
        tagId
        tagName
        fieldName
        oldValue
        newValue
        source
      }
    }
  }
`;

export const GET_SUBSCRIBER_FILTERS = gql`
  query GetSubscriberFilters {
    subscriberFilters {
      status {
        id
        name
        count
      }
      sources {
        id
        name
        count
      }
      segments {
        id
        name
        count
      }
      activity {
        id
        name
        count
      }
    }
  }
`;

// Template-related queries
export const GET_TEMPLATES = gql`
  query GetTemplates($page: Int, $pageSize: Int) {
    templates(page: $page, pageSize: $pageSize) {
      id
      name
      description
      thumbnail
      createdAt
      category
    }
  }
`;

export const GET_TEMPLATE = gql`
  query GetTemplate($id: ID!) {
    template(id: $id) {
      id
      name
      description
      content
      category
      createdAt
    }
  }
`;
