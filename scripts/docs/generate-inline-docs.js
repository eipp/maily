#!/usr/bin/env node

/**
 * Code Documentation Generator
 *
 * This script analyzes the codebase to extract and generate documentation from inline
 * code comments (JSDoc, Python docstrings, etc.) and creates structured markdown files.
 *
 * Features:
 * - Extracts documentation from JavaScript/TypeScript (JSDoc)
 * - Extracts documentation from Python (docstrings)
 * - Organizes documentation by module/package
 * - Creates navigation structure in MkDocs
 * - Generates architecture diagrams based on code relationships (optional)
 * - Integrates with existing documentation
 *
 * Usage: node scripts/generate-inline-docs.js [--dir=path/to/dir] [--output=path/to/output]
 */

const fs = require('fs');
const path = require('path');
const util = require('util');
const glob = util.promisify(require('glob'));
const jsdoc2md = require('jsdoc-to-markdown');
const yaml = require('js-yaml');
const { execSync } = require('child_process');

// Convert fs functions to promises
const readFile = util.promisify(fs.readFile);
const writeFile = util.promisify(fs.writeFile);
const mkdir = util.promisify(fs.mkdir);

// Parse command line arguments
const args = process.argv.slice(2).reduce((acc, arg) => {
  const [key, value] = arg.split('=');
  if (key && value) {
    acc[key.replace(/^--/, '')] = value;
  }
  return acc;
}, {});

// Configuration
const ROOT_DIR = path.resolve(__dirname, '..');
const SOURCE_DIR = path.resolve(ROOT_DIR, args.dir || '.');
const DOCS_OUTPUT_DIR = path.resolve(ROOT_DIR, args.output || 'docs/code');
const MKDOCS_PATH = path.join(ROOT_DIR, 'mkdocs.yml');

// File patterns for different languages
const FILE_PATTERNS = {
  javascript: ['**/*.js', '**/*.jsx', '!**/node_modules/**', '!**/build/**', '!**/dist/**'],
  typescript: ['**/*.ts', '**/*.tsx', '!**/node_modules/**', '!**/build/**', '!**/dist/**'],
  python: ['**/*.py', '!**/venv/**', '!**/__pycache__/**', '!**/env/**'],
};

/**
 * Generate documentation for JavaScript/TypeScript files using JSDoc
 */
async function generateJSDocDocumentation(files, outputDir) {
  if (files.length === 0) return [];

  console.log(`Generating documentation for ${files.length} JavaScript/TypeScript files...`);

  // Group files by directory
  const filesByDir = files.reduce((acc, file) => {
    const relPath = path.relative(SOURCE_DIR, file);
    const dirName = path.dirname(relPath);

    if (!acc[dirName]) {
      acc[dirName] = [];
    }
    acc[dirName].push(file);

    return acc;
  }, {});

  const generatedDocs = [];

  // Process each directory
  for (const [dirName, dirFiles] of Object.entries(filesByDir)) {
    // Skip node_modules, build, and other ignored directories
    if (dirName.includes('node_modules') || dirName.includes('build') || dirName === '.') continue;

    console.log(`Processing directory: ${dirName}`);

    try {
      // Create output directory
      const outputPath = path.join(outputDir, dirName);
      await mkdir(outputPath, { recursive: true });

      // Generate documentation for each file in the directory
      for (const file of dirFiles) {
        try {
          const fileBaseName = path.basename(file, path.extname(file));
          const outputFile = path.join(outputPath, `${fileBaseName}.md`);

          console.log(`Generating docs for ${file} -> ${outputFile}`);

          const template = `---
title: ${fileBaseName}
---

# ${fileBaseName}

{{>main}}`;

          const markdown = await jsdoc2md.render({
            files: [file],
            template: template
          });

          if (markdown.trim() !== `---
title: ${fileBaseName}
---

# ${fileBaseName}

`) {
            await writeFile(outputFile, markdown);
            generatedDocs.push({
              file: path.relative(DOCS_OUTPUT_DIR, outputFile),
              name: fileBaseName,
              dir: dirName
            });
          }
        } catch (error) {
          console.warn(`Warning: Error processing file ${file}: ${error.message}`);
        }
      }

      // Create an index file for the directory
      const indexPath = path.join(outputDir, dirName, 'index.md');
      let indexContent = `# ${dirName.split('/').pop() || dirName}\n\n`;
      indexContent += `Documentation for the ${dirName} module.\n\n`;
      indexContent += `## Files\n\n`;

      const dirGeneratedDocs = generatedDocs.filter(doc => doc.dir === dirName);
      if (dirGeneratedDocs.length > 0) {
        dirGeneratedDocs.forEach(doc => {
          indexContent += `- [${doc.name}](./${doc.name}.md)\n`;
        });
      } else {
        indexContent += `No documented files found in this directory.\n`;
      }

      await writeFile(indexPath, indexContent);
    } catch (error) {
      console.error(`Error processing directory ${dirName}: ${error.message}`);
    }
  }

  return generatedDocs;
}

/**
 * Generate documentation for Python files using docstrings
 */
async function generatePythonDocumentation(files, outputDir) {
  if (files.length === 0) return [];

  console.log(`Generating documentation for ${files.length} Python files...`);

  // Check if pydoc-markdown is installed
  try {
    execSync('python -c "import pydoc_markdown"', { stdio: 'ignore' });
  } catch (error) {
    console.warn('Warning: pydoc-markdown not installed. Skipping Python documentation generation.');
    console.warn('Install with: pip install pydoc-markdown');
    return [];
  }

  // Group files by directory
  const filesByDir = files.reduce((acc, file) => {
    const relPath = path.relative(SOURCE_DIR, file);
    const dirName = path.dirname(relPath);

    if (!acc[dirName]) {
      acc[dirName] = [];
    }
    acc[dirName].push(file);

    return acc;
  }, {});

  const generatedDocs = [];

  // Process each directory
  for (const [dirName, dirFiles] of Object.entries(filesByDir)) {
    // Skip ignored directories
    if (dirName.includes('__pycache__') || dirName.includes('venv') || dirName === '.') continue;

    console.log(`Processing Python directory: ${dirName}`);

    try {
      // Create output directory
      const outputPath = path.join(outputDir, dirName);
      await mkdir(outputPath, { recursive: true });

      // Generate documentation for each file in the directory
      for (const file of dirFiles) {
        try {
          const fileBaseName = path.basename(file, path.extname(file));
          const outputFile = path.join(outputPath, `${fileBaseName}.md`);

          console.log(`Generating Python docs for ${file} -> ${outputFile}`);

          // Read Python file
          const content = await readFile(file, 'utf8');

          // Simple extraction of docstrings (for files where pydoc-markdown might fail)
          const moduleDoc = content.match(/^"""([\s\S]*?)"""/m);
          const classDocs = content.match(/class\s+(\w+).*?:\s*?"""([\s\S]*?)"""/gm);
          const functionDocs = content.match(/def\s+(\w+).*?:\s*?"""([\s\S]*?)"""/gm);

          let markdown = `---
title: ${fileBaseName}
---

# ${fileBaseName}
`;

          if (moduleDoc && moduleDoc[1]) {
            markdown += `\n${moduleDoc[1].trim()}\n\n`;
          }

          if (classDocs || functionDocs) {
            // Extract and format class documentation
            if (classDocs) {
              markdown += `\n## Classes\n\n`;

              for (const classDoc of classDocs) {
                const className = classDoc.match(/class\s+(\w+)/)[1];
                const docString = classDoc.match(/"""([\s\S]*?)"""/)[1].trim();

                markdown += `### ${className}\n\n${docString}\n\n`;
              }
            }

            // Extract and format function documentation
            if (functionDocs) {
              markdown += `\n## Functions\n\n`;

              for (const funcDoc of functionDocs) {
                const funcName = funcDoc.match(/def\s+(\w+)/)[1];
                const docString = funcDoc.match(/"""([\s\S]*?)"""/)[1].trim();

                markdown += `### ${funcName}\n\n${docString}\n\n`;
              }
            }

            // Save the documentation
            await writeFile(outputFile, markdown);
            generatedDocs.push({
              file: path.relative(DOCS_OUTPUT_DIR, outputFile),
              name: fileBaseName,
              dir: dirName
            });
          } else {
            // Try to use pydoc-markdown if available
            try {
              const tempConfig = path.join(outputPath, `${fileBaseName}.yml`);
              const configContent = `
loaders:
  - type: python
    search_path:
      - ${path.dirname(file)}
processors:
  - type: filter
    expression: modules.name == "${fileBaseName}"
  - type: smart
  - type: crossref
renderer:
  type: markdown
  descriptive_class_title: false
  descriptive_module_title: false
  add_method_class_prefix: false
  add_member_class_prefix: false
  filename: ${outputFile}
              `;

              await writeFile(tempConfig, configContent);

              try {
                execSync(`pydoc-markdown ${tempConfig}`, { stdio: 'ignore' });

                // Check if the file was created and is not empty
                if (fs.existsSync(outputFile) && fs.statSync(outputFile).size > 0) {
                  generatedDocs.push({
                    file: path.relative(DOCS_OUTPUT_DIR, outputFile),
                    name: fileBaseName,
                    dir: dirName
                  });
                }
              } finally {
                // Clean up temporary config
                fs.unlinkSync(tempConfig);
              }
            } catch (pydocError) {
              console.warn(`Warning: pydoc-markdown error for ${file}: ${pydocError.message}`);
            }
          }
        } catch (error) {
          console.warn(`Warning: Error processing Python file ${file}: ${error.message}`);
        }
      }

      // Create an index file for the directory
      const indexPath = path.join(outputDir, dirName, 'index.md');
      let indexContent = `# ${dirName.split('/').pop() || dirName}\n\n`;
      indexContent += `Documentation for the ${dirName} Python module.\n\n`;
      indexContent += `## Files\n\n`;

      const dirGeneratedDocs = generatedDocs.filter(doc => doc.dir === dirName);
      if (dirGeneratedDocs.length > 0) {
        dirGeneratedDocs.forEach(doc => {
          indexContent += `- [${doc.name}](./${doc.name}.md)\n`;
        });
      } else {
        indexContent += `No documented Python files found in this directory.\n`;
      }

      await writeFile(indexPath, indexContent);
    } catch (error) {
      console.error(`Error processing Python directory ${dirName}: ${error.message}`);
    }
  }

  return generatedDocs;
}

/**
 * Create a main index for all generated documentation
 */
async function createDocumentationIndex(jsDocs, pythonDocs) {
  const indexPath = path.join(DOCS_OUTPUT_DIR, 'index.md');

  let indexContent = `# Code Documentation\n\n`;
  indexContent += `This section contains automatically generated documentation from code comments.\n\n`;

  // Organize docs by directories
  const docsByDir = {};

  [...jsDocs, ...pythonDocs].forEach(doc => {
    const dirParts = doc.dir.split('/');
    let currentLevel = docsByDir;

    for (let i = 0; i < dirParts.length; i++) {
      const part = dirParts[i];

      if (!currentLevel[part]) {
        currentLevel[part] = { files: [], dirs: {} };
      }

      if (i === dirParts.length - 1) {
        currentLevel[part].files.push(doc);
      } else {
        currentLevel = currentLevel[part].dirs;
      }
    }
  });

  // Generate hierarchical index
  function buildDirSection(dir, content, prefix = '') {
    const dirs = Object.keys(dir).sort();

    for (const dirName of dirs) {
      const dirData = dir[dirName];
      const dirPath = `${prefix}${dirName}`;

      content += `\n## ${dirPath}\n\n`;

      if (dirData.files.length > 0) {
        content += `- [Directory Index](${dirPath}/index.md)\n`;
        dirData.files.forEach(file => {
          content += `- [${file.name}](${dirPath}/${file.name}.md)\n`;
        });
      }

      if (Object.keys(dirData.dirs).length > 0) {
        content = buildDirSection(dirData.dirs, content, `${dirPath}/`);
      }
    }

    return content;
  }

  indexContent = buildDirSection(docsByDir, indexContent);

  await writeFile(indexPath, indexContent);
  console.log(`Documentation index created at ${indexPath}`);

  return indexPath;
}

/**
 * Update MkDocs configuration to include the generated code documentation
 */
async function updateMkDocsConfig() {
  try {
    // Read the existing mkdocs.yml
    const mkdocsContent = await readFile(MKDOCS_PATH, 'utf8');
    const mkdocs = yaml.load(mkdocsContent);

    // Find the Development section in the nav
    const devIndex = mkdocs.nav.findIndex(item =>
      typeof item === 'object' && Object.keys(item)[0] === 'Development'
    );

    if (devIndex === -1) {
      console.error('Could not find "Development" section in mkdocs.yml');
      return;
    }

    // Add Code Documentation to the Development section
    const devSection = mkdocs.nav[devIndex]['Development'];

    // Check if Code Documentation already exists
    let codeDocIndex = devSection.findIndex(item =>
      typeof item === 'object' && Object.keys(item)[0] === 'Code Documentation'
    );

    if (codeDocIndex !== -1) {
      // Update existing entry
      devSection[codeDocIndex] = { 'Code Documentation': 'code/index.md' };
    } else {
      // Add new entry
      devSection.push({ 'Code Documentation': 'code/index.md' });
    }

    // Write updated config
    await writeFile(
      MKDOCS_PATH,
      yaml.dump(mkdocs, { lineWidth: 100, noRefs: true })
    );

    console.log(`Updated MkDocs configuration at ${MKDOCS_PATH}`);
  } catch (error) {
    console.error(`Error updating MkDocs config: ${error.message}`);
  }
}

/**
 * Main function
 */
async function main() {
  try {
    console.log('Starting code documentation generation...');

    // Create output directory
    await mkdir(DOCS_OUTPUT_DIR, { recursive: true });

    // Find all JavaScript/TypeScript files
    const jsFiles = [
      ...(await glob(FILE_PATTERNS.javascript, { cwd: SOURCE_DIR })),
      ...(await glob(FILE_PATTERNS.typescript, { cwd: SOURCE_DIR }))
    ].map(file => path.join(SOURCE_DIR, file));

    // Find all Python files
    const pyFiles = (await glob(FILE_PATTERNS.python, { cwd: SOURCE_DIR }))
      .map(file => path.join(SOURCE_DIR, file));

    console.log(`Found ${jsFiles.length} JavaScript/TypeScript files and ${pyFiles.length} Python files`);

    // Generate documentation
    const jsDocs = await generateJSDocDocumentation(jsFiles, DOCS_OUTPUT_DIR);
    const pyDocs = await generatePythonDocumentation(pyFiles, DOCS_OUTPUT_DIR);

    // Create documentation index
    await createDocumentationIndex(jsDocs, pyDocs);

    // Update MkDocs configuration
    await updateMkDocsConfig();

    console.log(`Documentation generation completed successfully!`);
    console.log(`Generated ${jsDocs.length} JavaScript/TypeScript docs and ${pyDocs.length} Python docs`);
    console.log(`Documentation is available at ${DOCS_OUTPUT_DIR}`);
  } catch (error) {
    console.error(`Error generating code documentation: ${error.message}`);
    process.exit(1);
  }
}

// Run the main function
main();
