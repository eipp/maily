#!/usr/bin/env node
/**
 * Maily Database Migration Validation Script
 * This script validates that database migrations have been applied correctly
 * and performs health checks on the database schema and data integrity.
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// ANSI colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m'
};

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    environment: 'staging',
    configPath: null,
    verbose: false
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === '--environment' || arg === '-e') {
      options.environment = args[++i] || 'staging';
    } else if (arg === '--config' || arg === '-c') {
      options.configPath = args[++i];
    } else if (arg === '--verbose' || arg === '-v') {
      options.verbose = true;
    } else if (arg === '--help' || arg === '-h') {
      showHelp();
      process.exit(0);
    } else if (arg.startsWith('--')) {
      console.log(`${colors.yellow}Warning: Unknown option ${arg}${colors.reset}`);
    } else {
      options.environment = arg;
    }
  }
  
  return options;
}

/**
 * Show help text
 */
function showHelp() {
  console.log(`
${colors.cyan}Maily Database Migration Validation Script${colors.reset}

Usage: node validate-migrations.js [options]

Options:
  --environment, -e <env>    Set the environment to test (staging, production)
  --config, -c <path>        Path to environment config file (defaults to config/.env.<environment>)
  --verbose, -v              Show verbose output
  --help, -h                 Show this help message

Examples:
  node validate-migrations.js
  node validate-migrations.js --environment production
  node validate-migrations.js -e staging -v
`);
}

/**
 * Load environment variables from a file
 */
function loadEnvFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const vars = {};
    
    content.split('\n').forEach(line => {
      // Skip comments and empty lines
      if (line.trim().startsWith('#') || !line.trim()) {
        return;
      }
      
      const match = line.match(/^([^=]+)=(.*)$/);
      if (match) {
        const key = match[1].trim();
        let value = match[2].trim();
        
        // Remove quotes if present
        if ((value.startsWith('"') && value.endsWith('"')) || 
            (value.startsWith("'") && value.endsWith("'"))) {
          value = value.substring(1, value.length - 1);
        }
        
        vars[key] = value;
      }
    });
    
    return vars;
  } catch (error) {
    console.error(`${colors.red}Error loading env file: ${error.message}${colors.reset}`);
    return {};
  }
}

/**
 * Connect to the database using the provided connection string
 */
async function connectToDatabase(connectionString) {
  console.log(`${colors.blue}Connecting to database...${colors.reset}`);
  
  try {
    const client = new Client({ connectionString });
    await client.connect();
    console.log(`${colors.green}Connected to database successfully${colors.reset}`);
    return client;
  } catch (error) {
    console.error(`${colors.red}Failed to connect to database: ${error.message}${colors.reset}`);
    throw error;
  }
}

/**
 * Check if the _prisma_migrations table exists
 */
async function checkMigrationsTable(client) {
  console.log(`${colors.blue}Checking for Prisma migrations table...${colors.reset}`);
  
  try {
    const { rows } = await client.query(`
      SELECT EXISTS (
        SELECT FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename = '_prisma_migrations'
      );
    `);
    
    const exists = rows[0].exists;
    
    if (exists) {
      console.log(`${colors.green}✓ Prisma migrations table exists${colors.reset}`);
    } else {
      console.log(`${colors.red}✗ Prisma migrations table does not exist${colors.reset}`);
    }
    
    return exists;
  } catch (error) {
    console.error(`${colors.red}Error checking migrations table: ${error.message}${colors.reset}`);
    return false;
  }
}

/**
 * Get a list of applied migrations from the database
 */
async function getAppliedMigrations(client) {
  console.log(`${colors.blue}Retrieving applied migrations...${colors.reset}`);
  
  try {
    const { rows } = await client.query(`
      SELECT migration_name, finished_at
      FROM _prisma_migrations
      WHERE applied = 1
      ORDER BY finished_at;
    `);
    
    console.log(`${colors.green}✓ Found ${rows.length} applied migrations${colors.reset}`);
    return rows;
  } catch (error) {
    console.error(`${colors.red}Error retrieving migrations: ${error.message}${colors.reset}`);
    return [];
  }
}

/**
 * Get a list of expected migrations from the filesystem
 */
function getExpectedMigrations(migrationsDir) {
  console.log(`${colors.blue}Reading migration files from disk...${colors.reset}`);
  
  try {
    if (!fs.existsSync(migrationsDir)) {
      console.error(`${colors.red}Migrations directory not found: ${migrationsDir}${colors.reset}`);
      return [];
    }
    
    const migrationDirs = fs.readdirSync(migrationsDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name)
      .sort();
    
    console.log(`${colors.green}✓ Found ${migrationDirs.length} migration directories${colors.reset}`);
    return migrationDirs;
  } catch (error) {
    console.error(`${colors.red}Error reading migration files: ${error.message}${colors.reset}`);
    return [];
  }
}

/**
 * Compare applied migrations with expected migrations
 */
function compareMigrations(appliedMigrations, expectedMigrations) {
  console.log(`${colors.blue}Comparing migrations...${colors.reset}`);
  
  const appliedNames = appliedMigrations.map(m => m.migration_name);
  const missingMigrations = expectedMigrations.filter(name => !appliedNames.includes(name));
  const extraMigrations = appliedNames.filter(name => !expectedMigrations.includes(name));
  
  return {
    missingMigrations,
    extraMigrations,
    allApplied: missingMigrations.length === 0
  };
}

/**
 * Validate database schema against expected tables
 */
async function validateDatabaseSchema(client, expectedTables) {
  console.log(`${colors.blue}Validating database schema...${colors.reset}`);
  
  try {
    // Get all tables in the public schema
    const { rows: tables } = await client.query(`
      SELECT tablename
      FROM pg_tables
      WHERE schemaname = 'public'
      AND tablename != '_prisma_migrations';
    `);
    
    const actualTables = tables.map(t => t.tablename);
    
    // Find missing tables
    const missingTables = expectedTables.filter(table => !actualTables.includes(table));
    
    if (missingTables.length === 0) {
      console.log(`${colors.green}✓ All expected tables exist in the database${colors.reset}`);
    } else {
      console.log(`${colors.red}✗ Missing tables: ${missingTables.join(', ')}${colors.reset}`);
    }
    
    return {
      success: missingTables.length === 0,
      actualTables,
      missingTables
    };
  } catch (error) {
    console.error(`${colors.red}Error validating schema: ${error.message}${colors.reset}`);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Check table constraints (foreign keys, indexes)
 */
async function checkTableConstraints(client) {
  console.log(`${colors.blue}Checking database constraints...${colors.reset}`);
  
  try {
    // Check foreign key constraints
    const { rows: fkConstraints } = await client.query(`
      SELECT
        tc.constraint_name,
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM
        information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
      WHERE tc.constraint_type = 'FOREIGN KEY';
    `);
    
    // Check indexes
    const { rows: indexes } = await client.query(`
      SELECT
        tablename,
        indexname,
        indexdef
      FROM
        pg_indexes
      WHERE
        schemaname = 'public';
    `);
    
    console.log(`${colors.green}✓ Found ${fkConstraints.length} foreign key constraints${colors.reset}`);
    console.log(`${colors.green}✓ Found ${indexes.length} indexes${colors.reset}`);
    
    return {
      success: true,
      foreignKeys: fkConstraints,
      indexes: indexes
    };
  } catch (error) {
    console.error(`${colors.red}Error checking constraints: ${error.message}${colors.reset}`);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Perform data integrity checks
 */
async function checkDataIntegrity(client, checks) {
  console.log(`${colors.blue}Performing data integrity checks...${colors.reset}`);
  
  const results = [];
  
  for (const check of checks) {
    try {
      console.log(`${colors.cyan}Running check: ${check.name}${colors.reset}`);
      
      const { rows } = await client.query(check.query);
      const success = check.validate(rows);
      
      if (success) {
        console.log(`${colors.green}✓ ${check.name} passed${colors.reset}`);
      } else {
        console.log(`${colors.red}✗ ${check.name} failed${colors.reset}`);
      }
      
      results.push({
        name: check.name,
        success,
        details: rows
      });
    } catch (error) {
      console.error(`${colors.red}Error running check '${check.name}': ${error.message}${colors.reset}`);
      results.push({
        name: check.name,
        success: false,
        error: error.message
      });
    }
  }
  
  const passedChecks = results.filter(r => r.success).length;
  console.log(`${colors.blue}Data integrity checks: ${passedChecks}/${checks.length} passed${colors.reset}`);
  
  return {
    success: passedChecks === checks.length,
    results
  };
}

/**
 * Main validation function
 */
async function validateDatabase(options) {
  console.log(`${colors.green}Starting database migration validation for ${options.environment} environment${colors.reset}`);
  console.log(`Timestamp: ${new Date().toISOString()}`);
  
  // Load environment variables
  const configPath = options.configPath || path.join('config', `.env.${options.environment}`);
  console.log(`${colors.blue}Loading configuration from ${configPath}${colors.reset}`);
  
  if (!fs.existsSync(configPath)) {
    console.error(`${colors.red}Config file not found: ${configPath}${colors.reset}`);
    process.exit(1);
  }
  
  const envVars = loadEnvFile(configPath);
  
  // Check for required environment variables
  if (!envVars.DATABASE_URL) {
    console.error(`${colors.red}DATABASE_URL not found in config file${colors.reset}`);
    process.exit(1);
  }
  
  // Connect to the database
  let client;
  try {
    client = await connectToDatabase(envVars.DATABASE_URL);
  } catch (error) {
    process.exit(1);
  }
  
  try {
    // Results object to store all validation results
    const results = {
      timestamp: new Date().toISOString(),
      environment: options.environment,
      migrationValidation: null,
      schemaValidation: null,
      constraintValidation: null,
      dataIntegrityValidation: null
    };
    
    // Check migrations table
    const migrationsTableExists = await checkMigrationsTable(client);
    
    // Validate migrations if the table exists
    if (migrationsTableExists) {
      const appliedMigrations = await getAppliedMigrations(client);
      const expectedMigrations = getExpectedMigrations(path.join('prisma', 'migrations'));
      
      const migrationComparison = compareMigrations(appliedMigrations, expectedMigrations);
      
      if (migrationComparison.allApplied) {
        console.log(`${colors.green}✓ All migrations have been applied successfully${colors.reset}`);
      } else {
        console.log(`${colors.red}✗ Missing migrations: ${migrationComparison.missingMigrations.join(', ')}${colors.reset}`);
        
        if (migrationComparison.extraMigrations.length > 0) {
          console.log(`${colors.yellow}! Extra migrations found: ${migrationComparison.extraMigrations.join(', ')}${colors.reset}`);
        }
      }
      
      results.migrationValidation = {
        success: migrationComparison.allApplied,
        appliedMigrations: appliedMigrations.map(m => m.migration_name),
        expectedMigrations,
        missingMigrations: migrationComparison.missingMigrations,
        extraMigrations: migrationComparison.extraMigrations
      };
    } else {
      results.migrationValidation = {
        success: false,
        error: "Migrations table does not exist"
      };
    }
    
    // Expected tables in the database
    const expectedTables = [
      'users',
      'emails',
      'campaigns',
      'contacts',
      'segments',
      'templates',
      'analytics',
      'settings'
    ];
    
    // Validate schema
    results.schemaValidation = await validateDatabaseSchema(client, expectedTables);
    
    // Check constraints
    results.constraintValidation = await checkTableConstraints(client);
    
    // Data integrity checks
    const integrityChecks = [
      {
        name: "User emails are unique",
        query: "SELECT COUNT(*) as count, email FROM users GROUP BY email HAVING COUNT(*) > 1",
        validate: (rows) => rows.length === 0
      },
      {
        name: "All emails have a valid campaign_id",
        query: "SELECT COUNT(*) as count FROM emails WHERE campaign_id NOT IN (SELECT id FROM campaigns)",
        validate: (rows) => rows.length > 0 && parseInt(rows[0].count) === 0
      },
      {
        name: "All contacts have valid data",
        query: "SELECT COUNT(*) as count FROM contacts WHERE email IS NULL OR email = ''",
        validate: (rows) => rows.length > 0 && parseInt(rows[0].count) === 0
      }
    ];
    
    results.dataIntegrityValidation = await checkDataIntegrity(client, integrityChecks);
    
    // Generate summary
    console.log(`\n${colors.magenta}=== Validation Summary ===${colors.reset}`);
    
    const validationResults = [
      { name: "Migration Validation", result: results.migrationValidation.success },
      { name: "Schema Validation", result: results.schemaValidation.success },
      { name: "Constraint Validation", result: results.constraintValidation.success },
      { name: "Data Integrity Validation", result: results.dataIntegrityValidation.success }
    ];
    
    const allPassed = validationResults.every(r => r.result);
    const passedCount = validationResults.filter(r => r.result).length;
    
    for (const validation of validationResults) {
      const status = validation.result
        ? `${colors.green}PASS${colors.reset}`
        : `${colors.red}FAIL${colors.reset}`;
      console.log(`${validation.name}: ${status}`);
    }
    
    console.log(`\nValidation Tests Passed: ${passedCount}/${validationResults.length}`);
    
    if (allPassed) {
      console.log(`\n${colors.green}✓ All database validations passed!${colors.reset}`);
    } else {
      console.log(`\n${colors.red}✗ Some database validations failed.${colors.reset}`);
    }
    
    // Return validation results
    return {
      success: allPassed,
      results
    };
    
  } catch (error) {
    console.error(`${colors.red}Error during validation: ${error.message}${colors.reset}`);
    return {
      success: false,
      error: error.message
    };
  } finally {
    // Close database connection
    if (client) {
      await client.end();
      console.log(`${colors.blue}Database connection closed${colors.reset}`);
    }
  }
}

// Main script execution
async function main() {
  const options = parseArgs();
  
  try {
    const result = await validateDatabase(options);
    process.exit(result.success ? 0 : 1);
  } catch (error) {
    console.error(`${colors.red}Uncaught error: ${error.message}${colors.reset}`);
    process.exit(1);
  }
}

// Run the script
main();