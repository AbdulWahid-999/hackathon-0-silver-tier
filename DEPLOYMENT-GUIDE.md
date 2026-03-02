# MCP Email Server - Deployment and Operations Guide

## 🚀 Quick Start

### 1. Clone and Navigate
```bash
cd Silver-Tier
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Configure the Server
```bash
# Copy configuration templates
cp config-enhanced.json config.json
cp .env.example .env

# Edit configuration files
nano config.json
nano .env
```

### 4. Deploy the Server
```bash
./deploy.sh
```

### 5. Start the Server
```bash
# Development mode
./start.sh

# Production mode
./start-prod.sh

# Or using systemd (Linux)
sudo systemctl start mcp-email-server
```

## 📋 Configuration

### SMTP Settings
Edit `config.json`:
```json
{
  "email": {
    "smtp": {
      "host": "smtp.gmail.com",
      "port": 587,
      "secure": false,
      "user": "your-email@example.com",
      "pass": "your-app-password"
    }
  }
}
```

### Environment Variables
Edit `.env`:
```env
EMAIL_USER=your-email@example.com
EMAIL_PASS=your-app-password
MCP_AUTH_TOKEN=your-secure-token
SECURITY_KEY=your-encryption-key
```

## 🛠️ Management Commands

### Start/Stop
```bash
# Start
./start.sh          # Development
./start-prod.sh     # Production

# Stop
./stop.sh

# Status
./status.sh
```

### Updates
```bash
# Update the server
./update.sh

# Full maintenance
./maintenance.sh
```

### Health Check
```bash
# Check server health
./healthcheck.sh

# Check logs
tail -f logs/mcp-email-server-enhanced.log
```

## 📋 Systemd Integration (Linux)

### Enable on Boot
```bash
sudo systemctl enable mcp-email-server
```

### Start/Stop Service
```bash
sudo systemctl start mcp-email-server
sudo systemctl stop mcp-email-server
sudo systemctl restart mcp-email-server
```

### Service Status
```bash
sudo systemctl status mcp-email-server
```

## 🔧 API Methods

### Email Management
```javascript
// Compose an email
const email = await client.composeEmail({
    recipients: 'user@example.com',
    subject: 'Test Email',
    body: 'This is a test email',
    priority: 'high',
    category: 'general'
});

// Send email (with approval)
await client.sendEmail({ emailId: email.emailId, approval: true });

// Schedule email
await client.scheduleEmail({
    emailId: email.emailId,
    scheduleFor: new Date(Date.now() + 3600000).toISOString() // 1 hour from now
});

// Get email templates
const templates = await client.getEmailTemplates({ category: 'general' });
```

### Security Operations
```javascript
// Validate recipients
const validation = await client.validateRecipients({
    recipients: 'user@example.com,invalid-email,blocked@company.com'
});

// Test SMTP connection
const connection = await client.testConnection();

// Get server status
const status = await client.getServerStatus();
```

## 📊 Monitoring

### Log Files
- `logs/mcp-email-server-enhanced.log` - Main server logs
- `logs/forever.log` - Process manager logs (production)
- `logs/output.log` - Standard output logs
- `logs/error.log` - Error logs

### Metrics
```bash
# Check server performance
./maintenance.sh

# Monitor resource usage
watch -n 5 "./maintenance.sh"
```

## 🔒 Security Best Practices

### Environment Variables
```bash
# Set secure permissions
chmod 600 .env

# Use strong tokens
export MCP_AUTH_TOKEN=$(openssl rand -hex 32)
```

### Firewall Rules
```bash
# Allow MCP port (8081 by default)
sudo ufw allow 8081/tcp

# Restrict access if needed
sudo ufw allow from 192.168.1.0/24 to any port 8081
```

### Regular Maintenance
```bash
# Weekly maintenance
./maintenance.sh

# Monthly security review
./update.sh
```

## 🚨 Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Check logs
tail -f logs/mcp-email-server-enhanced.log

# Check configuration
cat config.json

# Test SMTP connection
node -e "
const nodemailer = require('nodemailer');
const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
    }
});

transporter.verify((error, success) => {
    if (error) {
        console.error('SMTP connection failed:', error.message);
    } else {
        console.log('SMTP connection successful');
    }
});
"
```

#### Email Not Sending
```bash
# Check email approval status
const status = await client.getApprovalStatus({ emailId: 'EMAIL_123' });
console.log(status);

# Check SMTP logs
grep 'smtp' logs/mcp-email-server-enhanced.log
```

#### Rate Limiting
```bash
# Check rate limit status
./maintenance.sh

# Wait for lockout duration (5 minutes by default)
sleep 300
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./start.sh

# Check verbose output
tail -f logs/mcp-email-server-enhanced.log | grep -i debug
```

## 🔄 Backup and Recovery

### Backup Configuration
```bash
# Manual backup
./maintenance.sh

# Automatic backup (add to crontab)
0 2 * * * /path/to/mcp-email-server/maintenance.sh
```

### Restore from Backup
```bash
# Restore configuration
cp backup_20240224_120000/config.json config.json
cp backup_20240224_120000/.env .env

# Restart server
./restart.sh
```

## 📈 Performance Tuning

### Configuration Optimization
```json
{
  "monitoring": {
    "maxConcurrentEmails": 10,
    "emailQueueSize": 500,
    "healthCheckInterval": 30000
  }
}
```

### Resource Limits
```bash
# Set file descriptor limits
ulimit -n 10000

# Monitor memory usage
watch -n 5 'ps aux | grep mcp-email-server'
```

## 📦 Production Deployment

### Pre-Deployment Checklist
- [ ] SMTP configuration tested
- [ ] Security tokens set
- [ ] Firewall rules configured
- [ ] Log rotation set up
- [ ] Backup procedures tested
- [ ] Monitoring configured

### Deployment Steps
1. Run `./deploy.sh`
2. Configure production settings
3. Test with `./healthcheck.sh`
4. Start with `./start-prod.sh`
5. Monitor with `./status.sh`

### Post-Deployment
```bash
# Monitor logs
tail -f logs/mcp-email-server-enhanced.log

# Check server health
./healthcheck.sh

# Set up monitoring alerts
```

## 📚 Additional Resources

### Documentation
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Node.js SMTP Guide](https://nodemailer.com)
- [Winston Logging](https://github.com/winstonjs/winston)

### Support
- Check server logs for error details
- Review configuration files
- Test with sample emails
- Monitor system resources

## 🎉 Congratulations!

Your MCP Email Server is now deployed and ready for use! Remember to:

1. **Monitor regularly** - Check logs and performance
2. **Update periodically** - Run `./update.sh` for security patches
3. **Backup consistently** - Use `./maintenance.sh` for automated backups
4. **Test thoroughly** - Verify email functionality regularly

The server provides a robust, secure, and scalable solution for email management with the Silver Tier Functional Assistant.