# Maily Email Renderer Package

The email-renderer package provides components and utilities for creating, rendering, and testing email templates with React components.

## Features

- **React Email Components**: Build emails using React components
- **Template System**: Reusable email templates with variable substitution
- **MJML Integration**: Use MJML for responsive email layouts
- **Personalization**: Dynamic content based on recipient data
- **Preview Mode**: In-app preview of email templates
- **Test Rendering**: Test email rendering across different email clients
- **Image Processing**: Automated image optimization for emails
- **Spam Score Testing**: Check email content against spam filters

## Installation

```bash
pnpm add @maily/email-renderer
```

## Usage

```tsx
import {
  EmailTemplate,
  EmailHeader,
  EmailBody,
  EmailFooter,
  renderToHtml
} from '@maily/email-renderer';

// Create an email template using React components
const WelcomeEmail = ({ userName, activationLink }) => (
  <EmailTemplate>
    <EmailHeader logo="https://example.com/logo.png" />
    <EmailBody>
      <h1>Welcome, {userName}!</h1>
      <p>Thank you for signing up for Maily.</p>
      <button href={activationLink}>Activate Your Account</button>
    </EmailBody>
    <EmailFooter
      companyName="Maily Inc."
      unsubscribeLink="https://example.com/unsubscribe"
    />
  </EmailTemplate>
);

// Render email to HTML
const html = renderToHtml(
  <WelcomeEmail
    userName="John Doe"
    activationLink="https://example.com/activate/123"
  />
);
```

## Components

The package includes the following components:

- **EmailTemplate**: Base container for emails
- **EmailHeader**: Email header with logo and navigation
- **EmailBody**: Main content area
- **EmailFooter**: Footer with compliance links and information
- **Button**: Styled button for email CTAs
- **Divider**: Horizontal divider
- **Image**: Responsive image component
- **Section**: Content section with background and padding
- **Column**: Layout column for multi-column layouts
- **Text**: Text component with styling options

## Testing

Test email rendering using the included testing utilities:

```typescript
import { testEmailRendering } from '@maily/email-renderer/testing';

const testResults = await testEmailRendering(html, {
  clients: ['gmail', 'outlook', 'apple-mail'],
  devices: ['desktop', 'mobile'],
});
```

## Dependencies

- react
- react-dom
- mjml
- juice
- email-templates
