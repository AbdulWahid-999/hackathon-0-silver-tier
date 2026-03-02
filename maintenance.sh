#!/bin/bash

# MCP Email Server Maintenance Script
# This script handles routine maintenance tasks

set -e

echo "🛠️  Performing MCP Email Server maintenance..."

# Check if we're in the right directory
if [ ! -f "mcp-email-server-enhanced.js" ]; then
    echo "❌ Not in the MCP Email Server directory"
    exit 1
fi

# Log rotation check
echo "📊 Checking log rotation..."
if command -v logrotate &> /dev/null; then
    if [ -f "/etc/logrotate.d/mcp-email-server" ]; then
        echo "✅ Log rotation configured"
    else
        echo "⚠️  Log rotation not configured. Setting up..."
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
        echo "✅ Log rotation set up"
    fi
else
    echo "⚠️  logrotate not found. Manual log rotation required."
fi

# Log file cleanup
echo "🧹 Cleaning up old log files..."
find logs/ -name "mcp-email-server-enhanced.log.*" -mtime +30 -delete 2>/dev/null || true
find logs/ -name "forever.log.*" -mtime +30 -delete 2>/dev/null || true
find logs/ -name "output.log.*" -mtime +30 -delete 2>/dev/null || true
find logs/ -name "error.log.*" -mtime +30 -delete 2>/dev/null || true

# Check disk space
echo "💾 Checking disk space usage..."
df -h .

# Check memory usage
echo "🧠 Checking memory usage..."
free -h

# Check if server is running
echo "🔍 Checking server status..."
if command -v forever &> /dev/null; then
    forever list | grep mcp-email-server || echo "❌ Server not running via forever"
else
    ps aux | grep "mcp-email-server-enhanced.js" | grep -v grep || echo "❌ Server not running"
fi

# Check for security updates
echo "🔒 Checking for security updates..."
if command -v npm &> /dev/null; then
    echo "📦 Checking for outdated packages..."
    npm outdated
else
    echo "⚠️  npm not found. Skipping package update check."
fi

# Check configuration syntax
echo "🔍 Validating configuration..."
if [ -f "config.json" ]; then
    echo "✅ Configuration file exists"
    # Basic validation - check for required fields
    if ! grep -q "email.smtp.host" config.json; then
        echo "⚠️  SMTP host not configured in config.json"
    fi

    if ! grep -q "security.authToken" config.json; then
        echo "⚠️  Authentication token not configured in config.json"
    fi
fi

# Check vault directory structure
echo "📁 Checking vault directory structure..."
VAULT_PATH=${VAULT_PATH:-"$(pwd)/test-vault"}
if [ -d "$VAULT_PATH" ]; then
    echo "✅ Vault directory exists: $VAULT_PATH"
    if [ -d "$VAULT_PATH/Needs_Action" ]; then
        echo "✅ Needs_Action directory exists"
    else
        echo "⚠️  Needs_Action directory missing"
    fi

    if [ -d "$VAULT_PATH/Done" ]; then
        echo "✅ Done directory exists"
    else
        echo "⚠️  Done directory missing"
    fi
else
    echo "⚠️  Vault directory not found: $VAULT_PATH"
fi

# Check for orphaned files
echo "🔍 Checking for orphaned files..."
if [ -d "$VAULT_PATH" ]; then
    # Check for files that don't match email pattern
    ORPHANED_FILES=$(find "$VAULT_PATH" -name "*.md" -not -name "EMAIL_*" 2>/dev/null | wc -l)
    if [ "$ORPHANED_FILES" -gt 0 ]; then
        echo "⚠️  Found $ORPHANED_FILES orphaned .md files"
    else
        echo "✅ No orphaned .md files found"
    fi
fi

# Test email functionality (if SMTP configured)
echo "✉️  Testing email functionality..."
if grep -q "email.smtp.user" config.json &> /dev/null && grep -q "email.smtp.pass" config.json &> /dev/null; then
    if node -e "
        const config = require('./config.json');
        const nodemailer = require('nodemailer');

        const transporter = nodemailer.createTransport(config.email.smtp);

        transporter.verify((error, success) => {
            if (error) {
                console.error('❌ SMTP connection failed:', error.message);
                process.exit(1);
            } else {
                console.log('✅ SMTP connection successful');
                process.exit(0);
            }
        });
    "; then
        echo "✅ Email server connection working"
    else
        echo "❌ Email server connection failed"
    fi
else
    echo "⚠️  SMTP credentials not configured. Skipping email test."
fi

# Check recent logs for errors
echo "📋 Checking recent logs for errors..."
if [ -f "logs/mcp-email-server-enhanced.log" ]; then
    ERROR_COUNT=$(grep -i "error\|failed\|exception" logs/mcp-email-server-enhanced.log | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "⚠️  Found $ERROR_COUNT errors in recent logs"
        echo "📋 Recent errors:"
        grep -i "error\|failed\|exception" logs/mcp-email-server-enhanced.log | tail -5
    else
        echo "✅ No errors found in recent logs"
    fi
else
    echo "⚠️  Log file not found"
fi

# Backup important files
echo "💾 Creating backup..."
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_$DATE"
mkdir -p "$BACKUP_DIR"

if [ -f "config.json" ]; then
    cp config.json "$BACKUP_DIR/config.json"
fi

if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/.env"
fi

if [ -f "logs/mcp-email-server-enhanced.log" ]; then
    cp logs/mcp-email-server-enhanced.log "$BACKUP_DIR/server.log"
fi

echo "✅ Backup created in $BACKUP_DIR"

# Performance check
echo "⚡ Checking performance metrics..."
if command -v forever &> /dev/null; then
    forever list | grep mcp-email-server
else
    ps aux | grep "mcp-email-server-enhanced.js" | grep -v grep
fi

# Cleanup temporary files
echo "🧹 Cleaning up temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.log.*" -mtime +7 -delete 2>/dev/null || true

# Security check
echo "🔒 Performing security check..."
if [ -f ".env" ]; then
    # Check if sensitive data is exposed
    if grep -q "EMAIL_PASS=" .env; then
        echo "⚠️  EMAIL_PASS found in .env - ensure file permissions are secure"
    fi

    if grep -q "MCP_AUTH_TOKEN=" .env; then
        echo "⚠️  MCP_AUTH_TOKEN found in .env - ensure file permissions are secure"
    fi
fi

# Check file permissions
echo "🔐 Checking file permissions..."
if [ -f ".env" ]; then
    PERM=$(stat -c "%a" .env 2>/dev/null || stat -f "%A" .env 2>/dev/null)
    if [ "$PERM" != "600" ] && [ "$PERM" != "-rw-------" ]; then
        echo "⚠️  .env file permissions should be 600 (-rw-------)"
        echo "   Current: $PERM"
    else
        echo "✅ .env file permissions are secure"
    fi
fi

# Health check
echo "🩺 Running health check..."
if [ -f "./healthcheck.sh" ]; then
    ./healthcheck.sh
else
    echo "⚠️  healthcheck.sh not found"
fi

echo "✅ Maintenance completed!"
echo ""
echo "📋 Maintenance summary:"
echo "- Log rotation: $(if [ -f "/etc/logrotate.d/mcp-email-server" ]; then echo "✅ Configured"; else echo "⚠️  Not configured"; fi)"
echo "- Disk space: $(df -h . | tail -1 | awk '{print $5}') used"
echo "- Memory usage: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "- Server status: $(if ps aux | grep "mcp-email-server-enhanced.js" | grep -v grep > /dev/null 2>&1; then echo "✅ Running"; else echo "❌ Not running"; fi)"
echo "- Error count: $ERROR_COUNT"
echo "- Backup created: $BACKUP_DIR"
echo ""
echo "🔧 Recommendations:"
echo "- Review any error messages above"
echo "- Check disk space if usage is high"
echo "- Monitor memory usage"
echo "- Ensure regular backups are scheduled"
echo "- Update security tokens periodically"
echo ""
echo "📊 Next maintenance:"
echo "- Schedule regular maintenance (weekly/monthly)"
echo "- Monitor server logs daily"
echo "- Check for software updates regularly"
echo "- Review security configurations periodically"
echo ""
echo "🎉 Maintenance completed successfully!"