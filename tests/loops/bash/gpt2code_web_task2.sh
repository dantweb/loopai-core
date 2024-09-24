#!/bin/bash

# Function to display an error message and exit
function error_exit {
    echo "$1" 1>&2
    exit 1
}

# Function to remove all binary files from a directory recursively
function remove_binaries {
    find "$1" -type f -exec sh -c 'file --mime "{}" | grep -q binary' \; -exec rm -f {} \;
}

# Function to find the next available backup directory index
function get_next_backup_dir {
    local base_dir="$1"
    local index=1

    while [[ -d "${base_dir}.bkp.${index}" ]]; do
        ((index++))
    done

    echo "${base_dir}.bkp.${index}"
}

# Define paths
SRC_DIR="/home/dtkachev/PycharmProjects/loopAI"
BASE_BACKUP_DIR="$SRC_DIR/var/filesystem/web_task2"
BACKUP_DIR=$(get_next_backup_dir "$BASE_BACKUP_DIR")
DEST_DIR="$SRC_DIR/var/filesystem/web_task2"
MASTER_TASK_FILE="MASTER_TASK.txt"
WEB_USERS_DIR="$DEST_DIR/web/users"

# Backup the directory
cp -rf "$DEST_DIR" "$BACKUP_DIR" || error_exit "Failed to backup $DEST_DIR to $BACKUP_DIR"
rm -rf "$DEST_DIR" || error_exit "Failed to remove $DEST_DIR"
mkdir -p "$DEST_DIR" || error_exit "Failed to create $DEST_DIR"

# Copy the web directory excluding node_modules
rsync -av --exclude='node_modules' --exclude='package-lock.json' "$SRC_DIR/web/" "$DEST_DIR/web" || error_exit "Failed to copy web directory to $DEST_DIR"
cp "$BACKUP_DIR/$MASTER_TASK_FILE" "$DEST_DIR/$MASTER_TASK_FILE" || error_exit "Failed to copy $MASTER_TASK_FILE"

# Remove unnecessary directories and files
rm -rf "$DEST_DIR/__pycache__" || error_exit "Failed to remove __pycache__"
rm -rf "$DEST_DIR/react" || error_exit "Failed to remove react"
rm -rf "$WEB_USERS_DIR" || error_exit "Failed to remove $WEB_USERS_DIR"

# Remove all binary files from the web/users directory
remove_binaries "$DEST_DIR" || error_exit "Failed to remove binary files from $DEST_DIR"

echo "Script executed successfully."
