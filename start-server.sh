#!/bin/bash

echo "Starting MCP Email Server..."
echo "Using vault path: $VAULT_PATH"
echo "SMTP user: $EMAIL_USER"

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Start the server
node mcp-email-server.js