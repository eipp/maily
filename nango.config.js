/**
 * Nango Configuration
 *
 * This file defines the sync configurations for Nango.
 * It specifies how data should be synchronized from different platforms.
 */

module.exports = {
  syncConfigs: [
    // LinkedIn Syncs
    {
      name: 'linkedin-contacts',
      provider: 'linkedin',
      models: ['contacts'],
      runs: 'every 1h',
      sync_type: 'full',
      output: {
        schema: {
          contacts: {
            first_name: 'string',
            last_name: 'string',
            title: 'string',
            company: 'string',
            email: 'string?',
            phone: 'string?',
            profile_url: 'string?',
            profile_picture_url: 'string?',
            location: 'string?',
            industry: 'string?',
            connection_degree: 'number?',
            last_modified: 'date?'
          }
        }
      }
    },
    {
      name: 'linkedin-companies',
      provider: 'linkedin',
      models: ['companies'],
      runs: 'every 6h',
      sync_type: 'full',
      output: {
        schema: {
          companies: {
            name: 'string',
            industry: 'string?',
            website: 'string?',
            company_size: 'string?',
            company_type: 'string?',
            founded_year: 'number?',
            logo_url: 'string?',
            tagline: 'string?',
            description: 'string?',
            location: 'string?',
            followers_count: 'number?'
          }
        }
      }
    },
    {
      name: 'linkedin-posts',
      provider: 'linkedin',
      models: ['posts'],
      runs: 'every 3h',
      sync_type: 'incremental',
      output: {
        schema: {
          posts: {
            id: 'string',
            content: 'string',
            author: 'object',
            created_at: 'date',
            updated_at: 'date?',
            likes_count: 'number?',
            comments_count: 'number?',
            shares_count: 'number?',
            url: 'string?',
            media: 'array?'
          }
        }
      }
    },

    // Twitter Syncs
    {
      name: 'twitter-followers',
      provider: 'twitter',
      models: ['followers'],
      runs: 'every 2h',
      sync_type: 'incremental',
      output: {
        schema: {
          followers: {
            id: 'string',
            username: 'string',
            name: 'string',
            profile_image_url: 'string?',
            description: 'string?',
            location: 'string?',
            verified: 'boolean?',
            followers_count: 'number?',
            following_count: 'number?',
            created_at: 'date?'
          }
        }
      }
    },
    {
      name: 'twitter-tweets',
      provider: 'twitter',
      models: ['tweets'],
      runs: 'every 1h',
      sync_type: 'incremental',
      output: {
        schema: {
          tweets: {
            id: 'string',
            text: 'string',
            created_at: 'date',
            author_id: 'string',
            conversation_id: 'string?',
            in_reply_to_user_id: 'string?',
            lang: 'string?',
            source: 'string?',
            public_metrics: 'object?',
            entities: 'object?',
            referenced_tweets: 'array?'
          }
        }
      }
    },

    // Gmail Syncs
    {
      name: 'gmail-contacts',
      provider: 'gmail',
      models: ['contacts'],
      runs: 'every 6h',
      sync_type: 'full',
      output: {
        schema: {
          contacts: {
            id: 'string',
            name: 'string',
            email: 'string',
            phone: 'string?',
            company: 'string?',
            title: 'string?',
            photo_url: 'string?',
            last_contacted: 'date?',
            groups: 'array?',
            notes: 'string?'
          }
        }
      }
    },
    {
      name: 'gmail-messages',
      provider: 'gmail',
      models: ['messages'],
      runs: 'every 30m',
      sync_type: 'incremental',
      output: {
        schema: {
          messages: {
            id: 'string',
            thread_id: 'string',
            subject: 'string?',
            snippet: 'string?',
            body_html: 'string?',
            body_text: 'string?',
            from: 'object',
            to: 'array',
            cc: 'array?',
            bcc: 'array?',
            date: 'date',
            labels: 'array?',
            attachments: 'array?',
            read: 'boolean?'
          }
        }
      }
    },

    // Outlook Syncs
    {
      name: 'outlook-contacts',
      provider: 'outlook',
      models: ['contacts'],
      runs: 'every 6h',
      sync_type: 'full',
      output: {
        schema: {
          contacts: {
            id: 'string',
            name: 'string',
            email: 'string',
            phone: 'string?',
            company: 'string?',
            title: 'string?',
            photo_url: 'string?',
            last_contacted: 'date?',
            address: 'object?',
            notes: 'string?'
          }
        }
      }
    },
    {
      name: 'outlook-messages',
      provider: 'outlook',
      models: ['messages'],
      runs: 'every 30m',
      sync_type: 'incremental',
      output: {
        schema: {
          messages: {
            id: 'string',
            conversation_id: 'string',
            subject: 'string?',
            preview: 'string?',
            body_html: 'string?',
            body_text: 'string?',
            from: 'object',
            to: 'array',
            cc: 'array?',
            bcc: 'array?',
            received_at: 'date',
            categories: 'array?',
            attachments: 'array?',
            is_read: 'boolean?',
            importance: 'string?'
          }
        }
      }
    }
  ]
};
