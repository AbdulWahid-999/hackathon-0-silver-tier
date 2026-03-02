#!/bin/bash

# MCP Email Server Update Script
# This script handles updating the MCP Email Server

set -e

echo "🔄 Updating MCP Email Server..."

# Check if we're in the right directory
if [ ! -f "mcp-email-server-enhanced.js" ]; then
    echo "❌ Not in the MCP Email Server directory"
    exit 1
fi

# Backup current configuration
echo "💾 Backing up current configuration..."
if [ -f "config.json" ]; then
    cp config.json "config.json.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backed up config.json"
fi

if [ -f ".env" ]; then
    cp .env ".env.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backed up .env"
fi

# Pull latest changes (if using git)
echo "📥 Pulling latest changes..."
if [ -d ".git" ]; then
    git pull origin main
    echo "✅ Pulled latest changes from git"
else
    echo "⚠️  Not a git repository. Skipping git pull."
fi

# Install or update dependencies
echo "📦 Updating dependencies..."
npm install

echo "✅ Dependencies updated"

# Check for configuration changes
echo "🔍 Checking for configuration updates..."
if [ -f "config-enhanced.json" ]; then
    echo "📋 New configuration template available: config-enhanced.json"
    echo "⚠️  Please review and update your config.json if needed"
fi

# Validate configuration
echo "🔍 Validating configuration..."
if [ -f "config.json" ]; then
    if ! grep -q "email.smtp.host" config.json; then
        echo "⚠️  SMTP configuration missing in config.json"
    fi

    if ! grep -q "security.authToken" config.json; then
        echo "⚠️  Authentication token missing in config.json"
    fi
fi

# Test the server
echo "🧪 Testing server startup..."
if timeout 10 node mcp-email-server-enhanced.js > /dev/null 2>&1; then
    echo "✅ Server starts successfully"
else
    echo "❌ Server startup test failed"
    echo "⚠️  Please check the error logs"
    exit 1
fi

# Update log rotation if needed
echo "📊 Updating log rotation..."
if command -v logrotate &> /dev/null; then
    if [ -f "/etc/logrotate.d/mcp-email-server" ]; then
        cat > /etc/logrotate.d/mcp-email-server << EOF
$(pwd)/logs/mcp-email-server-enhanced.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF
        echo "✅ Log rotation updated"
    fi
fi

# Check for systemd service updates
echo "⚙️  Checking systemd service..."
if [ -d "/etc/systemd/system" ] && [ -f "/etc/systemd/system/mcp-email-server.service" ]; then
    # Update the service file if needed
    cat > /etc/systemd/system/mcp-email-server.service << EOF
[Unit]
Description=MCP Email Server for Silver Tier
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=NODE_ENV=production
Environment=PATH=$(pwd)/node_modules/.bin:$PATH
ExecStart=$(which node) mcp-email-server-enhanced.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    echo "✅ systemd service updated"
    echo "💡 Run 'sudo systemctl daemon-reload' to reload the service"
fi

# Update start scripts if they exist
if [ -f "start.sh" ]; then
    cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting MCP Email Server..."
NODE_ENV=production node mcp-email-server-enhanced.js
EOF
    chmod +x start.sh
    echo "✅ start.sh updated"
fi

if [ -f "start-prod.sh" ]; then
    cat > start-prod.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting MCP Email Server in production mode..."
NODE_ENV=production forever start --uid "mcp-email-server" -a -l $(pwd)/logs/forever.log -o $(pwd)/logs/output.log -e $(pwd)/logs/error.log mcp-email-server-enhanced.js
EOF
    chmod +x start-prod.sh
    echo "✅ start-prod.sh updated"
fi

# Run database migrations if any (placeholder)
echo "🔄 Running database migrations..."
echo "⚠️  No database migrations found. Skipping."

# Clean up old log files
echo "🧹 Cleaning up old log files..."
find logs/ -name "mcp-email-server-enhanced.log.*" -mtime +30 -delete 2>/dev/null || true
find logs/ -name "forever.log.*" -mtime +30 -delete 2>/dev/null || true
find logs/ -name "output.log.*" -mtime +30 -delete 2>/dev/null || true
find logs/ -name "error.log.*" -mtime +30 -delete 2>/dev/null || true

echo "✅ Cleanup completed"

# Verify server is running
echo "✅ Update completed successfully!"
echo ""
echo "📋 Post-update steps:"
echo "1. Review configuration changes:"
echo "   - config.json (if template was updated)"
echo "   - .env (if template was updated)"
echo "2. Restart the server:"
echo "   ./stop.sh && ./start.sh"
echo "   or: sudo systemctl restart mcp-email-server"
echo "3. Check logs for any issues:"
echo "   tail -f logs/mcp-email-server-enhanced.log"
echo "4. Run tests to ensure everything works:"
echo "   npm test"
echo ""
echo "🔄 Service restart required:"
echo "   The server needs to be restarted to apply updates"
echo "   Use: ./restart.sh or sudo systemctl restart mcp-email-server"
echo ""
echo "📊 Monitoring:"
echo "   Check logs for any error messages"
echo "   Verify email functionality works"
echo "   Monitor system resources"
echo ""
echo "🔒 Security reminders:"
echo "   - Review security updates in release notes"
echo "   - Check for any new security configuration options"
echo "   - Update any API keys or tokens if required"
echo ""
echo "🎉 Update completed! Server is ready for use."