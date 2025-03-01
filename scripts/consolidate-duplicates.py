#!/usr/bin/env python3
"""
Duplicate Code Finder for Maily Repository

This script analyzes the Maily codebase to identify potential duplicate code patterns
that could be consolidated to improve maintainability and reduce technical debt.
"""

import os
import re
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict

@dataclass
class CodeBlock:
    """Represents a block of code for duplicate analysis"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    hash: str = field(init=False)

    def __post_init__(self):
        # Create a hash of the content for comparison
        self.hash = hashlib.md5(self.content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "line_count": self.end_line - self.start_line + 1,
            "content_preview": self.content[:200] + "..." if len(self.content) > 200 else self.content
        }


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate code blocks"""
    blocks: List[CodeBlock] = field(default_factory=list)

    def add_block(self, block: CodeBlock) -> None:
        """Add a code block to this duplicate group"""
        self.blocks.append(block)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "block_count": len(self.blocks),
            "line_count": self.blocks[0].end_line - self.blocks[0].start_line + 1,
            "blocks": [block.to_dict() for block in self.blocks],
            "content_sample": self.blocks[0].content[:500] + "..." if len(self.blocks[0].content) > 500 else self.blocks[0].content
        }


class DuplicateCodeFinder:
    """Finds duplicate code in the codebase"""

    def __init__(self, root_dir: str, min_lines: int = 5):
        self.root_dir = Path(root_dir)
        self.min_lines = min_lines
        self.exclude_dirs = {
            'node_modules', '.git', '.venv', 'venv', 'env',
            'dist', 'build', '.next', '.cache', 'optimization'
        }
        self.file_extensions = {'.py', '.ts', '.tsx', '.js', '.jsx'}
        self.duplicate_groups: List[DuplicateGroup] = []

    def should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded from analysis"""
        for part in path.parts:
            if part in self.exclude_dirs:
                return True
        return False

    def extract_code_blocks(self, file_path: Path) -> List[CodeBlock]:
        """Extract code blocks from a file for duplicate analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split content into lines
            lines = content.split('\n')
            blocks = []

            # Simple approach: sliding window of min_lines
            for i in range(len(lines) - self.min_lines + 1):
                block_content = '\n'.join(lines[i:i + self.min_lines])
                # Skip blocks that are too simple or just whitespace
                if len(block_content.strip()) < 50 or block_content.count('\n') < self.min_lines - 1:
                    continue
                blocks.append(CodeBlock(
                    content=block_content,
                    file_path=str(file_path.relative_to(self.root_dir)),
                    start_line=i + 1,  # 1-indexed line numbers
                    end_line=i + self.min_lines
                ))

            return blocks
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            return []

    def find_files(self) -> List[Path]:
        """Find all relevant files in the codebase"""
        files = []
        for ext in self.file_extensions:
            for file_path in self.root_dir.glob(f'**/*{ext}'):
                if not self.should_exclude(file_path):
                    files.append(file_path)
        return files

    def find_duplicates(self) -> None:
        """Find duplicate code blocks in the codebase"""
        files = self.find_files()
        print(f"Analyzing {len(files)} files for duplicate code...")

        # Extract code blocks from all files
        all_blocks = []
        for file_path in files:
            blocks = self.extract_code_blocks(file_path)
            all_blocks.extend(blocks)

        print(f"Extracted {len(all_blocks)} code blocks for analysis")

        # Group blocks by hash
        blocks_by_hash = defaultdict(list)
        for block in all_blocks:
            blocks_by_hash[block.hash].append(block)

        # Create duplicate groups for blocks with the same hash
        for hash_value, blocks in blocks_by_hash.items():
            if len(blocks) > 1:
                group = DuplicateGroup()
                for block in blocks:
                    group.add_block(block)
                self.duplicate_groups.append(group)

        # Sort duplicate groups by number of blocks (most duplicated first)
        self.duplicate_groups.sort(key=lambda g: len(g.blocks), reverse=True)

        print(f"Found {len(self.duplicate_groups)} duplicate code patterns")

    def generate_report(self, output_file: str) -> None:
        """Generate a report of duplicate code"""
        report = {
            "summary": {
                "total_duplicate_patterns": len(self.duplicate_groups),
                "total_duplicate_blocks": sum(len(group.blocks) for group in self.duplicate_groups),
                "analysis_date": import_time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "duplicate_patterns": [group.to_dict() for group in self.duplicate_groups]
        }

        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"Duplicate code report written to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Find duplicate code in the Maily codebase")
    parser.add_argument("--root", default=".", help="Root directory to search")
    parser.add_argument("--min-lines", type=int, default=5, help="Minimum number of lines for a code block")
    parser.add_argument("--output", default="optimization/reports/duplicate-code.json", help="Output file for the report")

    args = parser.parse_args()

    finder = DuplicateCodeFinder(args.root, args.min_lines)
    finder.find_duplicates()
    finder.generate_report(args.output)


if __name__ == "__main__":
    import time as import_time
    main()
