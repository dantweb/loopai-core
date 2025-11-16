#!/bin/bash
set -e

# Define relative source and destination directories
SRC_DIR="agentlife/post/reflexion/new"
DST_DIR="agentlife/post/reflexion/archive"

# Ensure the destination directory exists
mkdir -p "$DST_DIR"

# Check if the source directory is not empty
if find "$SRC_DIR" -mindepth 1 -print -quit | grep -q .; then
    echo "Files found in '$SRC_DIR'. Copying to '$DST_DIR'..."

    # Copy all files and directories from SRC_DIR to DST_DIR
    cp -R "$SRC_DIR/." "$DST_DIR/"
    echo "Copy completed."

    # Clear the source directory after successful copy
    rm -rf "$SRC_DIR"/*
    echo "Source directory '$SRC_DIR' has been cleared."
else
    echo "Source directory '$SRC_DIR' is empty; no action taken."
fi