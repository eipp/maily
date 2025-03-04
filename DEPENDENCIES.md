# Maily Dependencies Management

## Overview

This document consolidates information about Maily's dependencies, update processes, and current status. Use this as your reference for dependency management in the project.

## Current Status (March 2025)

- **Total target packages**: 34
- **✅ Matching**: 3 (9%)
- **⚠️ Outdated**: 8 (24%)
- **❌ Missing**: 23 (68%)

## Prerequisites

- Node.js v20.11.1 or higher
- npm v8.0.0 or higher

## Key Dependencies

### Core Framework & UI
- **Next.js**: v14.2.1 - Core framework with App Router
- **React**: v18.3.0 - UI library with concurrent features
- **TypeScript**: v5.4.2 - Type checking and developer experience
- **Tailwind CSS**: v3.4.1 - Utility-first CSS framework
- **shadcn/ui**: v0.6.0 - Component library

### Canvas & Visual Creation
- **tldraw**: v2.0.0-canary.20 - Drawing and diagramming
- **Lexical**: v0.12.5 - Extensible text editor
- **MJML**: v4.15.0 - Email template framework
- **react-email**: v1.10.0 - Email components

### State Management
- **Redux Toolkit**: v2.2.1 - State management
- **Zustand**: v4.5.0 - Lightweight state management
- **React Query**: v5.22.2 - Data fetching and caching

### Collaboration & Real-time
- **Yjs**: v13.6.1 - Collaborative editing
- **Socket.io**: v4.7.4 - Real-time communication

### AI & Machine Learning
- **@anthropic-ai/sdk**: v0.11.0 - Claude AI integration
- **openai**: v4.24.7 - OpenAI integration
- **@google/generative-ai**: v0.2.0 - Google AI integration
- **TensorFlow.js**: v4.16.0 - Machine learning for the web

### Visualization
- **Recharts**: v2.12.0 - React charting library
- **D3**: v7.8.5 - Data visualization

### Blockchain & Web3
- **Ethers.js**: v6.7.1 - Ethereum library
- **web3modal**: v5.1.11 - Web3 connection framework
- **MetaMask SDK**: v0.15.0 - MetaMask integration

## Update Process

### 1. Check Current Dependency Status

Run the dependency checker script to analyze your current dependencies:

```bash
node scripts/check-dependencies.js
```

This will generate a report showing which dependencies need to be updated.

### 2. Update Package.json Files

Run the package.json updater script:

```bash
node scripts/update-missing-dependencies.js
```

This will modify the package.json files to include all required dependencies.

### 3. Install Dependencies

After updating the package.json files, install the dependencies:

```bash
# Root project
npm install

# Web app
cd apps/web
npm install
```

### 4. Install shadcn/ui Components

```bash
./scripts/install-shadcn.sh
```

## Current Missing Packages

```
@radix-ui/react-primitives@2.0.2
cmdk@0.2.1
tldraw@2.0.0-canary.20
lexical@0.12.5
@lexical/react@0.12.5
mjml@4.15.0
react-email@1.10.0
@reduxjs/toolkit@2.2.1
react-redux@9.1.0
yjs@13.6.1
y-websocket@1.5.1
y-indexeddb@9.0.12
socket.io-client@4.7.4
@anthropic-ai/sdk@0.11.0
openai@4.24.7
@google/generative-ai@0.2.0
ai@2.2.34
@tensorflow/tfjs@4.16.0
recharts@2.12.0
d3@7.8.5
ethers@6.7.1
@web3modal/wagmi@5.1.11
@web3modal/react@2.7.1
@web3modal/standalone@2.4.3
@metamask/sdk-react@0.15.0
```

## Current Outdated Packages

```
next: 14.1.0 → 14.2.1
react: 18.2.0 → 18.3.0
react-dom: 18.2.0 → 18.3.0
typescript: 5.0.3 → 5.4.2
framer-motion: 12.4.7, 11.0.5 → 11.0.5
lucide-react: 0.475.0, 0.331.0 → 0.344.0
zustand: 4.5.1 → 4.5.0
@tanstack/react-query: 5.18.1 → 5.22.2
```

## Update Commands

### Priority Packages

```bash
npm install next@14.2.1 react@18.3.0 react-dom@18.3.0 @tensorflow/tfjs@4.16.0 ethers@6.7.1 yjs@13.6.1
```

### UI Packages

```bash
npm install @radix-ui/react-primitives@2.0.2 framer-motion@11.0.5 lucide-react@0.344.0 cmdk@0.2.1
```

### Canvas Packages

```bash
npm install tldraw@2.0.0-canary.20 lexical@0.12.5 @lexical/react@0.12.5 mjml@4.15.0 react-email@1.10.0
```

### State Management

```bash
npm install @reduxjs/toolkit@2.2.1 react-redux@9.1.0 zustand@4.5.0 @tanstack/react-query@5.22.2
```

### Collaboration

```bash
npm install y-websocket@1.5.1 y-indexeddb@9.0.12 socket.io-client@4.7.4
```

### AI Integration

```bash
npm install @anthropic-ai/sdk@0.11.0 openai@4.24.7 @google/generative-ai@0.2.0 ai@2.2.34
```

### Visualization

```bash
npm install recharts@2.12.0 d3@7.8.5
```

### Blockchain

```bash
npm install @web3modal/wagmi@5.1.11 @web3modal/react@2.7.1 @web3modal/standalone@2.4.3 @metamask/sdk-react@0.15.0
```

### shadcn/ui Components

```bash
npx shadcn-ui@0.6.0 init
npx shadcn-ui@0.6.0 add button card dialog dropdown-menu avatar toast
```

## Verification

After updating, verify the installation:

```bash
# Check Next.js version
npx next --version
# Should output: 14.2.1

# Check React version
npm list react
# Should show 18.3.0
```