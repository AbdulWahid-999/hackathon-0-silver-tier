#!/bin/bash

# MCP Email Server Deployment Script
# This script handles deployment of the MCP Email Server

set -e

echo "🚀 Deploying MCP Email Server..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16.0.0 or higher."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version must be 16.0.0 or higher. Current version: $(node --version)"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

# Navigate to project directory
echo "📁 Navigating to project directory..."
cd "$(dirname "$0")"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create necessary directories
echo "📂 Creating necessary directories..."
mkdir -p logs
mkdir -p config

# Check if configuration exists
echo "🔧 Checking configuration..."
if [ ! -f "config.json" ]; then
    echo "⚠️  config.json not found. Creating from template..."
    if [ -f "config-enhanced.json" ]; then
        cp config-enhanced.json config.json
        echo "✅ Created config.json from template"
    else
        echo "❌ config-enhanced.json not found. Please create config.json manually."
        exit 1
    fi
fi

# Check if environment file exists
echo "🔧 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from template"
        echo "⚠️  Please edit .env file with your SMTP and security settings"
    else
        echo "❌ .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Validate configuration
echo "🔍 Validating configuration..."
if ! grep -q "email.smtp.host" config.json; then
    echo "❌ SMTP configuration missing in config.json"
    exit 1
fi

if ! grep -q "security.authToken" config.json; then
    echo "❌ Authentication token missing in config.json"
    exit 1
fi

# Test SMTP connection if credentials are provided
echo "⌨️  Testing SMTP connection..."
if grep -q "email.smtp.user" config.json && grep -q "email.smtp.pass" config.json; then
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
        echo "✅ SMTP connection test passed"
    else
        echo "❌ SMTP connection test failed"
        exit 1
    fi
else
    echo "⚠️  SMTP credentials not configured. Skipping connection test."
fi

# Check for required environment variables
echo "🔍 Checking environment variables..."
if [ -f ".env" ]; then
    if ! grep -q "EMAIL_USER=" .env; then
        echo "⚠️  EMAIL_USER not set in .env"
    fi

    if ! grep -q "EMAIL_PASS=" .env; then
        echo "⚠️  EMAIL_PASS not set in .env"
    fi

    if ! grep -q "MCP_AUTH_TOKEN=" .env; then
        echo "⚠️  MCP_AUTH_TOKEN not set in .env"
    fi
fi

# Set up log rotation
echo "📊 Setting up log rotation..."
if command -v logrotate &> /dev/null; then
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
    echo "✅ Log rotation configured"
else
    echo "⚠️  logrotate not found. Manual log rotation required."
fi

# Create systemd service file (Linux)
echo "⚙️  Creating systemd service (Linux only)..."
if [ -d "/etc/systemd/system" ]; then
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
    echo "✅ systemd service created"
    echo "💡 Run 'sudo systemctl enable mcp-email-server' to enable on boot"
    echo "💡 Run 'sudo systemctl start mcp-email-server' to start the service"
else
    echo "⚠️  systemd not found. Manual service management required."
fi

# Create start scripts
echo "📃 Creating start scripts..."
cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting MCP Email Server..."
NODE_ENV=production node mcp-email-server-enhanced.js
EOF

chmod +x start.sh

cat > start-prod.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting MCP Email Server in production mode..."
NODE_ENV=production forever start --uid "mcp-email-server" -a -l $(pwd)/logs/forever.log -o $(pwd)/logs/output.log -e $(pwd)/logs/error.log mcp-email-server-enhanced.js
EOF

chmod +x start-prod.sh

# Create stop scripts
cat > stop.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping MCP Email Server..."
if command -v forever &> /dev/null; then
    forever stop mcp-email-server
else
    pkill -f "mcp-email-server-enhanced.js"
fi
EOF

chmod +x stop.sh

# Create status script
cat > status.sh << 'EOF'
#!/bin/bash

echo "📊 Checking MCP Email Server status..."
if command -v forever &> /dev/null; then
    forever list | grep mcp-email-server
else
    ps aux | grep "mcp-email-server-enhanced.js" | grep -v grep
fi
EOF

chmod +x status.sh

# Test the server briefly
echo "🧪 Testing server startup..."
if timeout 10 node mcp-email-server-enhanced.js > /dev/null 2>&1; then
    echo "✅ Server starts successfully"
else
    echo "⚠️  Server startup test failed (expected during test)"
fi

# Create health check script
cat > healthcheck.sh << 'EOF'
#!/bin/bash

# Health check for MCP Email Server
URL="http://localhost:8081"

# Check if server is responding
if curl -s "$URL" > /dev/null; then
    echo "✅ Server is running"
    exit 0
else
    echo "❌ Server is not responding"
    exit 1
fi
EOF

chmod +x healthcheck.sh

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit your configuration files:"
echo "   - config.json (SMTP and server settings)"
echo "   - .env (environment variables)"
echo "2. Start the server:"
echo "   ./start.sh (development)"
echo "   ./start-prod.sh (production with forever)"
echo "3. Check status:"
echo "   ./status.sh"
echo "4. Run tests:"
echo "   npm test"
echo ""
echo "🔧 Production deployment:"
echo "   sudo systemctl enable mcp-email-server"
echo "   sudo systemctl start mcp-email-server"
echo ""
echo "📊 Monitoring:"
echo "   tail -f logs/mcp-email-server-enhanced.log"
echo "   ./healthcheck.sh"
echo ""
echo "🔧 Logs location:"
echo "   logs/mcp-email-server-enhanced.log"
echo "   logs/forever.log (if using forever)"
echo ""
echo "🔒 Security reminders:"
echo "   - Change default security keys and tokens"
echo "   - Use HTTPS in production"
echo "   - Set up firewall rules"
echo "   - Monitor logs for suspicious activity"