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
          console.log(`Removing ${dep} from ${filePath}`);
          delete pkg.dependencies[dep];
          modified = true;
        }
      });
      
      // Add standard dependencies if any GraphQL dependency exists
      if (pkg.dependencies['graphql'] || pkg.dependencies['@apollo/client']) {
        Object.entries(standardGraphQLDeps).forEach(([dep, version]) => {
          if (!pkg.dependencies[dep] || pkg.dependencies[dep] !== version) {
            console.log(`Updating ${dep} to ${version} in ${filePath}`);
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
          console.log(`Removing ${dep} from devDependencies in ${filePath}`);
          delete pkg.devDependencies[dep];
          modified = true;
        }
      });
    }
    
    // Write back if modified
    if (modified) {
      fs.writeFileSync(filePath, JSON.stringify(pkg, null, 2) + '\n');
      console.log(`Updated ${filePath}`);
      return true;
    }
    
    return false;
  } catch (error) {
    console.error(`Error updating ${filePath}: ${error.message}`);
    return false;
  }
}

// Find all package.json files recursively
function findPackageJsonFiles(dir, fileList = []) {
  try {
    const files = fs.readdirSync(dir);
    
    files.forEach(file => {
      const filePath = path.join(dir, file);
      try {
        const stat = fs.statSync(filePath);
        if (stat.isDirectory() && file !== 'node_modules') {
          findPackageJsonFiles(filePath, fileList);
        } else if (file === 'package.json') {
          fileList.push(filePath);
        }
      } catch (error) {
        console.error(`Error accessing ${filePath}: ${error.message}`);
      }
    });
  } catch (error) {
    console.error(`Error reading directory ${dir}: ${error.message}`);
  }
  
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
  
  console.log(`Standardized GraphQL dependencies in ${updatedCount} package.json files`);
}

main();
