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
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    python_files.append(file_path)
    return python_files

def replace_imports(file_path: str) -> Tuple[bool, List[str]]:
    """Replace HTTP client imports in the given file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except (IOError, FileNotFoundError) as e:
        print(f"Error reading {file_path}: {e}")
        return False, []

    original_content = content
    replacements = []

    # Regular expressions for different import styles
    patterns = [
        # Regular import
        (r"import\s+(requests|aiohttp|urllib3)(\s+as\s+\w+)?", f"import {STANDARD_HTTP_CLIENT}\2"),
        # From import
        (r"from\s+(requests|aiohttp|urllib3)(\.\w+)?\s+import", f"from {STANDARD_HTTP_CLIENT}\2 import"),
    ]

    for pattern, replacement in patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if match[0] in HTTP_CLIENTS_TO_REPLACE:
                pattern_search = re.search(pattern, content)
                if pattern_search:
                    old_import = pattern_search.group(0)
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
