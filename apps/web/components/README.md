# Maily Web Application Components

This directory contains app-specific components for the Maily web application.

## Component Organization

The components in this directory are organized by feature or domain:

```
components/
├── Auth/                  # Authentication-related components
├── Dashboard/             # Dashboard-specific components
├── Email/                 # Email-related components
├── Canvas/                # Email canvas editor components
├── Settings/              # Settings-related components
├── Layout/                # Layout components specific to the web app
├── Analytics/             # Analytics and reporting components
├── Common/                # App-specific common components
└── AI/                    # AI feature components
```

## When to Create Components Here

Create components in this directory when:

1. The component is specific to the Maily web application
2. The component depends on application-specific state or logic
3. The component is a composition of multiple shared UI components for a specific use case

## When to Use Shared UI Components

For generic, reusable UI components that are not specific to the Maily web application, use components from the `packages/ui` package.

## Component Structure

Each component should follow this structure:

```
ComponentName/
├── ComponentName.tsx      # Component implementation
├── ComponentName.test.tsx # Component tests
├── ComponentName.module.css (optional) # Component-specific styles
└── index.ts               # Export file
```

## State Management

Components in this directory can use:

1. **Local State**: For component-specific state using React's `useState` and `useReducer`
2. **Context API**: For state that needs to be shared between components in a specific feature
3. **Global State**: For application-wide state using the chosen state management solution

## Canvas Components

Canvas components for the email editor should follow the patterns established in the `Canvas/` directory:

1. Use the fabric.js integration patterns
2. Follow the component hierarchy established in `Canvas/EmailEditor.tsx`
3. Implement proper event handling for canvas interactions

## AI Feature Components

AI feature components should:

1. Use the AI service interfaces defined in the API
2. Implement proper loading and error states
3. Follow the established patterns for AI-driven UI components

## Testing

All components should have tests that:

1. Verify the component renders correctly
2. Test user interactions
3. Test component state changes
4. Mock external dependencies

## Styling

Components should use:

1. **Tailwind CSS**: For utility-based styling
2. **CSS Modules**: For component-specific styles that can't be achieved with Tailwind
3. **Theme Variables**: For consistent theming across the application

## Accessibility

All components should:

1. Have appropriate ARIA attributes
2. Be keyboard navigable
3. Have proper focus management
4. Support screen readers
5. Have sufficient color contrast
