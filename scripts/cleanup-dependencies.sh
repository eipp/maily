#!/bin/bash

# Script to clean up redundant dependencies in the project
# This script will:
# 1. Remove built-in module requirements (asyncio)
# 2. Consolidate OpenTelemetry packages
# 3. Standardize GraphQL implementations
# 4. Consolidate HTTP client libraries

set -e

# Define colors for better output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting dependency cleanup...${NC}"

# 1. Remove built-in module dependencies
echo -e "\n${GREEN}Removing built-in module dependencies...${NC}"

# Remove asyncio from requirements files
echo -e "${YELLOW}Cleaning requirements-ai-ml.txt file${NC}"
sed -i.bak '/^asyncio/d' apps/api/requirements-ai-ml.txt
echo -e "${GREEN}✓ Removed built-in asyncio module from requirements${NC}"

# 2. Consolidate OpenTelemetry packages
echo -e "\n${GREEN}Consolidating OpenTelemetry packages...${NC}"

# Create a common file with standardized OpenTelemetry dependencies
cat > packages/config/monitoring/telemetry-requirements.txt << EOF
# Standardized OpenTelemetry dependencies for Maily
opentelemetry-api==1.20.0
opentelemetry-sdk==1.20.0
opentelemetry-exporter-otlp==1.20.0
opentelemetry-exporter-prometheus==1.12.0rc1
EOF

echo -e "${GREEN}✓ Created standardized OpenTelemetry requirements file${NC}"
echo -e "${YELLOW}Created packages/config/monitoring/telemetry-requirements.txt${NC}"
echo -e "${YELLOW}To use this file, add '-r packages/config/monitoring/telemetry-requirements.txt' to Python requirements files${NC}"

# 3. Clean up GraphQL implementations
echo -e "\n${GREEN}Standardizing GraphQL implementations...${NC}"

# Create a script to update package.json files
cat > scripts/standardize-graphql.js << EOF
/**
 * Script to standardize GraphQL implementations across the project
 */
const fs = require('fs');
const path = require('path');

// Standard GraphQL dependencies to use
const standardGraphQLDeps = {
  "@apollo/client": "^3.8.1",
  "graphql": "^16.8.0"
};

// Function to update package.json files
function updatePackageJson(filePath) {
  try {
    const pkg = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    let modified = false;
    
    // Dependencies to remove
    const depsToRemove = [
      'apollo-boost',
      'apollo-link',
      'apollo-link-http',
      'apollo-client',
      'apollo-cache-inmemory',
      'apollo-utilities',
      'react-apollo',
      '@graphql-tools/schema',
      'graphql-tag',
      'graphql-request'
    ];
    
    // Check and update dependencies
    if (pkg.dependencies) {
      depsToRemove.forEach(dep => {
        if (pkg.dependencies[dep]) {
          console.log(\`Removing \${dep} from \${filePath}\`);
          delete pkg.dependencies[dep];
          modified = true;
        }
      });
      
      // Add standard dependencies if any GraphQL dependency exists
      if (pkg.dependencies['graphql'] || pkg.dependencies['@apollo/client']) {
        Object.entries(standardGraphQLDeps).forEach(([dep, version]) => {
          if (!pkg.dependencies[dep] || pkg.dependencies[dep] !== version) {
            console.log(\`Updating \${dep} to \${version} in \${filePath}\`);
            pkg.dependencies[dep] = version;
            modified = true;
          }
        });
      }
    }
    
    // Check and update devDependencies
    if (pkg.devDependencies) {
      depsToRemove.forEach(dep => {
        if (pkg.devDependencies[dep]) {
          console.log(\`Removing \${dep} from devDependencies in \${filePath}\`);
          delete pkg.devDependencies[dep];
          modified = true;
        }
      });
    }
    
    // Write back if modified
    if (modified) {
      fs.writeFileSync(filePath, JSON.stringify(pkg, null, 2) + '\\n');
      console.log(\`Updated \${filePath}\`);
      return true;
    }
    
    return false;
  } catch (error) {
    console.error(\`Error updating \${filePath}: \${error.message}\`);
    return false;
  }
}

// Find all package.json files recursively
function findPackageJsonFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    if (fs.statSync(filePath).isDirectory() && file !== 'node_modules') {
      findPackageJsonFiles(filePath, fileList);
    } else if (file === 'package.json') {
      fileList.push(filePath);
    }
  });
  
  return fileList;
}

// Main function
function main() {
  console.log('Standardizing GraphQL implementations across the project...');
  
  const packageJsonFiles = findPackageJsonFiles('.');
  let updatedCount = 0;
  
  packageJsonFiles.forEach(filePath => {
    if (updatePackageJson(filePath)) {
      updatedCount++;
    }
  });
  
  console.log(\`Standardized GraphQL dependencies in \${updatedCount} package.json files\`);
}

main();
EOF

echo -e "${GREEN}✓ Created script to standardize GraphQL implementations${NC}"
echo -e "${YELLOW}Run 'node scripts/standardize-graphql.js' to apply changes${NC}"

# 4. Consolidate HTTP client libraries
echo -e "\n${GREEN}Consolidating HTTP client libraries...${NC}"

# Create a Python HTTP standardization script
cat > scripts/standardize-http-clients.py << EOF
#!/usr/bin/env python3
"""
Script to standardize HTTP client imports in Python code.
Replaces import statements for multiple HTTP libraries with the standard one.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Standard HTTP client to use
STANDARD_HTTP_CLIENT = "httpx"
HTTP_CLIENTS_TO_REPLACE = ["requests", "aiohttp", "urllib3"]

def find_python_files(start_dir: str) -> List[str]:
    """Find all Python files in the given directory tree."""
    python_files = []
    for root, _, files in os.walk(start_dir):
        # Skip virtual environments and node_modules
        if "venv" in root or "node_modules" in root or ".git" in root:
            continue
        python_files.extend(
            os.path.join(root, file)
            for file in files
            if file.endswith(".py")
        )
    return python_files

def replace_imports(file_path: str) -> Tuple[bool, List[str]]:
    """Replace HTTP client imports in the given file."""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content
    replacements = []

    # Regular expressions for different import styles
    patterns = [
        # Regular import
        (r"import\s+(requests|aiohttp|urllib3)(\s+as\s+\w+)?", f"import {STANDARD_HTTP_CLIENT}\\2"),
        # From import
        (r"from\s+(requests|aiohttp|urllib3)(\.\w+)?\s+import", f"from {STANDARD_HTTP_CLIENT}\\2 import"),
    ]

    for pattern, replacement in patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if match[0] in HTTP_CLIENTS_TO_REPLACE:
                old_import = re.search(pattern, content).group(0)
                new_import = re.sub(pattern, replacement, old_import)
                content = content.replace(old_import, new_import)
                replacements.append(f"{old_import} -> {new_import}")

    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        return True, replacements
    
    return False, []

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python standardize-http-clients.py <directory>")
        sys.exit(1)
    
    start_dir = sys.argv[1]
    if not os.path.isdir(start_dir):
        print(f"Error: {start_dir} is not a directory")
        sys.exit(1)
    
    python_files = find_python_files(start_dir)
    modified_count = 0
    all_replacements = []
    
    for file_path in python_files:
        modified, replacements = replace_imports(file_path)
        if modified:
            modified_count += 1
            print(f"Modified: {file_path}")
            for replacement in replacements:
                print(f"  {replacement}")
                all_replacements.append((file_path, replacement))
    
    print(f"\nSummary:")
    print(f"Scanned {len(python_files)} Python files")
    print(f"Modified {modified_count} files")
    print(f"Made {len(all_replacements)} replacements")
    
    # Output a complete replacement log
    with open("http_client_replacements.log", "w") as f:
        for file_path, replacement in all_replacements:
            f.write(f"{file_path}: {replacement}\n")

if __name__ == "__main__":
    main()
EOF

echo -e "${GREEN}✓ Created script to standardize HTTP client libraries${NC}"
echo -e "${YELLOW}Run 'python scripts/standardize-http-clients.py <directory>' to apply changes${NC}"

# Make scripts executable
chmod +x scripts/standardize-http-clients.py

echo -e "\n${GREEN}Dependency cleanup preparation completed!${NC}"
echo -e "${YELLOW}Please review the generated scripts and run them to apply the changes.${NC}"