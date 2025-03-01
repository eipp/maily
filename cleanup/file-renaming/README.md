# File Standardization Process

This directory contains the script and documentation for standardizing file names in the Maily codebase by removing versioning qualifiers that accumulated during development.

## Purpose

During development, files often accumulate versioning qualifiers such as "enhanced", "optimized", "improved", etc. Before production deployment, these qualifiers should be removed to ensure clean, standardized naming throughout the codebase.

## Contents

- `file-mapping.md`: A mapping document that lists all files to be renamed and their new standardized names
- `smart-rename.sh`: An all-in-one script for identifying, mapping, and renaming files with versioning qualifiers
- `reports/`: Directory containing reports generated during the standardization process

## Usage

### Smart Rename Utility

The `smart-rename.sh` script provides a unified solution for handling the entire file standardization process:

```bash
# Scan for files with versioning qualifiers (no changes made)
./cleanup/file-renaming/smart-rename.sh --scan-only

# Interactive mode: prompt for each file
./cleanup/file-renaming/smart-rename.sh --interactive

# Automatic mode: use high-confidence suggestions
./cleanup/file-renaming/smart-rename.sh --auto

# Execute renaming (must be combined with --interactive or --auto)
./cleanup/file-renaming/smart-rename.sh --interactive --execute

# Update existing mapping file with new candidates
./cleanup/file-renaming/smart-rename.sh --update-mapping
```

The script will:

1. Scan the entire codebase for files with versioning qualifiers
2. Suggest standardized names based on intelligent pattern matching
3. Allow you to interactively review and modify suggestions
4. Create or update the mapping file automatically
5. Optionally execute the renaming process with full reference updates
6. Verify all renames were successful when executing changes
7. Create backups of all modified files

## Safety Measures

The standardization process includes several safety measures:

- All files are backed up before any modifications are made
- The process can be aborted at any time
- A verification step ensures all references are updated correctly
- Detailed logs and reports are generated for review

## After Standardization

After running the standardization process:

1. Review the mapping file and any output logs
2. Run all tests to verify that the application still works as expected
3. Update any documentation that references the renamed files
4. Commit the changes to version control

## Manual Intervention

In some cases, manual intervention may be required:

- If a file with the new name already exists and is different from the old file
- If there are complex references that the script couldn't update automatically
- If there are references to the old files in external systems or documentation

The verification step will identify any issues that require manual intervention.

## Maintenance

To maintain clean file naming in the future:

1. Avoid using versioning qualifiers in file names
2. Use descriptive names that indicate function, not version/status
3. Follow the established naming conventions for each file type
4. Document any naming patterns for future reference
