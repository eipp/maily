# Maily - apps/web

This directory contains the web module for the Maily platform. It's built with Next.js using the Pages Router architecture (pages/ directory).

## Deployment

The web application is deployed at **app.justmaily.com** and serves as the main interface for the Maily platform.

## Technologies

- Next.js 14+
- React 18+
- TypeScript
- Tailwind CSS
- tldraw for Canvas interface
- Yjs for real-time collaboration
- React Aria for accessible components
- Radix UI for advanced components
- Jest for testing
- Cypress for E2E testing

## Structure

- `pages/`: Main application routes using Pages Router
- `components/`: Reusable React components
- `services/`: API client services
- `hooks/`: Custom React hooks
- `utils/`: Utility functions
- `types/`: TypeScript type definitions
- `tests/`: Unit and integration tests
- `public/`: Static assets
- `contexts/`: React context providers
- `stores/`: State management stores
- `ui/`: UI component library
- `lib/`: Shared libraries and utilities
- `contracts/`: TypeScript interfaces for API contracts

## Canvas Implementation

The Canvas interface is implemented using tldraw as the base framework with the following features:

- **Real-time Collaboration**: Implemented using Yjs and WebSocket integration
- **Multi-agent Assistance**: AI agents provide real-time assistance for content, design, and analytics
- **Split-screen Layout**: Chat interface on the left, visual workspace on the right
- **Content Card System**: Drag-and-drop components for email creation
- **State Persistence**: Canvas state is persisted to the database using Supabase

## Component Structure

The component structure follows a modular approach:

- **Layout Components**: Base layout components for different sections of the application
- **UI Components**: Reusable UI components built with React Aria and Radix UI
- **Feature Components**: Components specific to features like campaigns, contacts, analytics
- **Canvas Components**: Components specific to the Canvas interface
- **Chat Components**: Components for the chat-centric interface

## Development Philosophy

The web application is developed and maintained by a lean team consisting of a founder and an AI coding agent. This approach enables:

- **Rapid UI Evolution**: Quick adaptation to changing requirements and user feedback
- **Consistent Implementation**: AI-enforced coding standards and patterns
- **Comprehensive Component Documentation**: Automated documentation generation and maintenance
- **Efficient Problem Solving**: AI-assisted debugging and optimization
- **Scalable Architecture**: Design patterns that facilitate growth without proportional team expansion

## Accessibility

The web application follows WCAG 2.1 AA guidelines with the following features:

- **Keyboard Navigation**: Full keyboard navigation support
- **Screen Reader Support**: Proper ARIA attributes and screen reader announcements
- **Focus Management**: Proper focus management for modals, dialogs, and other interactive elements
- **Color Contrast**: Sufficient color contrast for all text and UI elements
- **Responsive Design**: Fully responsive design that works on all device sizes

## Development

To run the web application locally:

```bash
cd apps/web
npm install
npm run dev
```

The application will be available at http://localhost:3000.

## Testing

To run tests:

```bash
# Unit and integration tests
npm run test

# E2E tests
npm run cypress

# Accessibility tests
npm run a11y
```
