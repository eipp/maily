# UI Components

This package contains shared UI components used across the Maily platform. These components provide consistent styling, behavior, and accessibility features.

## Features

- Accessible components following WCAG guidelines
- Consistent styling with Tailwind CSS
- Responsive design for all screen sizes
- Thoroughly tested and documented components
- Type-safe with TypeScript

## Component Library

- **Layout components**: Grid, Container, Section
- **Input components**: Button, Input, Select, Checkbox, Radio
- **Display components**: Card, Badge, Alert, Toast
- **Navigation components**: Navbar, Sidebar, Tabs
- **Feedback components**: Spinner, Progress, Skeleton

## Usage

Install the package:

```bash
npm install @maily/ui-components
```

Import and use components:

```tsx
import { Button, Card, Input } from '@maily/ui-components';

function MyComponent() {
  return (
    <Card>
      <Card.Header>My Form</Card.Header>
      <Card.Body>
        <Input label="Name" placeholder="Enter your name" />
        <Button variant="primary">Submit</Button>
      </Card.Body>
    </Card>
  );
}
```

## Component Development

Each component should:
1. Be fully accessible
2. Support dark mode
3. Be responsive
4. Include tests
5. Include Storybook stories
6. Be thoroughly documented

## Adding New Components

When adding new components:
1. Create the component in the appropriate directory
2. Create tests for the component
3. Create Storybook stories
4. Document the component API
5. Export the component from the package