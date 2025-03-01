import { gql } from '@apollo/client';

// Authentication mutations
export const LOGIN = gql`
  mutation Login($email: String!, $password: String!) {
    login(email: $email, password: $password) {
      token
      user {
        id
        email
        firstName
        lastName
        role
      }
    }
  }
`;

export const REGISTER = gql`
  mutation Register($email: String!, $password: String!, $firstName: String, $lastName: String) {
    register(email: $email, password: $password, firstName: $firstName, lastName: $lastName) {
      token
      user {
        id
        email
        firstName
        lastName
        role
      }
    }
  }
`;

// Campaign mutations
export const CREATE_CAMPAIGN = gql`
  mutation CreateCampaign(
    $name: String!,
    $subject: String!,
    $previewText: String,
    $templateId: ID!,
    $segmentId: ID!,
    $fromName: String!,
    $fromEmail: String!,
    $replyToEmail: String!,
    $trackOpens: Boolean!,
    $trackClicks: Boolean!
  ) {
    createCampaign(
      input: {
        name: $name,
        subject: $subject,
        previewText: $previewText,
        templateId: $templateId,
        segmentId: $segmentId,
        fromName: $fromName,
        fromEmail: $fromEmail,
        replyToEmail: $replyToEmail,
        trackOpens: $trackOpens,
        trackClicks: $trackClicks
      }
    ) {
      id
      name
      subject
      status
    }
  }
`;

export const UPDATE_CAMPAIGN = gql`
  mutation UpdateCampaign(
    $id: ID!,
    $name: String,
    $subject: String,
    $previewText: String,
    $templateId: ID,
    $segmentId: ID,
    $fromName: String,
    $fromEmail: String,
    $replyToEmail: String,
    $trackOpens: Boolean,
    $trackClicks: Boolean
  ) {
    updateCampaign(
      id: $id,
      input: {
        name: $name,
        subject: $subject,
        previewText: $previewText,
        templateId: $templateId,
        segmentId: $segmentId,
        fromName: $fromName,
        fromEmail: $fromEmail,
        replyToEmail: $replyToEmail,
        trackOpens: $trackOpens,
        trackClicks: $trackClicks
      }
    ) {
      id
      name
      subject
      status
    }
  }
`;

export const DELETE_CAMPAIGN = gql`
  mutation DeleteCampaign($id: ID!) {
    deleteCampaign(id: $id) {
      success
      message
    }
  }
`;

export const SEND_CAMPAIGN = gql`
  mutation SendCampaign($id: ID!) {
    sendCampaign(id: $id) {
      id
      status
    }
  }
`;

export const SCHEDULE_CAMPAIGN = gql`
  mutation ScheduleCampaign($id: ID!, $scheduledFor: DateTime!) {
    scheduleCampaign(id: $id, scheduledFor: $scheduledFor) {
      id
      status
      scheduledFor
    }
  }
`;

// Subscriber mutations
export const CREATE_SUBSCRIBER = gql`
  mutation CreateSubscriber(
    $email: String!,
    $firstName: String,
    $lastName: String,
    $phone: String,
    $address: AddressInput,
    $isActive: Boolean,
    $source: String,
    $tags: [ID!]
  ) {
    createSubscriber(
      input: {
        email: $email,
        firstName: $firstName,
        lastName: $lastName,
        phone: $phone,
        address: $address,
        isActive: $isActive,
        source: $source,
        tags: $tags
      }
    ) {
      id
      email
      firstName
      lastName
    }
  }
`;

export const UPDATE_SUBSCRIBER = gql`
  mutation UpdateSubscriber(
    $id: ID!,
    $email: String,
    $firstName: String,
    $lastName: String,
    $phone: String,
    $address: AddressInput,
    $isActive: Boolean
  ) {
    updateSubscriber(
      id: $id,
      input: {
        email: $email,
        firstName: $firstName,
        lastName: $lastName,
        phone: $phone,
        address: $address,
        isActive: $isActive
      }
    ) {
      id
      email
      firstName
      lastName
      isActive
    }
  }
`;

export const DELETE_SUBSCRIBER = gql`
  mutation DeleteSubscriber($id: ID!) {
    deleteSubscriber(id: $id) {
      success
      message
    }
  }
`;

export const ADD_TAG_TO_SUBSCRIBER = gql`
  mutation AddTagToSubscriber($subscriberId: ID!, $tagId: ID!) {
    addTagToSubscriber(subscriberId: $subscriberId, tagId: $tagId) {
      id
      tags {
        id
        name
      }
    }
  }
`;

export const REMOVE_TAG_FROM_SUBSCRIBER = gql`
  mutation RemoveTagFromSubscriber($subscriberId: ID!, $tagId: ID!) {
    removeTagFromSubscriber(subscriberId: $subscriberId, tagId: $tagId) {
      id
      tags {
        id
        name
      }
    }
  }
`;

export const UNSUBSCRIBE_SUBSCRIBER = gql`
  mutation UnsubscribeSubscriber($id: ID!) {
    unsubscribeSubscriber(id: $id) {
      id
      isActive
    }
  }
`;

export const RESUBSCRIBE_SUBSCRIBER = gql`
  mutation ResubscribeSubscriber($id: ID!) {
    resubscribeSubscriber(id: $id) {
      id
      isActive
    }
  }
`;

// Template mutations
export const CREATE_TEMPLATE = gql`
  mutation CreateTemplate($name: String!, $description: String, $content: String!, $category: String) {
    createTemplate(
      input: {
        name: $name,
        description: $description,
        content: $content,
        category: $category
      }
    ) {
      id
      name
      description
    }
  }
`;

export const UPDATE_TEMPLATE = gql`
  mutation UpdateTemplate($id: ID!, $name: String, $description: String, $content: String, $category: String) {
    updateTemplate(
      id: $id,
      input: {
        name: $name,
        description: $description,
        content: $content,
        category: $category
      }
    ) {
      id
      name
      description
    }
  }
`;

export const DELETE_TEMPLATE = gql`
  mutation DeleteTemplate($id: ID!) {
    deleteTemplate(id: $id) {
      success
      message
    }
  }
`;
