#!/usr/bin/env node

/**
 * Git commit-msg hook to enforce standardized commit message format
 *
 * Installation:
 * 1. Make this file executable: chmod +x scripts/commit-msg-hook.js
 * 2. Create a symlink to this file in .git/hooks/commit-msg:
 *    ln -sf ../../scripts/commit-msg-hook.js .git/hooks/commit-msg
 * 3. Or use husky to manage git hooks
 */

const fs = require('fs');
const path = require('path');

// Get the commit message file path from the first argument
const commitMsgFile = process.argv[2];

// Conventional Commit format: <type>(<scope>): <subject>
// Example: feat(auth): add OAuth2 support
const COMMIT_PATTERN = /^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9-]+\))?: .{1,100}$/;

// Read the commit message
try {
  const message = fs.readFileSync(commitMsgFile, 'utf8').trim();

  // Skip merge commits
  if (message.startsWith('Merge ')) {
    process.exit(0);
  }

  const firstLine = message.split('\n')[0];

  if (!COMMIT_PATTERN.test(firstLine)) {
    console.error('\x1b[31mError: Invalid commit message format\x1b[0m');
    console.error('\x1b[33mCommit message must follow the format:\x1b[0m');
    console.error('\x1b[33m  <type>(<scope>): <subject>\x1b[0m');
    console.error('\x1b[33mExamples:\x1b[0m');
    console.error('\x1b[32m  feat(auth): add OAuth2 support\x1b[0m');
    console.error('\x1b[32m  fix(api): resolve user creation issue\x1b[0m');
    console.error('\x1b[32m  docs(readme): update installation instructions\x1b[0m');
    console.error('\x1b[33mAllowed types:\x1b[0m');
    console.error('\x1b[33m  build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test\x1b[0m');
    process.exit(1);
  }
} catch (error) {
  console.error(`Error reading commit message: ${error.message}`);
  process.exit(1);
}

process.exit(0);
