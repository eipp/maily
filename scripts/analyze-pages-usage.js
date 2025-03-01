#!/usr/bin/env node
/**
 * Script to analyze pages usage to help prioritize migration to App Router
 * This script analyzes the structure of the pages directory and provides
 * recommendations on migration priority
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const projectRoot = path.resolve(__dirname, '..');
const pagesDir = path.join(projectRoot, 'apps/web/pages');

function getFilesRecursively(dir, ext = ['.js', '.jsx', '.ts', '.tsx'], acc = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      getFilesRecursively(fullPath, ext, acc);
    } else if (
      entry.isFile() &&
      ext.some(extension => entry.name.endsWith(extension))
    ) {
      acc.push(fullPath);
    }
  }

  return acc;
}

function getImportCount(file) {
  try {
    const content = fs.readFileSync(file, 'utf8');
    const importLines = content.match(/import\s+.*\s+from\s+['"].*['"]/g) || [];
    return importLines.length;
  } catch (error) {
    console.error(`Error reading file ${file}:`, error);
    return 0;
  }
}

function getComponentComplexity(file) {
  try {
    const content = fs.readFileSync(file, 'utf8');
    const lineCount = content.split('\n').length;
    const hasServerSideData = content.includes('getServerSideProps') || content.includes('getStaticProps');
    const stateUsageCount = (content.match(/useState\(/g) || []).length;
    const effectUsageCount = (content.match(/useEffect\(/g) || []).length;

    // Higher value means more complex
    return {
      lineCount,
      hasServerSideData,
      stateUsageCount,
      effectUsageCount,
      complexityScore: lineCount * 0.1 + (hasServerSideData ? 5 : 0) + stateUsageCount + effectUsageCount * 2
    };
  } catch (error) {
    console.error(`Error analyzing complexity for ${file}:`, error);
    return {
      lineCount: 0,
      hasServerSideData: false,
      stateUsageCount: 0,
      effectUsageCount: 0,
      complexityScore: 0
    };
  }
}

function getGitCommitFrequency(file) {
  try {
    const result = execSync(`git log --pretty=format:"%h" -- "${file}" | wc -l`, { encoding: 'utf8' });
    return parseInt(result.trim());
  } catch (error) {
    console.error(`Error getting commit frequency for ${file}:`, error);
    return 0;
  }
}

function getGitLastModified(file) {
  try {
    const result = execSync(`git log -1 --pretty=format:"%ad" --date=relative -- "${file}"`, { encoding: 'utf8' });
    return result.trim();
  } catch (error) {
    console.error(`Error getting last modified date for ${file}:`, error);
    return 'unknown';
  }
}

function analyzePagesUsage() {
  const pageFiles = getFilesRecursively(pagesDir);

  // Skip _app, _document, etc.
  const relevantPages = pageFiles.filter(file => {
    const basename = path.basename(file);
    return !basename.startsWith('_') && basename !== 'api';
  });

  const pageAnalytics = relevantPages.map(file => {
    const relativePath = path.relative(projectRoot, file);
    const complexity = getComponentComplexity(file);
    const importCount = getImportCount(file);
    const commitFrequency = getGitCommitFrequency(file);
    const lastModified = getGitLastModified(file);

    // Calculate migration difficulty based on various factors
    const migrationDifficulty = (
      complexity.complexityScore * 0.5 +
      importCount * 0.2 +
      commitFrequency * 0.3
    );

    return {
      path: relativePath,
      complexity,
      importCount,
      commitFrequency,
      lastModified,
      migrationDifficulty: Math.round(migrationDifficulty * 10) / 10,
      migrationPriority: complexity.complexityScore > 20 ? 'High' : complexity.complexityScore > 10 ? 'Medium' : 'Low'
    };
  });

  // Sort by migration difficulty (descending)
  pageAnalytics.sort((a, b) => b.migrationDifficulty - a.migrationDifficulty);

  console.log('\n===== PAGES MIGRATION ANALYSIS =====\n');

  console.log('Top 5 Most Complex Pages (Prioritize for early migration testing):');
  pageAnalytics.slice(0, 5).forEach((page, index) => {
    console.log(`${index + 1}. ${page.path}`);
    console.log(`   Complexity: ${page.complexity.complexityScore.toFixed(1)}, Lines: ${page.complexity.lineCount}, Last Modified: ${page.lastModified}`);
    console.log(`   Has Server Data: ${page.complexity.hasServerSideData}, State Usage: ${page.complexity.stateUsageCount}, Effects: ${page.complexity.effectUsageCount}`);
    console.log(`   Migration Difficulty: ${page.migrationDifficulty} (${page.migrationPriority} priority)`);
    console.log('');
  });

  // Group pages by directory
  const pagesByDirectory = pageAnalytics.reduce((acc, page) => {
    const dir = path.dirname(page.path);
    if (!acc[dir]) {
      acc[dir] = [];
    }
    acc[dir].push(page);
    return acc;
  }, {});

  console.log('\nDirectory Migration Order (recommended):');

  // Calculate average complexity per directory
  const dirComplexity = Object.entries(pagesByDirectory).map(([dir, pages]) => {
    const avgComplexity = pages.reduce((sum, page) => sum + page.complexity.complexityScore, 0) / pages.length;
    const pageCount = pages.length;
    return { dir, avgComplexity, pageCount };
  });

  // Order directories by lowest average complexity (easiest first)
  dirComplexity.sort((a, b) => a.avgComplexity - b.avgComplexity);

  dirComplexity.forEach((dir, index) => {
    console.log(`${index + 1}. ${dir.dir} (${dir.pageCount} pages, Avg Complexity: ${dir.avgComplexity.toFixed(1)})`);
  });

  console.log('\n===== MIGRATION STRATEGY RECOMMENDATION =====\n');
  console.log('1. Start with the simplest directories to build confidence and patterns');
  console.log('2. Create shared layouts early to maximize code reuse');
  console.log('3. For complex pages, consider breaking them into smaller components first');
  console.log('4. Migrate one route group at a time and test thoroughly before proceeding');
  console.log('5. Leave API routes until the end as they need minimal changes');
}

analyzePagesUsage();
