#!/bin/bash

# Source shared flow
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/shared-flow.sh"

main() {
    # Setup SSH Environment
    setup_ssh_environment || exit 1

    # Check if repository directory exists
    if [ ! -d "$REPO_DIR" ]; then
        log "Error: Repository directory does not exist: $REPO_DIR"
        exit 1
    fi

    # Change to repository directory
    cd "$REPO_DIR" || exit 1


    # Fetch and reset to latest remote state
    git fetch origin "$REPO_BRANCH"
    git reset --hard "origin/$REPO_BRANCH"
    git clean -fd

    log "Repository updated to latest state on $REPO_BRANCH"
}

# Execute Main Function
main "$@"