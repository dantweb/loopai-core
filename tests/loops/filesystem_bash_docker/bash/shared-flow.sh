#!/bin/bash

# Shared Flow Script
# Version: 2.0.0
# Purpose: Centralized CI/CD Flow Management

# Strict error handling
set -euo pipefail

REPO_DIR="${REPO_DIR:-/var/www/filesystem/g2c-test-py}"
REPO_BRANCH="${REPO_BRANCH:-feature/loopai-g2c-test}"


# Logging Configuration
LOG_FILE="/var/log/shared-flow.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Color Codes for Enhanced Logging
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging Functions
log() {
    local level="${1:-INFO}"
    local message="${2:-No message provided}"
    echo -e "[${TIMESTAMP}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

info() {
    log "${GREEN}INFO${NC}" "$1"
}

warn() {
    log "${YELLOW}WARN${NC}" "$1"
}

error() {
    log "${RED}ERROR${NC}" "$1"
    exit 1
}

setup_ssh_environment() {
    info "Configuring SSH Environment"

    # Check for ssh-agent and OpenSSH
    if ! command -v ssh-agent &> /dev/null; then
        warn "ssh-agent not found. Attempting to locate or use alternatives"

        # Try different package managers or direct binary checks
        if command -v apk &> /dev/null; then
            # Alpine Linux
            apk add --no-cache openssh-client
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            yum install -y openssh-clients
        elif command -v dnf &> /dev/null; then
            # Fedora
            dnf install -y openssh-clients
        elif [[ -f "/etc/os-release" ]]; then
            # Generic fallback
            source /etc/os-release
            warn "Unsupported package manager. OS detected: ${NAME}"
        fi
    fi

    # Verify OpenSSH installation
    if ! command -v ssh-agent &> /dev/null; then
        error "Unable to install or locate ssh-agent"
    fi

    # SSH key paths
    local ssh_key_paths=(
        "/var/www/filesystem/.ssh/id_ed25519"
        "/var/www/filesystem/.ssh/id_rsa"
        "/root/.ssh/id_rsa"
    )

    local valid_key_path=""

    # Find a valid SSH key
    for key_path in "${ssh_key_paths[@]}"; do
        if [[ -f "${key_path}" ]]; then
            info "Attempting to use SSH key: ${key_path}"

            # Validate key
            if validate_ssh_key "${key_path}"; then
                valid_key_path="${key_path}"
                break
            fi
        fi
    done

    # Exit if no valid key found
    if [[ -z "${valid_key_path}" ]]; then
        error "No valid SSH key found"
    fi

 # SSH Config Template
    mkdir -p /root/.ssh
    chmod 700 /root/.ssh  # Correct directory permissions

    cat > /root/.ssh/config << EOL
Host github.com
    IdentityFile ${valid_key_path}
    User git
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
EOL

    # Ensure strict permissions on SSH files
    chmod 600 /root/.ssh/config
    chmod 600 "${valid_key_path}"

    # Ensure proper ownership
    chown -R root:root /root/.ssh

    # Additional permission check
    find /root/.ssh -type f -print0 | while IFS= read -r -d '' file; do
        if [[ $(stat -c '%a' "$file") != "600" ]]; then
            chmod 600 "$file"
        fi
    done

    git config --global --add safe.directory /var/www/filesystem/g2c-test-py
    git config --global --add safe.directory "$REPO_DIR"
    git config --global user.email "daniil.tkachev@gmail.com"
    git config --global user.name "dantweb"


    info "SSH Environment Configured Successfully"
}

# GitHub Connection Test
test_github_connection() {
    info "Testing GitHub SSH Connection"

    # Use SSH with -T flag to disable pseudo-terminal allocation
    if ssh -T git@github.com; then
        info "GitHub SSH Connection Successful"
    else
        # Check if the exit code is 1 (which is expected for GitHub)
        if [ $? -eq 1 ]; then
            info "GitHub SSH Connection Successful (No shell access)"
        else
            error "GitHub SSH Connection Failed"
        fi
    fi
}
# Git Repository Operations
clone_repository() {
    local repo_url="$1"
    local clone_path="$2"
    local branch="${3:-main}"

    info "Cloning Repository: ${repo_url}"

    # Ensure clean clone directory
    rm -rf "${clone_path}"
    mkdir -p "${clone_path}"

    # Clone with depth 1 for faster checkout
    if git clone --depth 1 -b "${branch}" "${repo_url}" "${clone_path}"; then
        info "Repository Cloned Successfully"
    else
        error "Repository Cloning Failed"
    fi
}

# Enhanced SSH Key Validation Function
validate_ssh_key() {
    local key_path="$1"

    # Check file existence
    if [[ ! -f "${key_path}" ]]; then
        echo "Error: Key file does not exist"
        return 1
    fi

    # Check file permissions
    local permissions=$(stat -c '%a' "${key_path}")
    if [[ "${permissions}" != "600" ]]; then
        echo "Warning: Incorrect key permissions. Should be 600."
    fi

    # Attempt multiple validation methods
    if ssh-keygen -l -f "${key_path}" 2>/dev/null; then
        echo "Key appears valid"
        return 0
    fi

    # Fallback validation attempts
    ssh-keygen -y -f "${key_path}" > /dev/null 2>&1 && {
        echo "Key validated using alternative method"
        return 0
    }

    # Detailed error checking
    openssl rsa -in "${key_path}" -check 2>/dev/null && {
        echo "Key validated using OpenSSL"
        return 0
    }

    echo "Error: Unable to validate SSH key"
    return 1
}

validate_repo_settings() {
    # Ensure REPO_DIR is set and exists
    if [ -z "$REPO_DIR" ]; then
        error "Repository directory (REPO_DIR) is not set"
    fi

    # Ensure REPO_BRANCH is set
    if [ -z "$REPO_BRANCH" ]; then
        REPO_BRANCH="main"
        warn "Repository branch not specified. Using default: $REPO_BRANCH"
    fi

    # Optional: Create directory if it doesn't exist
    mkdir -p "$REPO_DIR"

    info "Repository settings validated: DIR=$REPO_DIR, BRANCH=$REPO_BRANCH"
}


# Main Execution Flow
main() {
    info "Starting Shared Flow Process"

    # SSH Environment Setup
    setup_ssh_environment

    # Usage
    validate_ssh_key /var/www/filesystem/.ssh/id_rsa
    test_github_connection

#    # Repository Configuration (customize as needed)
#    local REPO_URL="git@github.com:dantweb/g2c-test-py.git"
#    local REPO_PATH="/var/www/filesystem/g2c-test-py"
#    local REPO_BRANCH="feature/loopai-g2c-test"

    # Clone Repository
#    clone_repository "${REPO_URL}" "${REPO_PATH}" "${REPO_BRANCH}"

    info "Shared Flow Completed Successfully"
}

# Execute Main Function
main "$@"