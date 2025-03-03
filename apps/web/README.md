# JustMaily Web Interface

This is the web interface for JustMaily, an enterprise-grade email marketing platform with AI-powered features.

## Features

- **Hybrid Interface**: Split-screen layout with chat interface and canvas workspace
- **AI Mesh Network**: Multiple specialized AI agents working together
- **Operational Modes**: Content Creation, Campaign Flow, Analytics, and Audience
- **Real-Time Collaboration**: Multi-user editing with presence awareness
- **Trust Verification**: Blockchain-based verification for email campaigns

## Tech Stack

- **Frontend Framework**: Next.js 14.1.0+ with App Router
- **UI Library**: React 18.2.0+ with TypeScript 5.3.0+
- **Styling**: Tailwind CSS 3.4.0+ with shadcn/ui components
- **State Management**: React Context, SWR, and Zustand
- **AI Integration**: Claude 3.7 Sonnet, GPT-4o, and Gemini 2.0

## Getting Started

### Prerequisites

- Node.js 18.x or later
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Run the development server
npm run dev
```

### Build

```bash
# Build for production
npm run build

# Start the production server
npm start
```

## Project Structure

- `/app`: Next.js App Router pages and layouts
- `/components`: React components organized by feature
  - `/ai-mesh`: AI agent components
  - `/analytics`: Analytics and reporting components
  - `/canvas`: Email editor canvas components
  - `/chat`: Chat interface components
  - `/layout`: Layout components
  - `/modes`: Operational mode components
  - `/navigation`: Navigation components
  - `/ui`: Reusable UI components
- `/lib`: Utility functions and shared code
- `/public`: Static assets

## Performance Optimization

The application is optimized for performance with:

- Server-side rendering with Next.js
- Code splitting and lazy loading
- Image optimization
- Efficient state management
- Hardware-accelerated animations

## Accessibility

The application follows WCAG 2.1 AA guidelines with:

- Semantic HTML structure
- ARIA attributes where necessary
- Keyboard navigation
- Sufficient color contrast
- Screen reader support
- Reduced motion options

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
