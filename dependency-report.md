# Maily Dependency Report - 3/3/2025

## Summary
- Total target packages: 34
- ✅ Matching: 3 (9%)
- ⚠️ Outdated: 8 (24%)
- ❌ Missing: 23 (68%)

## Missing Packages

- @radix-ui/react-primitives@2.0.2
- cmdk@0.2.1
- tldraw@2.0.0-canary.20
- lexical@0.12.5
- @lexical/react@0.12.5
- mjml@4.15.0
- react-email@1.10.0
- @reduxjs/toolkit@2.2.1
- react-redux@9.1.0
- yjs@13.6.1
- y-websocket@1.5.1
- y-indexeddb@9.0.12
- socket.io-client@4.7.4
- @anthropic-ai/sdk@0.11.0
- openai@4.24.7
- @google/generative-ai@0.2.0
- ai@2.2.34
- @tensorflow/tfjs@4.16.0
- recharts@2.12.0
- d3@7.8.5
- ethers@6.7.1
- @web3modal/wagmi@5.1.11
- @web3modal/react@2.7.1
- @web3modal/standalone@2.4.3
- @metamask/sdk-react@0.15.0

## Outdated Packages

- next: 14.1.0 → 14.2.1
- react: 18.2.0 → 18.3.0
- react-dom: 18.2.0 → 18.3.0
- typescript: 5.0.3 → 5.4.2
- framer-motion: 12.4.7, 11.0.5 → 11.0.5
- lucide-react: 0.475.0, 0.331.0 → 0.344.0
- zustand: 4.5.1 → 4.5.0
- @tanstack/react-query: 5.18.1 → 5.22.2

## Update Commands

```bash
# Install priority packages first (Next.js, React, etc.)
npm install next@14.2.1 react@18.3.0 react-dom@18.3.0 @tensorflow/tfjs@4.16.0 ethers@6.7.1 yjs@13.6.1 @anthropic-ai/sdk@0.11.0 openai@4.24.7 @google/generative-ai@0.2.0

# Install ui packages
npm install @radix-ui/react-primitives@2.0.2 framer-motion@11.0.5 lucide-react@0.344.0 cmdk@0.2.1

# Install canvas packages
npm install tldraw@2.0.0-canary.20 lexical@0.12.5 @lexical/react@0.12.5 mjml@4.15.0 react-email@1.10.0

# Install state packages
npm install @reduxjs/toolkit@2.2.1 react-redux@9.1.0 zustand@4.5.0 @tanstack/react-query@5.22.2

# Install collaboration packages
npm install y-websocket@1.5.1 y-indexeddb@9.0.12 socket.io-client@4.7.4

# Install ai packages
npm install ai@2.2.34

# Install visualization packages
npm install recharts@2.12.0 d3@7.8.5

# Install blockchain packages
npm install @web3modal/wagmi@5.1.11 @web3modal/react@2.7.1 @web3modal/standalone@2.4.3 @metamask/sdk-react@0.15.0

# Install shadcn/ui components
npx shadcn-ui@0.6.0 init
npx shadcn-ui@0.6.0 add button card dialog dropdown-menu avatar toast
```
