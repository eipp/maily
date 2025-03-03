#!/bin/bash
# Maily Dependency Update Script - Generated 2025-03-03T15:48:38.522Z
set -e

echo "🚀 Updating Maily dependencies to March 2025 versions..."

# Install priority packages first (Next.js, React, etc.)
npm install next@14.2.1 react@18.3.0 react-dom@18.3.0 @tensorflow/tfjs@4.16.0 ethers@6.10.0 yjs@13.6.1 @anthropic-ai/sdk@0.11.0 openai@4.24.7 @google/generative-ai@0.2.0

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
npm install ethers@6.7.1 @web3modal/wagmi@5.1.11 @web3modal/react@2.7.1 @web3modal/standalone@2.4.3 @metamask/sdk-react@0.15.0

# Install shadcn/ui components
npx shadcn-ui@0.6.0 init
npx shadcn-ui@0.6.0 add button card dialog dropdown-menu avatar toast


echo "✅ Dependencies updated successfully!"
