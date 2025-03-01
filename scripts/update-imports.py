#!/usr/bin/env python3
"""
Import Statement Updater for Maily Repository

This script updates import statements in the Maily codebase to reflect
the new locations of modules after deprecated components have been removed.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set, Any
from dataclasses import dataclass

# Define the import replacements
# Format: regex pattern -> replacement
IMPORT_REPLACEMENTS = {
    # AI package replacements
    r'from\s+packages\.ai(?:\.[\w\.]+)?\s+import': 'from apps.api.ai import',
    r'import\s+packages\.ai(?:\.[\w\.]+)?\s+as': 'import apps.api.ai as',

    # Model module replacements
    r'from\s+apps\.api\.models(?:\.[\w\.]+)?\s+import': 'from apps.api.octotools import',
    r'import\s+apps\.api\.models(?:\.[\w\.]+)?\s+as': 'import apps.api.octotools as',

    # Usage monitoring replacements
    r'from\s+apps\.api\.middleware\.usage_monitoring\s+import.*': '# REMOVED: Usage monitoring import',
    r'from\s+apps\.api\.services\.usage_monitoring_service\s+import.*': '# REMOVED: Usage monitoring service import',

    # Trust infrastructure replacements
    r'from\s+apps\.trust-infrastructure(?:\.[\w\.]+)?\s+import.*': '# REMOVED: Trust infrastructure import',
    r'import\s+apps\.trust-infrastructure(?:\.[\w\.]+)?\s+as.*': '# REMOVED: Trust infrastructure import',
}


def update_file_imports(file_path: Path) -> Tuple[int, List[Dict[str, str]]]:
    """
    Update import statements in a file.

    Args:
        file_path: Path to the file to update

    Returns:
        Tuple of (number of replacements, list of changes made)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = []

        # Apply each replacement pattern
        for pattern, replacement in IMPORT_REPLACEMENTS.items():
            # Find all matches
            matches = list(re.finditer(pattern, content, re.MULTILINE))

            # Apply replacements in reverse order to avoid messing up indices
            for match in reversed(matches):
                # Get the full line containing the match
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_end = content.find('\n', match.end())
                if line_end == -1:
                    line_end = len(content)

                original_line = content[line_start:line_end]

                # Replace just the matched part
                new_line = original_line[:match.start() - line_start] + \
                           replacement + \
                           original_line[match.end() - line_start:]

                # Update the content
                content = content[:line_start] + new_line + content[line_end:]

                # Record the change
                changes.append({
                    "file": str(file_path),
                    "original": original_line.strip(),
                    "updated": new_line.strip()
                })

        # Only write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return len(changes), changes

        return 0, []

    except Exception as e:
        print(f"Error updating {file_path}: {e}", file=sys.stderr)
        return 0, []


def find_files(root_dir: Path, exclude_dirs: List[str], file_extensions: List[str]) -> List[Path]:
    """
    Find all relevant files in the codebase.

    Args:
        root_dir: Root directory to search
        exclude_dirs: Directories to exclude
        file_extensions: File extensions to include

    Returns:
        List of file paths
    """
    files = []

    for ext in file_extensions:
        for file_path in root_dir.glob(f'**/*{ext}'):
            # Check if the file is in an excluded directory
            if any(exclude in file_path.parts for exclude in exclude_dirs):
                continue

            files.append(file_path)

    return files


def update_imports(
    root_dir: str,
    exclude_dirs: List[str] = None,
    file_extensions: List[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Update import statements in the codebase.

    Args:
        root_dir: Root directory to search
        exclude_dirs: Directories to exclude
        file_extensions: File extensions to include
        dry_run: If True, don't actually modify files

    Returns:
        Dictionary with summary of changes
    """
    if exclude_dirs is None:
        exclude_dirs = ['node_modules', '.git', '.venv', 'venv', 'env', 'dist', 'build']

    if file_extensions is None:
        file_extensions = ['.py', '.ts', '.tsx', '.js', '.jsx']

    root_path = Path(root_dir)
    files = find_files(root_path, exclude_dirs, file_extensions)

    print(f"Found {len(files)} files to check for import updates")

    total_replacements = 0
    modified_files = 0
    all_changes = []

    for file_path in files:
        if dry_run:
            print(f"Would check {file_path}")
            continue

        replacements, changes = update_file_imports(file_path)

        if replacements > 0:
            print(f"Updated {replacements} imports in {file_path}")
            modified_files += 1
            total_replacements += replacements
            all_changes.extend(changes)

    summary = {
        "total_files": len(files),
        "modified_files": modified_files,
        "total_replacements": total_replacements,
        "dry_run": dry_run,
        "changes": all_changes
    }

    print(f"\nSummary:")
    print(f"  Total files processed: {len(files)}")
    print(f"  Files modified: {modified_files}")
    print(f"  Total replacements: {total_replacements}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Update import statements in the Maily codebase")
    parser.add_argument("--root", default=".", help="Root directory to search")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually modify files")
    parser.add_argument("--output", default="optimization/reports/import-updates.json", help="Output file for the report")

    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Update imports and get summary
    summary = update_imports(args.root, dry_run=args.dry_run)

    # Write summary to file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"Import update report written to {args.output}")


if __name__ == "__main__":
    main()
