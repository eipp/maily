#!/bin/bash

# Backup Archive and Remove Script for Maily
# This script creates an archive of backup directories and removes them

# Text formatting
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

# Configuration
ARCHIVE_DIR="backup_archives"
DATE_STAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="backup_archive_${DATE_STAMP}.tar.gz"

# Directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Root directory of the project (parent of script dir)
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}${BOLD}==================================${RESET}"
echo -e "${BLUE}${BOLD}  BACKUP ARCHIVE AND REMOVE TOOL  ${RESET}"
echo -e "${BLUE}${BOLD}==================================${RESET}"
echo ""

# Check for existing backup directories
BACKUP_DIRS=$(find "${ROOT_DIR}/backups" -type d -depth 1 -not -path "*/\.*" 2>/dev/null)

if [ -z "$BACKUP_DIRS" ]; then
  echo -e "${YELLOW}No backup directories found. Nothing to archive.${RESET}"
  exit 0
fi

# Calculate initial sizes
INITIAL_SIZE=$(du -sh "${ROOT_DIR}" | cut -f1)
BACKUP_SIZE=$(du -sh "${ROOT_DIR}/backups" | cut -f1)

echo -e "${BLUE}Found backup directories to archive:${RESET}"
echo "$BACKUP_DIRS" | sed 's|^.*/||' | while read -r dir; do
  echo "- $dir"
done

echo ""
echo -e "${BLUE}Current repository size: ${BOLD}${INITIAL_SIZE}${RESET}"
echo -e "${BLUE}Backup directories size: ${BOLD}${BACKUP_SIZE}${RESET}"
echo ""

# Prompt before continuing
echo -e "${YELLOW}${BOLD}This script will archive backup directories and optionally remove them.${RESET}"
read -p "Continue with archiving? (y/n): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Operation canceled."
  exit 0
fi

# Create archive directory if it doesn't exist
mkdir -p "${ROOT_DIR}/${ARCHIVE_DIR}"

# Create the archive
echo -e "\n${BLUE}Creating archive of backup directories...${RESET}"
# macOS compatible version - create list of backup directories first
BACKUP_LIST=""
for dir in $(find "${ROOT_DIR}/backups" -type d -depth 1 -not -path "*/\.*" 2>/dev/null); do
  # Get just the directory name relative to ROOT_DIR
  rel_dir="${dir#$ROOT_DIR/}"
  BACKUP_LIST="$BACKUP_LIST $rel_dir"
done

# Create tar archive from the backup list
if [ -n "$BACKUP_LIST" ]; then
  (cd "${ROOT_DIR}" && tar -czf "${ROOT_DIR}/${ARCHIVE_DIR}/${ARCHIVE_NAME}" $BACKUP_LIST)
else
  echo -e "${YELLOW}No backup directories found matching the pattern.${RESET}"
  exit 1
fi

# Check if archive was created successfully
if [ -f "${ROOT_DIR}/${ARCHIVE_DIR}/${ARCHIVE_NAME}" ]; then
  ARCHIVE_SIZE=$(du -sh "${ROOT_DIR}/${ARCHIVE_DIR}/${ARCHIVE_NAME}" | cut -f1)
  echo -e "${GREEN}Archive created successfully: ${ARCHIVE_DIR}/${ARCHIVE_NAME} (${ARCHIVE_SIZE})${RESET}"

  # Ask if user wants to remove original backup directories
  echo ""
  read -p "Remove original backup directories to save space? (y/n): " remove_confirm

  if [[ "$remove_confirm" == "y" || "$remove_confirm" == "Y" ]]; then
    echo -e "\n${BLUE}Removing original backup directories...${RESET}"
    # Remove all direct subdirectories of backups, not matching hidden directories
    find "${ROOT_DIR}/backups" -type d -depth 1 -not -path "*/\.*" -exec rm -rf {} \; 2>/dev/null
    echo -e "${GREEN}Original backup directories removed.${RESET}"

    # Calculate final size
    FINAL_SIZE=$(du -sh "${ROOT_DIR}" | cut -f1)
    echo -e "\n${BLUE}${BOLD}Operation Complete!${RESET}"
    echo -e "Initial repository size: ${INITIAL_SIZE}"
    echo -e "Final repository size: ${FINAL_SIZE}"
    echo -e "Archive size: ${ARCHIVE_SIZE}"
    echo -e "Archive location: ${ROOT_DIR}/${ARCHIVE_DIR}/${ARCHIVE_NAME}"
    echo ""
    echo -e "${GREEN}For safety, consider moving the archive to external storage.${RESET}"
  else
    echo -e "\n${YELLOW}Original backup directories kept intact.${RESET}"
    echo -e "${YELLOW}Note: Repository size will remain larger until backups are removed.${RESET}"
  fi
else
  echo -e "${RED}Failed to create archive. Check permissions and disk space.${RESET}"
  exit 1
fi
