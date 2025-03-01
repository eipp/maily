#!/usr/bin/env node

/**
 * API Documentation Generator
 *
 * This script generates comprehensive API documentation from the OpenAPI specification.
 * It creates Markdown files for API endpoints, organized by tags/categories.
 *
 * Features:
 * - Generates individual markdown files for each API tag
 * - Creates an index page linking to all API documentation
 * - Includes request/response examples, schemas, and status codes
 * - Updates the MkDocs configuration to include the generated files
 * - Validates the OpenAPI spec before generation
 *
 * Usage: node scripts/generate-api-docs.js
 */

const fs = require('fs');
const path = require('path');
const util = require('util');
const yaml = require('js-yaml');
const SwaggerParser = require('@apidevtools/swagger-parser');
const OpenAPISnippet = require('openapi-snippet');

// Convert callbacks to promises
const readFile = util.promisify(fs.readFile);
const writeFile = util.promisify(fs.writeFile);
const mkdir = util.promisify(fs.mkdir);
const readdir = util.promisify(fs.readdir);

// Configuration
const OPENAPI_PATH = path.join(__dirname, '..', 'openapi.json');
const DOCS_API_DIR = path.join(__dirname, '..', 'docs', 'api');
const MKDOCS_PATH = path.join(__dirname, '..', 'mkdocs.yml');
const API_INDEX_PATH = path.join(DOCS_API_DIR, 'index.md');

// Supported code snippet languages
const SNIPPET_LANGUAGES = ['curl', 'node', 'python', 'go', 'ruby'];

/**
 * Generate a markdown code block with language
 */
function codeBlock(code, language = '') {
  return `\`\`\`${language}\n${code}\n\`\`\``;
}

/**
 * Generate a parameter table from OpenAPI parameters
 */
function generateParameterTable(parameters) {
  if (!parameters || parameters.length === 0) {
    return 'This endpoint does not require any parameters.';
  }

  let table = '| Name | Located In | Required | Type | Description |\n';
  table += '|------|------------|----------|------|-------------|\n';

  parameters.forEach(param => {
    const required = param.required ? 'Yes' : 'No';
    const type = param.schema ? param.schema.type : param.type;
    table += `| ${param.name} | ${param.in} | ${required} | ${type} | ${param.description || ''} |\n`;
  });

  return table;
}

/**
 * Generate response section for an endpoint
 */
function generateResponseSection(responses) {
  if (!responses || Object.keys(responses).length === 0) {
    return 'No response information available.';
  }

  let responseSection = '';

  Object.entries(responses).forEach(([statusCode, response]) => {
    responseSection += `### Status: ${statusCode}\n\n`;
    responseSection += `${response.description || 'No description provided.'}\n\n`;

    if (response.content && response.content['application/json']) {
      if (response.content['application/json'].example) {
        responseSection += '**Example:**\n\n';
        responseSection += codeBlock(
          JSON.stringify(response.content['application/json'].example, null, 2),
          'json'
        );
        responseSection += '\n\n';
      }

      if (response.content['application/json'].schema) {
        responseSection += '**Schema:**\n\n';
        if (response.content['application/json'].schema.$ref) {
          const schemaName = response.content['application/json'].schema.$ref.split('/').pop();
          responseSection += `Reference to \`${schemaName}\`\n\n`;
        } else {
          responseSection += codeBlock(
            JSON.stringify(response.content['application/json'].schema, null, 2),
            'json'
          );
          responseSection += '\n\n';
        }
      }
    }
  });

  return responseSection;
}

/**
 * Generate code snippets for an endpoint
 */
async function generateCodeSnippets(openapi, path, method) {
  try {
    const results = OpenAPISnippet.getEndpointSnippets(
      openapi,
      path,
      method,
      SNIPPET_LANGUAGES
    );

    let snippetsSection = '### Code Samples\n\n';
    snippetsSection += 'These samples show how to call this API endpoint using various programming languages and tools.\n\n';

    results.snippets.forEach(snippet => {
      snippetsSection += `#### ${snippet.title}\n\n`;
      snippetsSection += codeBlock(snippet.content, snippet.language);
      snippetsSection += '\n\n';
    });

    return snippetsSection;
  } catch (error) {
    console.warn(`Warning: Could not generate code snippets for ${method.toUpperCase()} ${path}: ${error.message}`);
    return '<!-- Code snippets generation failed -->\n\n';
  }
}

/**
 * Generate schema definitions section
 */
function generateSchemaSection(schemas) {
  if (!schemas || Object.keys(schemas).length === 0) {
    return '';
  }

  let schemaSection = '## Schema Definitions\n\n';
  schemaSection += 'This section details the structure of request and response objects used in the API.\n\n';

  Object.entries(schemas).forEach(([schemaName, schema]) => {
    schemaSection += `### ${schemaName}\n\n`;

    if (schema.description) {
      schemaSection += `${schema.description}\n\n`;
    }

    if (schema.type === 'object' && schema.properties) {
      schemaSection += '**Properties:**\n\n';
      schemaSection += '| Property | Type | Required | Description |\n';
      schemaSection += '|----------|------|----------|-------------|\n';

      Object.entries(schema.properties).forEach(([propName, propDetails]) => {
        const required = schema.required && schema.required.includes(propName) ? 'Yes' : 'No';
        const type = propDetails.type || (propDetails.$ref ? 'object' : 'any');
        const description = propDetails.description || '';

        schemaSection += `| ${propName} | ${type} | ${required} | ${description} |\n`;
      });

      schemaSection += '\n';
    } else {
      schemaSection += codeBlock(JSON.stringify(schema, null, 2), 'json');
      schemaSection += '\n\n';
    }
  });

  return schemaSection;
}

/**
 * Generate markdown documentation for a single endpoint
 */
async function generateEndpointDoc(openapi, path, methodName, methodObj, tag) {
  let doc = `## ${methodObj.summary || path}\n\n`;

  if (methodObj.description) {
    doc += `${methodObj.description}\n\n`;
  }

  // Endpoint details
  doc += `**URL:** \`${path}\`\n\n`;
  doc += `**Method:** \`${methodName.toUpperCase()}\`\n\n`;

  // Rate limiting
  if (methodObj['x-rateLimit']) {
    doc += `**Rate Limit:** ${methodObj['x-rateLimit'].limit} requests per ${methodObj['x-rateLimit'].period}\n\n`;
  }

  // Authentication
  if (openapi.security) {
    doc += '**Authentication Required:** Yes\n\n';
  }

  // Parameters
  if (methodObj.parameters && methodObj.parameters.length > 0) {
    doc += '### Parameters\n\n';
    doc += generateParameterTable(methodObj.parameters);
    doc += '\n\n';
  }

  // Request Body
  if (methodObj.requestBody) {
    doc += '### Request Body\n\n';

    if (methodObj.requestBody.description) {
      doc += `${methodObj.requestBody.description}\n\n`;
    }

    if (methodObj.requestBody.required) {
      doc += '**Required:** Yes\n\n';
    }

    if (methodObj.requestBody.content && methodObj.requestBody.content['application/json']) {
      if (methodObj.requestBody.content['application/json'].schema) {
        doc += '**Schema:**\n\n';

        if (methodObj.requestBody.content['application/json'].schema.$ref) {
          const schemaName = methodObj.requestBody.content['application/json'].schema.$ref.split('/').pop();
          doc += `Reference to \`${schemaName}\`\n\n`;
        } else {
          doc += codeBlock(
            JSON.stringify(methodObj.requestBody.content['application/json'].schema, null, 2),
            'json'
          );
        }
        doc += '\n\n';
      }

      if (methodObj.requestBody.content['application/json'].example) {
        doc += '**Example:**\n\n';
        doc += codeBlock(
          JSON.stringify(methodObj.requestBody.content['application/json'].example, null, 2),
          'json'
        );
        doc += '\n\n';
      }
    }
  }

  // Responses
  doc += '### Responses\n\n';
  doc += generateResponseSection(methodObj.responses);
  doc += '\n\n';

  // Code Snippets
  doc += await generateCodeSnippets(openapi, path, methodName);

  return doc;
}

/**
 * Generate markdown documentation for a specific tag
 */
async function generateTagDoc(openapi, tag) {
  // Create filename from tag
  const filename = `${tag.name.toLowerCase().replace(/\s+/g, '-')}.md`;
  const outputPath = path.join(DOCS_API_DIR, filename);

  console.log(`Generating documentation for tag: ${tag.name}`);

  let doc = `# ${tag.name} API\n\n`;

  if (tag.description) {
    doc += `${tag.description}\n\n`;
  }

  // Find all endpoints with this tag
  let endpoints = [];

  for (const [pathKey, pathObj] of Object.entries(openapi.paths)) {
    for (const [method, methodObj] of Object.entries(pathObj)) {
      if (methodObj.tags && methodObj.tags.includes(tag.name)) {
        endpoints.push({ path: pathKey, method, methodObj });
      }
    }
  }

  if (endpoints.length === 0) {
    doc += `No endpoints found for the ${tag.name} tag.\n`;
  } else {
    // Table of Contents
    doc += `## Endpoints\n\n`;

    endpoints.forEach(endpoint => {
      doc += `* [${endpoint.methodObj.summary || endpoint.path}](#${endpoint.method.toLowerCase()}-${endpoint.path.replace(/\//g, '').replace(/[{}]/g, '')})`;
      doc += '\n';
    });

    doc += '\n';

    // Generate detailed documentation for each endpoint
    for (const endpoint of endpoints) {
      doc += await generateEndpointDoc(
        openapi,
        endpoint.path,
        endpoint.method,
        endpoint.methodObj,
        tag.name
      );
      doc += '---\n\n';
    }
  }

  // Write to file
  await writeFile(outputPath, doc);
  console.log(`Documentation written to ${outputPath}`);

  return {
    name: tag.name,
    file: filename
  };
}

/**
 * Generate API index page
 */
async function generateApiIndex(tags) {
  let indexContent = `# API Documentation\n\n`;
  indexContent += `This documentation provides details about the Maily API endpoints, request parameters, response formats, and example code snippets.\n\n`;

  indexContent += `## API Base URLs\n\n`;
  indexContent += `| Environment | Base URL |\n`;
  indexContent += `|-------------|----------|\n`;
  indexContent += `| Production | \`https://api.maily.app/v1\` |\n`;
  indexContent += `| Staging | \`https://staging-api.maily.app/v1\` |\n`;
  indexContent += `| Development | \`http://localhost:8000/v1\` |\n\n`;

  indexContent += `## Authentication\n\n`;
  indexContent += `All API requests require authentication using an API key. You can obtain an API key from the [Maily developer console](https://console.justmaily.com).\n\n`;
  indexContent += `Include your API key in the \`X-API-Key\` header with every request:\n\n`;

  indexContent += `\`\`\`\n`;
  indexContent += `X-API-Key: your-api-key-here\n`;
  indexContent += `\`\`\`\n\n`;

  indexContent += `## Rate Limiting\n\n`;
  indexContent += `API endpoints have rate limits to ensure fair usage. When you exceed the rate limit, you'll receive a \`429 Too Many Requests\` response with a \`Retry-After\` header indicating how many seconds to wait before retrying.\n\n`;

  indexContent += `## Available API Categories\n\n`;
  indexContent += `| Category | Description |\n`;
  indexContent += `|----------|-------------|\n`;

  tags.forEach(tag => {
    indexContent += `| [${tag.name}](./${tag.file}) | ${tag.description || 'API operations related to ' + tag.name} |\n`;
  });

  await writeFile(API_INDEX_PATH, indexContent);
  console.log(`API index written to ${API_INDEX_PATH}`);
}

/**
 * Update MkDocs configuration to include the API documentation
 */
async function updateMkDocsConfig(tags) {
  try {
    // Read the existing mkdocs.yml
    const mkdocsContent = await readFile(MKDOCS_PATH, 'utf8');
    const mkdocs = yaml.load(mkdocsContent);

    // Find the 'Technical Reference' section in the nav
    const technicalRefIndex = mkdocs.nav.findIndex(item =>
      typeof item === 'object' && Object.keys(item)[0] === 'Technical Reference'
    );

    if (technicalRefIndex === -1) {
      console.error('Could not find "Technical Reference" section in mkdocs.yml');
      return;
    }

    // Check if 'API Reference' already exists
    const techRef = mkdocs.nav[technicalRefIndex]['Technical Reference'];
    let apiRefIndex = -1;

    techRef.forEach((item, index) => {
      if (typeof item === 'object' && Object.keys(item)[0] === 'API Reference') {
        apiRefIndex = index;
      }
    });

    // Create API Reference structure
    const apiRef = {
      'API Reference': [
        { 'Overview': 'api/index.md' }
      ]
    };

    // Add each tag documentation file
    tags.forEach(tag => {
      apiRef['API Reference'].push({
        [tag.name]: `api/${tag.file}`
      });
    });

    // Update or add the API Reference section
    if (apiRefIndex !== -1) {
      techRef[apiRefIndex] = apiRef;
    } else {
      // Find the simple string 'API Reference' entry
      const simpleApiRefIndex = techRef.findIndex(item =>
        typeof item === 'object' && Object.keys(item)[0] === 'API Reference'
      );

      if (simpleApiRefIndex !== -1) {
        techRef[simpleApiRefIndex] = apiRef;
      } else {
        techRef.push(apiRef);
      }
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
    console.log('Starting API documentation generation...');

    // Validate and parse OpenAPI spec
    console.log(`Validating OpenAPI specification at ${OPENAPI_PATH}...`);
    const openapi = await SwaggerParser.validate(OPENAPI_PATH);
    console.log('OpenAPI specification is valid');

    // Create API docs directory if it doesn't exist
    await mkdir(DOCS_API_DIR, { recursive: true });

    // Generate documentation for each tag
    const tagDocs = [];

    for (const tag of openapi.tags) {
      const tagDoc = await generateTagDoc(openapi, tag);
      tagDocs.push({
        name: tag.name,
        file: tagDoc.file,
        description: tag.description
      });
    }

    // Generate API index
    await generateApiIndex(tagDocs);

    // Update MkDocs configuration
    await updateMkDocsConfig(tagDocs);

    console.log('API documentation generation completed successfully!');
  } catch (error) {
    console.error(`Error generating API documentation: ${error.message}`);
    process.exit(1);
  }
}

// Run the main function
main();
