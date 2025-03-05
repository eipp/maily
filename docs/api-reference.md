# Maily API Reference

This comprehensive API reference documentation covers all the endpoints available in the Maily API. The API is organized around REST principles and returns JSON-encoded responses. All API requests must be authenticated unless explicitly specified.

## Base URL

All API requests should be made to the following base URL:

```
https://api.maily.com/v1
```

## Authentication

Maily API uses API keys for authentication. You can manage your API keys in the Maily dashboard. Include your API key in all requests as follows:

```
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

API requests are rate-limited to ensure fair usage and system stability. Current limits are:

- 100 requests per minute for standard accounts
- 1,000 requests per minute for premium accounts

When rate limits are exceeded, the API will return a `429 Too Many Requests` response with a `Retry-After` header indicating when you can resume making requests.

## Error Handling

Maily API uses conventional HTTP response codes to indicate the success or failure of an API request:

- `2xx` - Success
- `4xx` - Client error (validation error, authentication error, etc.)
- `5xx` - Server error

All error responses have a consistent format:

```json
{
  "error": {
    "type": "validation_error",
    "message": "The email field is required",
    "code": "FIELD_REQUIRED",
    "details": {
      "field": "email"
    },
    "request_id": "req_1234567890"
  }
}
```

## Pagination

List endpoints support pagination through the `limit` and `cursor` parameters:

- `limit` - Number of records to return (default: 25, max: 100)
- `cursor` - Cursor for pagination (obtained from previous response)

Paginated responses include a `pagination` object:

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "cursor_123456",
    "has_more": true
  }
}
```

## API Endpoints

### Contacts

#### List Contacts

```
GET /contacts
```

Retrieve a paginated list of contacts.

**Query Parameters:**

| Parameter   | Description                                          |
|-------------|------------------------------------------------------|
| limit       | Number of contacts to return (default: 25, max: 100) |
| cursor      | Cursor for pagination                                |
| status      | Filter by status (active, inactive, unsubscribed)    |
| list_id     | Filter by list ID                                    |
| tag         | Filter by tag                                        |
| created_after | Filter by creation date (ISO 8601)                 |
| search      | Search term to filter contacts                       |

**Response:**

```json
{
  "data": [
    {
      "id": "cnt_123456789",
      "email": "john@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "status": "active",
      "tags": ["customer", "newsletter"],
      "createdAt": "2023-01-15T18:30:00Z",
      "updatedAt": "2023-01-15T18:30:00Z"
    },
    // ...
  ],
  "pagination": {
    "next_cursor": "cursor_123456",
    "has_more": true
  }
}
```

#### Create Contact

```
POST /contacts
```

Create a new contact.

**Request Body:**

```json
{
  "email": "jane@example.com",
  "firstName": "Jane",
  "lastName": "Smith",
  "status": "active",
  "tags": ["prospect"],
  "customFields": [
    {
      "key": "company",
      "value": "Acme Inc"
    }
  ],
  "listIds": ["list_123456"]
}
```

**Response:**

```json
{
  "data": {
    "id": "cnt_123456790",
    "email": "jane@example.com",
    "firstName": "Jane",
    "lastName": "Smith",
    "status": "active",
    "tags": ["prospect"],
    "customFields": [
      {
        "key": "company",
        "value": "Acme Inc"
      }
    ],
    "listIds": ["list_123456"],
    "createdAt": "2023-05-20T14:15:30Z",
    "updatedAt": "2023-05-20T14:15:30Z"
  }
}
```

#### Get Contact

```
GET /contacts/:id
```

Retrieve a specific contact by ID.

**Response:**

```json
{
  "data": {
    "id": "cnt_123456789",
    "email": "john@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "fullName": "John Doe",
    "status": "active",
    "source": "api",
    "tags": ["customer", "newsletter"],
    "listIds": ["list_123456", "list_789012"],
    "customFields": [
      {
        "key": "company",
        "value": "Example Inc"
      }
    ],
    "consent": {
      "marketing": true,
      "transactional": true,
      "thirdParty": false,
      "timestamp": "2023-01-15T18:30:00Z"
    },
    "lastActivity": "2023-05-18T09:45:12Z",
    "createdAt": "2023-01-15T18:30:00Z",
    "updatedAt": "2023-05-18T09:45:12Z"
  }
}
```

#### Update Contact

```
PATCH /contacts/:id
```

Update an existing contact.

**Request Body:**

```json
{
  "firstName": "Jonathan",
  "tags": ["customer", "newsletter", "vip"]
}
```

**Response:**

```json
{
  "data": {
    "id": "cnt_123456789",
    "email": "john@example.com",
    "firstName": "Jonathan",
    "lastName": "Doe",
    "status": "active",
    "tags": ["customer", "newsletter", "vip"],
    // ...other fields
    "updatedAt": "2023-05-20T15:10:25Z"
  }
}
```

#### Delete Contact

```
DELETE /contacts/:id
```

Delete a contact.

**Response:**

```json
{
  "data": {
    "deleted": true,
    "id": "cnt_123456789"
  }
}
```

### Lists

#### List Contact Lists

```
GET /lists
```

Retrieve a paginated list of contact lists.

**Query Parameters:**

| Parameter   | Description                                   |
|-------------|-----------------------------------------------|
| limit       | Number of lists to return (default: 25)       |
| cursor      | Cursor for pagination                         |
| search      | Search term to filter lists                   |

**Response:**

```json
{
  "data": [
    {
      "id": "list_123456",
      "name": "Newsletter Subscribers",
      "description": "People who subscribed to our newsletter",
      "contactCount": 1250,
      "createdAt": "2023-01-10T18:30:00Z",
      "updatedAt": "2023-05-19T12:30:00Z"
    },
    // ...
  ],
  "pagination": {
    "next_cursor": "cursor_789012",
    "has_more": true
  }
}
```

#### Create List

```
POST /lists
```

Create a new contact list.

**Request Body:**

```json
{
  "name": "Product Updates",
  "description": "Customers interested in product updates"
}
```

**Response:**

```json
{
  "data": {
    "id": "list_789013",
    "name": "Product Updates",
    "description": "Customers interested in product updates",
    "contactCount": 0,
    "createdAt": "2023-05-20T15:30:00Z",
    "updatedAt": "2023-05-20T15:30:00Z"
  }
}
```

#### Get List

```
GET /lists/:id
```

Retrieve a specific list.

**Response:**

```json
{
  "data": {
    "id": "list_123456",
    "name": "Newsletter Subscribers",
    "description": "People who subscribed to our newsletter",
    "contactCount": 1250,
    "createdAt": "2023-01-10T18:30:00Z",
    "updatedAt": "2023-05-19T12:30:00Z"
  }
}
```

#### Update List

```
PATCH /lists/:id
```

Update an existing list.

**Request Body:**

```json
{
  "name": "Weekly Newsletter Subscribers",
  "description": "People who subscribed to our weekly newsletter"
}
```

**Response:**

```json
{
  "data": {
    "id": "list_123456",
    "name": "Weekly Newsletter Subscribers",
    "description": "People who subscribed to our weekly newsletter",
    "contactCount": 1250,
    "createdAt": "2023-01-10T18:30:00Z",
    "updatedAt": "2023-05-20T15:45:00Z"
  }
}
```

#### Delete List

```
DELETE /lists/:id
```

Delete a list (does not delete contacts).

**Response:**

```json
{
  "data": {
    "deleted": true,
    "id": "list_123456"
  }
}
```

#### Add Contacts to List

```
POST /lists/:id/contacts
```

Add contacts to a list.

**Request Body:**

```json
{
  "contactIds": [
    "cnt_123456789",
    "cnt_123456790"
  ]
}
```

**Response:**

```json
{
  "data": {
    "added": 2,
    "listId": "list_123456"
  }
}
```

#### Remove Contacts from List

```
DELETE /lists/:id/contacts
```

Remove contacts from a list.

**Request Body:**

```json
{
  "contactIds": [
    "cnt_123456789"
  ]
}
```

**Response:**

```json
{
  "data": {
    "removed": 1,
    "listId": "list_123456"
  }
}
```

### Campaigns

#### List Campaigns

```
GET /campaigns
```

Retrieve a paginated list of campaigns.

**Query Parameters:**

| Parameter   | Description                                      |
|-------------|--------------------------------------------------|
| limit       | Number of campaigns to return (default: 25)      |
| cursor      | Cursor for pagination                            |
| status      | Filter by status (draft, scheduled, sent, etc.)  |
| search      | Search term to filter campaigns                  |

**Response:**

```json
{
  "data": [
    {
      "id": "camp_123456",
      "name": "May Newsletter",
      "subject": "Your May Newsletter",
      "status": "sent",
      "sentAt": "2023-05-15T09:00:00Z",
      "openRate": 0.42,
      "clickRate": 0.12,
      "recipientCount": 1200,
      "createdAt": "2023-05-10T14:30:00Z",
      "updatedAt": "2023-05-15T09:00:00Z"
    },
    // ...
  ],
  "pagination": {
    "next_cursor": "cursor_345678",
    "has_more": true
  }
}
```

#### Create Campaign

```
POST /campaigns
```

Create a new campaign.

**Request Body:**

```json
{
  "name": "June Newsletter",
  "subject": "Your June Newsletter",
  "fromName": "Maily Team",
  "fromEmail": "newsletter@maily.com",
  "replyTo": "support@maily.com",
  "templateId": "tmpl_123456",
  "listIds": ["list_123456"],
  "scheduledAt": "2023-06-15T09:00:00Z"
}
```

**Response:**

```json
{
  "data": {
    "id": "camp_234567",
    "name": "June Newsletter",
    "subject": "Your June Newsletter",
    "fromName": "Maily Team",
    "fromEmail": "newsletter@maily.com",
    "replyTo": "support@maily.com",
    "templateId": "tmpl_123456",
    "listIds": ["list_123456"],
    "scheduledAt": "2023-06-15T09:00:00Z",
    "status": "scheduled",
    "recipientCount": 1250,
    "createdAt": "2023-05-20T16:00:00Z",
    "updatedAt": "2023-05-20T16:00:00Z"
  }
}
```

#### Get Campaign

```
GET /campaigns/:id
```

Retrieve a specific campaign.

**Response:**

```json
{
  "data": {
    "id": "camp_123456",
    "name": "May Newsletter",
    "subject": "Your May Newsletter",
    "fromName": "Maily Team",
    "fromEmail": "newsletter@maily.com",
    "replyTo": "support@maily.com",
    "templateId": "tmpl_123456",
    "listIds": ["list_123456"],
    "status": "sent",
    "sentAt": "2023-05-15T09:00:00Z",
    "openRate": 0.42,
    "clickRate": 0.12,
    "recipientCount": 1200,
    "analytics": {
      "sent": 1200,
      "delivered": 1180,
      "opened": 504,
      "clicked": 144,
      "bounced": 20,
      "unsubscribed": 5
    },
    "createdAt": "2023-05-10T14:30:00Z",
    "updatedAt": "2023-05-15T09:00:00Z"
  }
}
```

#### Update Campaign

```
PATCH /campaigns/:id
```

Update an existing campaign (only allowed for draft or scheduled campaigns).

**Request Body:**

```json
{
  "name": "June Newsletter - Special Edition",
  "subject": "Your Special June Newsletter",
  "scheduledAt": "2023-06-16T09:00:00Z"
}
```

**Response:**

```json
{
  "data": {
    "id": "camp_234567",
    "name": "June Newsletter - Special Edition",
    "subject": "Your Special June Newsletter",
    "fromName": "Maily Team",
    "fromEmail": "newsletter@maily.com",
    "replyTo": "support@maily.com",
    "templateId": "tmpl_123456",
    "listIds": ["list_123456"],
    "scheduledAt": "2023-06-16T09:00:00Z",
    "status": "scheduled",
    "recipientCount": 1250,
    "createdAt": "2023-05-20T16:00:00Z",
    "updatedAt": "2023-05-20T16:15:00Z"
  }
}
```

#### Cancel Campaign

```
POST /campaigns/:id/cancel
```

Cancel a scheduled campaign.

**Response:**

```json
{
  "data": {
    "id": "camp_234567",
    "status": "cancelled",
    "updatedAt": "2023-05-20T16:30:00Z"
  }
}
```

#### Send Campaign

```
POST /campaigns/:id/send
```

Send a draft campaign immediately or schedule it.

**Request Body:**

```json
{
  "scheduledAt": "2023-06-16T09:00:00Z"  // Optional, if not provided, sends immediately
}
```

**Response:**

```json
{
  "data": {
    "id": "camp_234567",
    "status": "scheduled",
    "scheduledAt": "2023-06-16T09:00:00Z",
    "updatedAt": "2023-05-20T16:45:00Z"
  }
}
```

### Templates

#### List Templates

```
GET /templates
```

Retrieve a paginated list of templates.

**Query Parameters:**

| Parameter   | Description                                      |
|-------------|--------------------------------------------------|
| limit       | Number of templates to return (default: 25)      |
| cursor      | Cursor for pagination                            |
| category    | Filter by category                               |
| search      | Search term to filter templates                  |

**Response:**

```json
{
  "data": [
    {
      "id": "tmpl_123456",
      "name": "Newsletter - Basic",
      "category": "newsletter",
      "thumbnail": "https://assets.maily.com/thumbnails/tmpl_123456.png",
      "createdAt": "2023-01-05T10:30:00Z",
      "updatedAt": "2023-05-10T14:15:00Z"
    },
    // ...
  ],
  "pagination": {
    "next_cursor": "cursor_456789",
    "has_more": true
  }
}
```

#### Create Template

```
POST /templates
```

Create a new template.

**Request Body:**

```json
{
  "name": "Product Announcement",
  "category": "announcement",
  "html": "<html><body><h1>{{title}}</h1><p>{{content}}</p></body></html>",
  "variables": {
    "title": {
      "type": "string",
      "defaultValue": "New Product"
    },
    "content": {
      "type": "string",
      "defaultValue": "We're excited to announce our new product!"
    }
  }
}
```

**Response:**

```json
{
  "data": {
    "id": "tmpl_345678",
    "name": "Product Announcement",
    "category": "announcement",
    "html": "<html><body><h1>{{title}}</h1><p>{{content}}</p></body></html>",
    "variables": {
      "title": {
        "type": "string",
        "defaultValue": "New Product"
      },
      "content": {
        "type": "string",
        "defaultValue": "We're excited to announce our new product!"
      }
    },
    "thumbnail": "https://assets.maily.com/thumbnails/tmpl_345678.png",
    "createdAt": "2023-05-20T17:00:00Z",
    "updatedAt": "2023-05-20T17:00:00Z"
  }
}
```

#### Get Template

```
GET /templates/:id
```

Retrieve a specific template.

**Response:**

```json
{
  "data": {
    "id": "tmpl_123456",
    "name": "Newsletter - Basic",
    "category": "newsletter",
    "html": "<html><body><h1>{{title}}</h1><div>{{content}}</div></body></html>",
    "variables": {
      "title": {
        "type": "string",
        "defaultValue": "Monthly Newsletter"
      },
      "content": {
        "type": "rich_text",
        "defaultValue": "<p>Welcome to our newsletter!</p>"
      }
    },
    "thumbnail": "https://assets.maily.com/thumbnails/tmpl_123456.png",
    "createdAt": "2023-01-05T10:30:00Z",
    "updatedAt": "2023-05-10T14:15:00Z"
  }
}
```

#### Update Template

```
PATCH /templates/:id
```

Update an existing template.

**Request Body:**

```json
{
  "name": "Newsletter - Enhanced",
  "html": "<html><body><h1>{{title}}</h1><div>{{content}}</div><footer>{{footer}}</footer></body></html>",
  "variables": {
    "title": {
      "type": "string",
      "defaultValue": "Monthly Newsletter"
    },
    "content": {
      "type": "rich_text",
      "defaultValue": "<p>Welcome to our newsletter!</p>"
    },
    "footer": {
      "type": "string",
      "defaultValue": "© 2023 Maily"
    }
  }
}
```

**Response:**

```json
{
  "data": {
    "id": "tmpl_123456",
    "name": "Newsletter - Enhanced",
    "category": "newsletter",
    "html": "<html><body><h1>{{title}}</h1><div>{{content}}</div><footer>{{footer}}</footer></body></html>",
    "variables": {
      "title": {
        "type": "string",
        "defaultValue": "Monthly Newsletter"
      },
      "content": {
        "type": "rich_text",
        "defaultValue": "<p>Welcome to our newsletter!</p>"
      },
      "footer": {
        "type": "string",
        "defaultValue": "© 2023 Maily"
      }
    },
    "thumbnail": "https://assets.maily.com/thumbnails/tmpl_123456.png",
    "createdAt": "2023-01-05T10:30:00Z",
    "updatedAt": "2023-05-20T17:15:00Z"
  }
}
```

#### Delete Template

```
DELETE /templates/:id
```

Delete a template.

**Response:**

```json
{
  "data": {
    "deleted": true,
    "id": "tmpl_123456"
  }
}
```

#### Render Template

```
POST /templates/:id/render
```

Render a template with provided variables.

**Request Body:**

```json
{
  "variables": {
    "title": "May Newsletter",
    "content": "<p>Here are our updates for May...</p>"
  }
}
```

**Response:**

```json
{
  "data": {
    "html": "<html><body><h1>May Newsletter</h1><div><p>Here are our updates for May...</p></div></body></html>"
  }
}
```

### Analytics

#### Overview

```
GET /analytics/overview
```

Get an overview of analytics data.

**Query Parameters:**

| Parameter   | Description                                      |
|-------------|--------------------------------------------------|
| startDate   | Start date for data (ISO 8601)                   |
| endDate     | End date for data (ISO 8601)                     |
| interval    | Data interval (day, week, month)                 |

**Response:**

```json
{
  "data": {
    "contactGrowth": {
      "total": 12500,
      "growth": 0.15,
      "history": [
        {
          "date": "2023-05-01",
          "count": 12000
        },
        {
          "date": "2023-05-15",
          "count": 12250
        },
        {
          "date": "2023-05-31",
          "count": 12500
        }
      ]
    },
    "emailPerformance": {
      "sent": 25000,
      "delivered": 24500,
      "opened": 10000,
      "clicked": 2500,
      "bounced": 500,
      "unsubscribed": 100,
      "openRate": 0.4,
      "clickRate": 0.1,
      "bounceRate": 0.02,
      "unsubscribeRate": 0.004
    },
    "topCampaigns": [
      {
        "id": "camp_123456",
        "name": "May Newsletter",
        "openRate": 0.45,
        "clickRate": 0.15
      },
      {
        "id": "camp_123457",
        "name": "Product Launch",
        "openRate": 0.55,
        "clickRate": 0.25
      }
    ]
  }
}
```

#### Campaign Performance

```
GET /analytics/campaigns/:id/performance
```

Get performance data for a specific campaign.

**Query Parameters:**

| Parameter   | Description                                      |
|-------------|--------------------------------------------------|
| metrics     | Specific metrics to include (comma-separated)    |

**Response:**

```json
{
  "data": {
    "id": "camp_123456",
    "name": "May Newsletter",
    "sent": 1200,
    "delivered": 1180,
    "opened": 504,
    "clicked": 144,
    "bounced": 20,
    "unsubscribed": 5,
    "openRate": 0.42,
    "clickRate": 0.12,
    "bounceRate": 0.017,
    "unsubscribeRate": 0.004,
    "topLinks": [
      {
        "url": "https://example.com/product",
        "clicks": 80,
        "clickRate": 0.067
      },
      {
        "url": "https://example.com/blog",
        "clicks": 45,
        "clickRate": 0.038
      }
    ],
    "timeline": {
      "opens": [
        {
          "date": "2023-05-15T09:00:00Z",
          "count": 200
        },
        {
          "date": "2023-05-15T12:00:00Z",
          "count": 150
        },
        {
          "date": "2023-05-15T15:00:00Z",
          "count": 100
        },
        {
          "date": "2023-05-15T18:00:00Z",
          "count": 54
        }
      ],
      "clicks": [
        {
          "date": "2023-05-15T09:00:00Z",
          "count": 60
        },
        {
          "date": "2023-05-15T12:00:00Z",
          "count": 40
        },
        {
          "date": "2023-05-15T15:00:00Z",
          "count": 30
        },
        {
          "date": "2023-05-15T18:00:00Z",
          "count": 14
        }
      ]
    }
  }
}
```

#### Contact Activity

```
GET /analytics/contacts/:id/activity
```

Get activity data for a specific contact.

**Query Parameters:**

| Parameter   | Description                                         |
|-------------|-----------------------------------------------------|
| limit       | Number of activities to return (default: 25)        |
| cursor      | Cursor for pagination                               |
| activityType | Filter by activity type (open, click, etc.)         |

**Response:**

```json
{
  "data": {
    "id": "cnt_123456789",
    "email": "john@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "activities": [
      {
        "type": "email_open",
        "timestamp": "2023-05-15T10:30:45Z",
        "campaignId": "camp_123456",
        "campaignName": "May Newsletter"
      },
      {
        "type": "email_click",
        "timestamp": "2023-05-15T10:31:20Z",
        "campaignId": "camp_123456",
        "campaignName": "May Newsletter",
        "metadata": {
          "url": "https://example.com/product"
        }
      },
      {
        "type": "email_open",
        "timestamp": "2023-05-01T14:20:10Z",
        "campaignId": "camp_123455",
        "campaignName": "April Newsletter"
      }
    ],
    "metrics": {
      "openRate": 0.75,
      "clickRate": 0.25,
      "engagement": 0.65
    }
  },
  "pagination": {
    "next_cursor": "cursor_567890",
    "has_more": true
  }
}
```

### AI Services

#### Generate Subject Lines

```
POST /ai/subject-lines
```

Generate email subject line suggestions.

**Request Body:**

```json
{
  "campaignType": "newsletter",
  "content": "Monthly update on new product features, including improved analytics dashboard and mobile app enhancements.",
  "count": 5
}
```

**Response:**

```json
{
  "data": {
    "subjectLines": [
      {
        "text": "📊 New Analytics Dashboard & Mobile Updates | May Newsletter",
        "score": 0.92,
        "metrics": {
          "estimated_open_rate": 0.35,
          "estimated_click_rate": 0.12
        }
      },
      {
        "text": "Your May Updates: Enhanced Analytics & Mobile Improvements",
        "score": 0.89,
        "metrics": {
          "estimated_open_rate": 0.33,
          "estimated_click_rate": 0.11
        }
      },
      {
        "text": "See What's New: Analytics Dashboard & Mobile App Enhancements",
        "score": 0.87,
        "metrics": {
          "estimated_open_rate": 0.32,
          "estimated_click_rate": 0.10
        }
      },
      {
        "text": "May Product Update: Better Analytics, Better Mobile Experience",
        "score": 0.85,
        "metrics": {
          "estimated_open_rate": 0.31,
          "estimated_click_rate": 0.09
        }
      },
      {
        "text": "Unlock New Insights with Our Updated Analytics Dashboard",
        "score": 0.82,
        "metrics": {
          "estimated_open_rate": 0.29,
          "estimated_click_rate": 0.08
        }
      }
    ]
  }
}
```

#### Generate Email Content

```
POST /ai/content
```

Generate email content.

**Request Body:**

```json
{
  "type": "product_announcement",
  "product": {
    "name": "Analytics Dashboard 2.0",
    "description": "Improved analytics dashboard with real-time data and advanced filtering",
    "features": [
      "Real-time data updates",
      "Advanced filtering and segmentation",
      "Customizable dashboards",
      "Export to multiple formats"
    ],
    "releaseDate": "2023-06-01"
  },
  "tone": "professional",
  "length": "medium"
}
```

**Response:**

```json
{
  "data": {
    "subject": "Introducing Analytics Dashboard 2.0: Real-time Insights & More",
    "content": "<h1>Introducing Analytics Dashboard 2.0</h1><p>We're excited to announce the release of our new Analytics Dashboard 2.0, available on June 1, 2023.</p><p>Our next-generation dashboard brings you:</p><ul><li><strong>Real-time data updates</strong>: See your metrics update instantly as new data comes in</li><li><strong>Advanced filtering and segmentation</strong>: Slice and dice your data with precision</li><li><strong>Customizable dashboards</strong>: Create the perfect view for your needs</li><li><strong>Export to multiple formats</strong>: Share insights in PDF, CSV, or Excel format</li></ul><p>Ready to try it? <a href=\"#\">Upgrade now</a> to experience the power of real-time analytics.</p>",
    "tone": "professional",
    "metrics": {
      "estimated_open_rate": 0.38,
      "estimated_click_rate": 0.15,
      "estimated_readability": 0.95
    }
  }
}
```

#### Analyze Campaign Performance

```
POST /ai/campaign-analysis
```

Get AI-powered analysis of campaign performance.

**Request Body:**

```json
{
  "campaignId": "camp_123456"
}
```

**Response:**

```json
{
  "data": {
    "summary": "Your May Newsletter performed above average with a 42% open rate (industry average: 25%) and a 12% click rate (industry average: 3.5%). The email performed particularly well with the 25-34 age demographic and mobile users.",
    "strengths": [
      "Strong open rate (42%) compared to industry average (25%)",
      "Excellent click rate (12%) compared to industry average (3.5%)",
      "Mobile engagement was 20% higher than your previous campaigns"
    ],
    "areas_for_improvement": [
      "Desktop engagement was slightly below average",
      "Lower performance in the 55+ age demographic",
      "Second link received minimal clicks (2.1%)"
    ],
    "recommendations": [
      "Continue with similar subject line styles which drove high open rates",
      "Consider more engaging content for desktop users",
      "Create targeted content for the 55+ demographic",
      "Replace or reposition the second link to improve visibility"
    ]
  }
}
```

#### Cognitive Canvas

```
POST /ai/canvas/render
```

Generate HTML content from Cognitive Canvas design.

**Request Body:**

```json
{
  "canvasId": "cnv_123456",
  "format": "html",
  "options": {
    "responsiveDesign": true,
    "darkModeSupport": false
  }
}
```

**Response:**

```json
{
  "data": {
    "html": "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><style>/* CSS styles */</style></head><body><!-- Generated HTML content --></body></html>",
    "verification": {
      "verified": true,
      "verificationId": "ver_789012",
      "timestamp": "2023-05-20T18:30:00Z",
      "score": 0.98
    }
  }
}
```

## Webhooks

Maily provides webhooks to notify your application when events occur in your account. To set up a webhook, go to the Webhook section in your account settings.

### Webhook Events

The following events are supported:

| Event                      | Description                                          |
|----------------------------|------------------------------------------------------|
| contact.created            | A new contact was created                            |
| contact.updated            | A contact was updated                                |
| contact.deleted            | A contact was deleted                                |
| campaign.sent              | A campaign was sent                                  |
| campaign.delivered         | A campaign was delivered to a recipient              |
| campaign.opened            | A recipient opened a campaign                        |
| campaign.clicked           | A recipient clicked a link in a campaign             |
| campaign.bounced           | A campaign bounced                                   |
| campaign.unsubscribed      | A recipient unsubscribed from a campaign             |
| campaign.complained        | A recipient marked a campaign as spam                |

### Webhook Payload

Webhook payloads are delivered as HTTP POST requests with JSON bodies:

```json
{
  "event": "contact.updated",
  "occurred_at": "2023-05-20T15:10:25Z",
  "data": {
    "id": "cnt_123456789",
    "email": "john@example.com",
    "firstName": "Jonathan",
    "lastName": "Doe",
    "status": "active",
    "tags": ["customer", "newsletter", "vip"],
    // ...other fields
    "updatedAt": "2023-05-20T15:10:25Z"
  }
}
```

### Webhook Security

Webhook requests include a signature header `X-Maily-Signature` that you can use to verify the request came from Maily. The signature is a HMAC SHA-256 hex digest of the request body, using your webhook secret as the key.

## SDKs and Client Libraries

Maily provides official client libraries for several programming languages:

- [JavaScript/TypeScript](https://github.com/maily/maily-js)
- [Python](https://github.com/maily/maily-python)
- [PHP](https://github.com/maily/maily-php)
- [Ruby](https://github.com/maily/maily-ruby)
- [Go](https://github.com/maily/maily-go)
- [Java](https://github.com/maily/maily-java)

## API Status and Support

For API status updates, please check our [status page](https://status.maily.com).

If you need help with the API, please contact [api-support@maily.com](mailto:api-support@maily.com) or visit our [API documentation](https://docs.maily.com/api).