# Maily UI Package

The UI package provides a comprehensive design system and component library for Maily applications, built with React and Tailwind CSS.

## Features

- **Component Library**: Reusable React components
- **Design System**: Consistent visual language
- **Accessibility**: WCAG 2.1 AA compliant components
- **Theming**: Customizable color schemes and branding
- **Dark Mode Support**: Built-in light and dark themes
- **Responsive Design**: Mobile-first approach
- **Form Components**: Validated form inputs and controls
- **Data Display**: Tables, charts, and data visualization
- **Animations**: Smooth transitions and interactions

## Installation

```bash
pnpm add @maily/ui
```

## Usage

```tsx
import { Button, Card, Input, Select } from '@maily/ui';

function CampaignForm() {
  return (
    <Card>
      <Card.Header>
        <h2>Create New Campaign</h2>
      </Card.Header>
      <Card.Body>
        <div className="space-y-4">
          <Input
            label="Campaign Name"
            placeholder="Enter campaign name"
            required
          />

          <Select
            label="Campaign Type"
            options={[
              { value: 'newsletter', label: 'Newsletter' },
              { value: 'onboarding', label: 'Onboarding Sequence' },
              { value: 'promotional', label: 'Promotional' }
            ]}
          />

          <div className="flex justify-end gap-2">
            <Button variant="outline">Cancel</Button>
            <Button>Create Campaign</Button>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
}
```

## Component Categories

### Layout
- `Box` - Basic container
- `Card` - Content container with header, body, footer
- `Container` - Responsive page container
- `Flex` - Flexbox container
- `Grid` - CSS Grid container
- `Stack` - Vertical or horizontal stack

### Forms
- `Button` - Action buttons with variants
- `Checkbox` - Single checkbox or checkbox group
- `Input` - Text input fields
- `Radio` - Radio button group
- `Select` - Dropdown select component
- `Switch` - Toggle switch component
- `Textarea` - Multi-line text input
- `DatePicker` - Date selection component
- `Form` - Form wrapper with validation

### Data Display
- `Table` - Data table with sorting and pagination
- `Badge` - Status indicators
- `Avatar` - User avatars with fallbacks
- `Tag` - Categorization labels
- `Chart` - Data visualization
- `Progress` - Progress indicators

### Feedback
- `Alert` - Contextual feedback messages
- `Toast` - Temporary notifications
- `Skeleton` - Loading state placeholders
- `Spinner` - Loading indicator

### Navigation
- `Breadcrumb` - Page location indicator
- `Tabs` - Content organization with tabs
- `Pagination` - Page navigation for content
- `Dropdown` - Contextual dropdown menu
- `Sidebar` - Application navigation sidebar

## Theming

Customize the UI theme in your application:

```tsx
import { ThemeProvider } from '@maily/ui';

function App() {
  return (
    <ThemeProvider
      theme={{
        colors: {
          primary: '#0070f3',
          secondary: '#ff4081',
          // ...other color overrides
        }
      }}
    >
      <YourApplication />
    </ThemeProvider>
  );
}
```

## Documentation

For full component documentation and examples, run the Storybook:

```bash
pnpm --filter @maily/ui storybook
```

## Dependencies

- react
- react-dom
- tailwindcss
- class-variance-authority
- radix-ui
- framer-motion
- date-fns
- react-hook-form
- zod
