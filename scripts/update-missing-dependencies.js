#!/usr/bin/env node

/**
 * Maily Package.json Updater - March 2025
 * 
 * This script updates package.json files with the missing dependencies
 * specified in the Maily comprehensive dependency list.
 */

const fs = require('fs');
const path = require('path');

// March 2025 dependency specifications by category
const dependencyCategories = {
  // 1. Core Framework & UI Dependencies
  core: {
    // Application Framework
    "next": "14.2.1",
    "react": "18.3.0",
    "react-dom": "18.3.0",
    "typescript": "5.4.2",
    
    // UI Foundation
    "tailwindcss": "3.4.1",
    "@radix-ui/react-primitives": "2.0.2",
    "framer-motion": "11.0.5",
    "lucide-react": "0.344.0",
    "next-themes": "0.2.1",
    
    // UI Components & Interaction
    "cmdk": "0.2.1",
    "@react-aria/calendar": "3.30.0",
    "@floating-ui/react": "0.26.4",
    "react-hook-form": "7.50.1",
    "zod": "3.22.4",
    "react-dropzone": "14.2.3",
    "react-resizable": "3.0.5",
    "@dnd-kit/core": "6.1.0",
    "react-window": "1.8.10"
  },
  
  // 2. Canvas & Visual Creation Dependencies
  canvas: {
    // Canvas Engine
    "tldraw": "2.0.0-canary.20",
    "react-use-gesture": "9.1.3", 
    "perfect-freehand": "1.2.0",
    "html-to-image": "1.11.11",
    "zustand": "4.5.0",
    "immer": "10.0.3",
    
    // Rich Text Editing
    "lexical": "0.12.5",
    "@lexical/react": "0.12.5",
    "@lexical/rich-text": "0.12.5",
    "@lexical/list": "0.12.5",
    "@lexical/markdown": "0.12.5",
    "@lexical/code": "0.12.5",
    "prosemirror-view": "1.32.6",
    
    // Email & Template Rendering
    "mjml": "4.15.0",
    "mjml-react": "2.0.9",
    "react-email": "1.10.0",
    "html-react-parser": "5.1.1",
    "juice": "9.1.0",
    "handlebars": "4.7.8"
  },
  
  // 3. State Management & Data Flow
  state: {
    // Global State
    "@reduxjs/toolkit": "2.2.1",
    "react-redux": "9.1.0",
    "jotai": "2.6.2",
    "zustand": "4.5.0",
    "valtio": "1.13.1",
    "recoil": "0.7.7",
    
    // Data Fetching & API
    "swr": "2.2.4",
    "@tanstack/react-query": "5.22.2",
    "axios": "1.6.7",
    "graphql": "16.8.1",
    "graphql-request": "6.1.0",
    "@apollo/client": "3.8.10",
    
    // Local Storage & Persistence
    "idb": "7.1.1",
    "localforage": "1.10.0",
    "cookies-next": "4.1.0",
    "@vercel/kv": "0.2.5",
    "superjson": "2.2.1"
  },
  
  // 4. Collaboration & Real-time Features
  collaboration: {
    // Collaborative Editing
    "yjs": "13.6.1",
    "y-websocket": "1.5.1",
    "y-indexeddb": "9.0.12",
    "@tldraw/yjs-example": "2.0.0-canary.20",
    "automerge": "2.1.8",
    
    // Websockets & Real-time
    "socket.io-client": "4.7.4",
    "@supabase/realtime-js": "2.9.3",
    "pusher-js": "8.4.0-rc2",
    "phoenix": "1.7.10",
    "centrifuge": "4.1.0"
  },
  
  // 5. AI & Machine Learning
  ai: {
    // AI Integration
    "@anthropic-ai/sdk": "0.11.0",
    "openai": "4.24.7",
    "@google/generative-ai": "0.2.0",
    "ai": "2.2.34",
    "langchain": "0.1.17",
    
    // Machine Learning & TensorFlow
    "@tensorflow/tfjs": "4.16.0",
    "@tensorflow/tfjs-vis": "1.5.1",
    "ml5": "0.12.2",
    "@tensorflow-models/universal-sentence-encoder": "1.3.3",
    "@xenova/transformers": "2.14.0",
    "onnxruntime-web": "1.17.0",
    
    // NLP & Text Processing
    "compromise": "14.11.0",
    "natural": "6.10.4",
    "sentiment": "5.0.2",
    "marked": "11.1.1",
    "dompurify": "3.0.8",
    "linkify-it": "5.0.0"
  }
};

// Dev dependencies by category
const devDependencyCategories = {
  // 8. Testing & Quality Assurance
  testing: {
    // Testing Libraries
    "jest": "29.7.0",
    "@testing-library/react": "14.2.1",
    "@testing-library/user-event": "14.5.2",
    "vitest": "1.2.2",
    "cypress": "13.6.4",
    "playwright": "1.41.2",
    
    // Performance & Quality
    "eslint": "8.56.0",
    "prettier": "3.2.5",
    "typescript-eslint": "6.21.0",
    "axe-core": "4.8.3",
    "lighthouse": "11.4.0",
    "@next/bundle-analyzer": "14.2.1"
  },
  
  // 9. Build Tools & Infrastructure
  build: {
    // Build & Bundling
    "webpack": "5.90.3",
    "turbopack": "1.12.1",
    "@swc/core": "1.3.107",
    "esbuild": "0.20.0",
    "postcss": "8.4.35",
    "autoprefixer": "10.4.17",
    
    // DevOps & Monitoring
    "@sentry/nextjs": "7.101.1",
    "@vercel/analytics": "1.1.1",
    "datadog-rum": "4.60.3",
    "@opentelemetry/api": "1.18.1",
    "prom-client": "15.1.0"
  },
  
  // 10. Developer Experience & Utilities
  devExp: {
    // Developer Tools
    "@storybook/react": "7.6.10",
    "chromatic": "7.4.0",
    "plop": "4.0.1",
    "husky": "9.0.6",
    "lint-staged": "15.2.0",
    
    // Utilities
    "date-fns": "3.3.1",
    "nanoid": "5.0.4",
    "lodash-es": "4.17.21",
    "clsx": "2.1.0",
    "tailwind-merge": "2.2.0",
    "class-variance-authority": "0.7.0",
    "@faker-js/faker": "8.4.1"
  }
};

// Priority packages that must be updated first
const priorityPackages = [
  "next", "react", "react-dom", "typescript", 
  "@tensorflow/tfjs", "ethers", "yjs", 
  "@anthropic-ai/sdk", "openai", "@google/generative-ai"
];

/**
 * Find target package.json files
 */
function findPackageJsonFiles() {
  // We'll focus on the root package.json and web app package.json
  const files = [];
  
  if (fs.existsSync('package.json')) {
    files.push({
      path: 'package.json',
      type: 'root'
    });
  }
  
  if (fs.existsSync('apps/web/package.json')) {
    files.push({
      path: 'apps/web/package.json',
      type: 'web'
    });
  }
  
  return files;
}

/**
 * Update a package.json file with missing dependencies
 */
function updatePackageJson(filePath, type) {
  console.log(`\nUpdating ${filePath}...`);
  
  let packageJson;
  
  try {
    packageJson = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    console.error(`Error reading ${filePath}:`, error.message);
    return false;
  }
  
  // Ensure dependencies objects exist
  packageJson.dependencies = packageJson.dependencies || {};
  packageJson.devDependencies = packageJson.devDependencies || {};
  
  let addedCount = 0;
  let updatedCount = 0;
  
  // Update Node.js version
  if (type === 'root' && packageJson.engines) {
    packageJson.engines.node = ">=20.11.1";
    console.log(`✅ Updated Node.js engine requirement to >=20.11.1`);
  }
  
  // Update dependencies
  for (const [category, deps] of Object.entries(dependencyCategories)) {
    console.log(`\nProcessing ${category} dependencies...`);
    
    for (const [name, version] of Object.entries(deps)) {
      // Skip some categories for the root package.json
      if (type === 'root' && ['canvas', 'ai'].includes(category)) {
        continue;
      }
      
      if (!packageJson.dependencies[name]) {
        packageJson.dependencies[name] = version;
        console.log(`➕ Added ${name}@${version}`);
        addedCount++;
      } else if (packageJson.dependencies[name] !== version && 
                (type === 'web' || priorityPackages.includes(name))) {
        const oldVersion = packageJson.dependencies[name];
        packageJson.dependencies[name] = version;
        console.log(`🔄 Updated ${name}: ${oldVersion} → ${version}`);
        updatedCount++;
      }
    }
  }
  
  // Update dev dependencies
  if (type === 'web') {
    for (const [category, deps] of Object.entries(devDependencyCategories)) {
      console.log(`\nProcessing ${category} dev dependencies...`);
      
      for (const [name, version] of Object.entries(deps)) {
        if (!packageJson.devDependencies[name]) {
          packageJson.devDependencies[name] = version;
          console.log(`➕ Added ${name}@${version} (dev)`);
          addedCount++;
        } else if (packageJson.devDependencies[name] !== version) {
          const oldVersion = packageJson.devDependencies[name];
          packageJson.devDependencies[name] = version;
          console.log(`🔄 Updated ${name}: ${oldVersion} → ${version} (dev)`);
          updatedCount++;
        }
      }
    }
  }
  
  // Write updated package.json
  try {
    fs.writeFileSync(filePath, JSON.stringify(packageJson, null, 2));
    console.log(`\n✅ Successfully updated ${filePath}`);
    console.log(`   Added: ${addedCount} packages`);
    console.log(`   Updated: ${updatedCount} packages`);
    return true;
  } catch (error) {
    console.error(`Error writing ${filePath}:`, error.message);
    return false;
  }
}

/**
 * Create shadcn/ui components.json if it doesn't exist
 */
function ensureShadcnConfig() {
  const componentsJsonPath = 'apps/web/components.json';
  
  if (!fs.existsSync(componentsJsonPath)) {
    const componentsJson = {
      "$schema": "https://ui.shadcn.com/schema.json",
      "style": "default",
      "rsc": true,
      "tsx": true,
      "tailwind": {
        "config": "tailwind.config.ts",
        "css": "globals.css",
        "baseColor": "neutral",
        "cssVariables": true
      },
      "aliases": {
        "components": "@/components",
        "utils": "@/lib/utils"
      }
    };
    
    try {
      fs.writeFileSync(componentsJsonPath, JSON.stringify(componentsJson, null, 2));
      console.log(`✅ Created shadcn/ui configuration file`);
      return true;
    } catch (error) {
      console.error(`Error creating shadcn/ui configuration:`, error.message);
      return false;
    }
  }
  
  return true;
}

/**
 * Create a shadcn/ui installation script
 */
function createShadcnInstallScript() {
  const scriptPath = 'scripts/install-shadcn.sh';
  const components = [
    "button", "card", "dialog", "dropdown-menu", 
    "avatar", "toast", "tabs", "form", "select",
    "input", "textarea", "checkbox", "radio-group",
    "slider", "switch", "accordion", "alert",
    "badge", "calendar", "command", "popover",
    "progress", "sheet", "table"
  ];
  
  const scriptContent = `#!/bin/bash
# Script to install all shadcn/ui components
cd $(dirname $0)/..

# Navigate to web app directory
cd apps/web

# Initialize shadcn/ui if not already initialized
if [ ! -f "components.json" ]; then
  npx shadcn-ui@0.6.0 init
fi

# Install all components
${components.map(component => `npx shadcn-ui@0.6.0 add ${component}`).join('\n')}

echo "✅ All shadcn/ui components have been installed!"
`;

  try {
    fs.writeFileSync(scriptPath, scriptContent);
    fs.chmodSync(scriptPath, '755'); // Make executable
    console.log(`✅ Created shadcn/ui installation script at ${scriptPath}`);
    return true;
  } catch (error) {
    console.error(`Error creating shadcn/ui script:`, error.message);
    return false;
  }
}

/**
 * Create installation instructions
 */
function createInstallInstructions() {
  const readmePath = 'DEPENDENCY-UPDATE-GUIDE.md';
  
  const readmeContent = `# Maily Dependency Update Guide (March 2025)

This guide will help you update the Maily project dependencies to match the comprehensive list from March 2025.

## Prerequisites

- Node.js v20.11.1 or higher
- npm v8.0.0 or higher

## Steps to Update Dependencies

1. **Check Current Dependency Status**

   Run the dependency checker script to analyze your current dependencies:

   \`\`\`bash
   node scripts/check-dependencies.js
   \`\`\`

   This will generate a report showing which dependencies need to be updated.

2. **Update Package.json Files**

   Run the package.json updater script:

   \`\`\`bash
   node scripts/update-missing-dependencies.js
   \`\`\`

   This will modify the package.json files to include all required dependencies.

3. **Install Dependencies**

   After updating the package.json files, install the dependencies:

   \`\`\`bash
   # Root project
   npm install

   # Web app
   cd apps/web
   npm install
   \`\`\`

4. **Install shadcn/ui Components**

   \`\`\`bash
   ./scripts/install-shadcn.sh
   \`\`\`

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

\`\`\`bash
# Check Next.js version
npx next --version
# Should output: 14.2.1

# Check React version
npm list react
# Should show 18.3.0
\`\`\`
`;

  try {
    fs.writeFileSync(readmePath, readmeContent);
    console.log(`✅ Created installation guide at ${readmePath}`);
    return true;
  } catch (error) {
    console.error(`Error creating installation guide:`, error.message);
    return false;
  }
}

/**
 * Main function
 */
function main() {
  console.log('🚀 Maily Package.json Updater - March 2025');
  console.log('===========================================');
  
  // Find package.json files
  const packageJsonFiles = findPackageJsonFiles();
  
  if (packageJsonFiles.length === 0) {
    console.error('❌ No package.json files found!');
    return;
  }
  
  console.log(`Found ${packageJsonFiles.length} package.json files to update.`);
  
  // Update each package.json file
  let successCount = 0;
  
  for (const { path: filePath, type } of packageJsonFiles) {
    if (updatePackageJson(filePath, type)) {
      successCount++;
    }
  }
  
  // Ensure shadcn configuration
  ensureShadcnConfig();
  
  // Create shadcn installation script
  createShadcnInstallScript();
  
  // Create installation instructions
  createInstallInstructions();
  
  console.log('\n===========================================');
  console.log(`✅ Successfully updated ${successCount}/${packageJsonFiles.length} package.json files.`);
  console.log('📝 Next steps:');
  console.log('1. Run `npm install` in the project root');
  console.log('2. Run `cd apps/web && npm install`');
  console.log('3. Run `./scripts/install-shadcn.sh`');
  console.log('4. See DEPENDENCY-UPDATE-GUIDE.md for more details');
}

// Run the script
main(); 