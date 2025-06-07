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

    # Check for changes
    if ! git diff-index --quiet HEAD --; then
        log "Changes detected. Preparing to commit and push."

        # Create commit message
        COMMIT_MESSAGE="Automated pipeline commit: $(date '+%Y-%m-%d %H:%M:%S')"

        # Add, commit, and push changes
        git add .
        git commit -m "$COMMIT_MESSAGE"

        # Push with verbose output
        if git push -v origin "$REPO_BRANCH"; then
            log "Successfully pushed changes to $REPO_BRANCH"
        else
            log "Error: Failed to push changes"
            exit 1
        fi
    else
        log "No changes to commit"
    fi
}

# Execute Main Function
main "$@"