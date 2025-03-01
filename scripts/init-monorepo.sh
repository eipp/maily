#!/bin/bash

# Script to initialize the monorepo structure for Maily

echo "🚀 Initializing Maily monorepo structure..."

# Create the directory structure
echo "📁 Creating directory structure..."
mkdir -p apps/{web,api,workers}
mkdir -p packages/{ai,ui,config,database,email-renderer,analytics,utils}
mkdir -p infrastructure/{terraform,kubernetes,helm,docker}
mkdir -p .github/{workflows,ISSUE_TEMPLATE}
mkdir -p package-templates

# Create README files for each directory
echo "📝 Creating README files..."
for dir in apps/{web,api,workers} packages/{ai,ui,config,database,email-renderer,analytics,utils} infrastructure/{terraform,kubernetes,helm,docker}; do
  echo "# Maily - ${dir}" > "${dir}/README.md"
  echo "" >> "${dir}/README.md"
  echo "This directory contains the $(basename ${dir}) module for the Maily platform." >> "${dir}/README.md"
done

# Copy package templates to their destinations
echo "📦 Setting up package configurations..."
mkdir -p packages/eslint-config-maily

# Create eslint-config-maily
cat > packages/eslint-config-maily/package.json << EOF
{
  "name": "eslint-config-maily",
  "version": "0.0.1",
  "main": "index.js",
  "license": "MIT",
  "dependencies": {
    "eslint-config-next": "^13.3.0",
    "eslint-config-prettier": "^8.8.0",
    "eslint-plugin-react": "^7.32.2",
    "eslint-config-turbo": "^1.9.3"
  },
  "publishConfig": {
    "access": "public"
  }
}
EOF

cat > packages/eslint-config-maily/index.js << EOF
module.exports = {
  extends: ["next", "turbo", "prettier"],
  rules: {
    "@next/next/no-html-link-for-pages": "off",
    "react/jsx-key": "off",
  },
};
EOF

echo "✅ Initial monorepo structure created successfully!"
echo ""
echo "Next steps:"
echo "1. Run 'npm install' to install root dependencies"
echo "2. Follow the migration plan in MIGRATION_PLAN.md to move code to the new structure"
echo "3. Update imports and paths in all files"
echo ""
echo "Happy coding! 🎉"
