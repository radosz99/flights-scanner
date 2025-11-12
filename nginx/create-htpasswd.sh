#!/bin/bash

# Script to create .htpasswd file for nginx basic authentication
# This protects the API documentation endpoints (/api/docs, /api/redoc, /api/openapi.json)

set -e

HTPASSWD_FILE="$(dirname "$0")/.htpasswd"

echo "=========================================="
echo "Create HTTP Basic Auth for API Docs"
echo "=========================================="
echo ""

# Check if htpasswd command is available
if ! command -v htpasswd &> /dev/null; then
    echo "Error: 'htpasswd' command not found."
    echo ""
    echo "Install apache2-utils (Debian/Ubuntu) or httpd-tools (RedHat/CentOS):"
    echo "  - Ubuntu/Debian: sudo apt-get install apache2-utils"
    echo "  - CentOS/RedHat: sudo yum install httpd-tools"
    echo "  - macOS: htpasswd is included with Apache (should be pre-installed)"
    echo ""
    exit 1
fi

# Prompt for username
read -p "Enter username for API docs access: " username

if [ -z "$username" ]; then
    echo "Error: Username cannot be empty"
    exit 1
fi

# Check if file exists
if [ -f "$HTPASSWD_FILE" ]; then
    echo ""
    echo "Warning: $HTPASSWD_FILE already exists"
    read -p "Do you want to add/update user '$username'? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Aborted."
        exit 0
    fi

    # Update existing user or add new one
    htpasswd -B "$HTPASSWD_FILE" "$username"
else
    # Create new file with first user
    htpasswd -Bc "$HTPASSWD_FILE" "$username"
fi

echo ""
echo "✓ Password file created/updated: $HTPASSWD_FILE"
echo ""
echo "To access API documentation:"
echo "  URL: https://wylot.eu/api/docs"
echo "  Username: $username"
echo "  Password: (the one you just entered)"
echo ""
echo "To add more users, run this script again."
echo "To remove a user: htpasswd -D $HTPASSWD_FILE username"
echo ""
echo "Restart nginx to apply changes:"
echo "  make docker-restart"
echo ""
