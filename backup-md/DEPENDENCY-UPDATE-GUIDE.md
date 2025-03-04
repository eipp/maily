# Maily Dependency Update Guide (March 2025)

This guide will help you update the Maily project dependencies to match the comprehensive list from March 2025.

## Prerequisites

- Node.js v20.11.1 or higher
- npm v8.0.0 or higher

## Steps to Update Dependencies

1. **Check Current Dependency Status**

   Run the dependency checker script to analyze your current dependencies:

   ```bash
   node scripts/check-dependencies.js
   ```

   This will generate a report showing which dependencies need to be updated.

2. **Update Package.json Files**

   Run the package.json updater script:

   ```bash
   node scripts/update-missing-dependencies.js
   ```

   This will modify the package.json files to include all required dependencies.

3. **Install Dependencies**

   After updating the package.json files, install the dependencies:

   ```bash
   # Root project
   npm install

   # Web app
   cd apps/web
   npm install
   ```

4. **Install shadcn/ui Components**

   ```bash
   ./scripts/install-shadcn.sh
   ```

## Key Dependencies

The most important dependencies to verify:

- **Next.js**: v14.2.1 - Core framework with App Router
- **React**: v18.3.0 - UI library with concurrent features
- **TypeScript**: v5.4.2 - Type checking and developer experience
- **TensorFlow.js**: v4.16.0 - Machine learning for the web
- **Ethers.js**: v6.10.0 - Ethereum library
- **Yjs**: v13.6.1 - Collaborative editing
- **AI SDKs**:
  - @anthropic-ai/sdk: v0.11.0
  - openai: v4.24.7
  - @google/generative-ai: v0.2.0

## Dependency Categories

1. **Core Framework & UI**: Next.js, React, Tailwind CSS, shadcn/ui
2. **Canvas & Visual Creation**: tldraw, Lexical editor, MJML email templates
3. **State Management**: Redux Toolkit, Zustand, React Query
4. **Collaboration & Real-time**: Yjs, Socket.io
5. **AI & Machine Learning**: Anthropic, OpenAI, TensorFlow.js
6. **Visualization**: Recharts, D3
7. **Blockchain & Web3**: Ethers.js, MetaMask
8. **Testing & Quality**: Jest, Cypress, Playwright
9. **Build Tools**: Webpack, SWC, ESBuild
10. **Developer Experience**: Storybook, Utility libraries
11. **Integration & API Clients**: Email services, Database clients

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
