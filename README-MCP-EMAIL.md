# MCP Email Server for Silver Tier Functional Assistant

A comprehensive Model Context Protocol (MCP) server implementation for email management with robust security, workflow integration, and enhanced features.

## 🚀 Features

### Core Functionality
- **Email Composition**: Create emails with rich metadata, templates, and attachments
- **Secure Email Sending**: SMTP integration with authentication and encryption
- **Approval Workflow**: File-based approval system integrated with existing workflows
- **Email Templates**: Predefined templates for common use cases
- **Scheduling**: Schedule emails for future delivery
- **History Management**: Track sent emails and manage archives

### Security & Reliability
- **Authentication**: Token-based authentication with IP-based security
- **Rate Limiting**: Configurable rate limits to prevent abuse
- **Input Validation**: Comprehensive validation for email content and recipients
- **Encryption**: AES-256 encryption for sensitive data
- **Retry Logic**: Automatic retry with exponential backoff
- **Error Handling**: Detailed error logging and recovery mechanisms

### Enhanced Features
- **Batch Operations**: Send multiple emails efficiently
- **Recipient Validation**: Real-time email validation and domain filtering
- **Connection Testing**: Verify SMTP connectivity before sending
- **Email Reports**: Generate usage reports and analytics
- **Graceful Shutdown**: Clean shutdown with active request completion

## 📋 Prerequisites

- Node.js 16.0.0 or higher
- npm or yarn package manager
- SMTP email provider (Gmail, Outlook, etc.)
- Access to the Silver Tier Employee Vault directory

## 🛠️ Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd Silver-Tier
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure the server:**
   Copy `config-enhanced.json` to `config.json` and update the settings:
   ```bash
   cp config-enhanced.json config.json
   ```

## 📋 Configuration

### SMTP Settings
Update your email provider settings in `config.json`:

```json
{
  "email": {
    "smtp": {
      "host": "smtp.gmail.com",
      "port": 587,
      "secure": false,
      "user": "your-email@gmail.com",
      "pass": "your-app-password"
    }
  }
}
```

### Security Settings
Configure security parameters:

```json
{
  "security": {
    "maxAttempts": 5,
    "lockoutDuration": 300000,
    "allowedDomains": ["example.com", "company.com"],
    "rateLimit": 10,
    "encryptionKey": "change-this-key-in-production",
    "authToken": "change-this-token-in-production"
  }
}
```

### Environment Variables
Set the following environment variables:

```bash
# SMTP Credentials
export EMAIL_USER="your-email@example.com"
export EMAIL_PASS="your-app-password"

# MCP Authentication
export MCP_AUTH_TOKEN="your-mcp-token"

# Vault Path (optional)
export VAULT_PATH="/path/to/your/vault"
```

## 🎯 Usage

### Starting the Server
```bash
# Using npm
npm start

# Or run directly
node mcp-email-server-enhanced.js

# Development mode with auto-restart
npm run dev
```

The server will start on port 8081 by default.

### Using the Client

The enhanced client provides a simple API for interacting with the server:

```javascript
const { EnhancedMCPClient } = require('./mcp-email-client-enhanced.js');

const client = new EnhancedMCPClient();

// Example: Send an email
const result = await client.composeEmail({
    recipients: 'recipient@example.com',
    subject: 'Test Email',
    body: 'This is a test email',
    priority: 'medium',
    category: 'general'
});

await client.sendEmail({ emailId: result.emailId, approval: true });
```

### Available MCP Methods

#### Email Management
- `compose-email`: Create a new email with metadata
- `send-email`: Send an existing email (with optional approval)
- `resend-email`: Resend an email to new recipients
- `schedule-email`: Schedule email for future delivery
- `cancel-scheduled-email`: Cancel a scheduled email

#### Email Templates
- `get-email-templates`: Retrieve predefined email templates
- `validate-email-recipients`: Validate email addresses and domains

#### Workflow & Status
- `get-approval-status`: Check email approval status
- `list-pending-emails`: List emails awaiting approval
- `get-email-history`: Retrieve sent email history
- `test-email-connection`: Test SMTP connectivity

## 🔧 API Methods

### compose-email
Create a new email with comprehensive metadata.

**Parameters:**
```json
{
  "recipients": "string, required",
  "subject": "string, required",
  "body": "string, required",
  "htmlBody": "string, optional",
  "from": "string, optional",
  "priority": "string, optional (low|medium|high|urgent)",
  "category": "string, optional",
  "attachments": "array, optional",
  "schedule_for": "string, optional (ISO timestamp)"
}
```

**Response:**
```json
{
  "emailId": "string",
  "filePath": "string",
  "status": "string",
  "metadata": "object"
}
```

### send-email
Send an existing email.

**Parameters:**
```json
{
  "emailId": "string, required",
  "approval": "boolean, optional (default: false)"
}
```

**Response:**
```json
{
  "emailId": "string",
  "status": "string",
  "message": "string"
}
```

### get-email-templates
Retrieve predefined email templates.

**Parameters:**
```json
{
  "category": "string, optional (general|business|technical)"
}
```

**Response:**
```json
[
  {
    "name": "string",
    "subject": "string",
    "body": "string"
  }
]
```

### schedule-email
Schedule an email for future delivery.

**Parameters:**
```json
{
  "emailId": "string, required",
  "scheduleFor": "string, required (ISO timestamp)"
}
```

**Response:**
```json
{
  "emailId": "string",
  "scheduleFor": "string",
  "status": "string"
}
```

## 🗂️ File Structure

```
Silver-Tier/
├── mcp-email-server-enhanced.js    # Main server implementation
├── mcp-email-client-enhanced.js    # Enhanced client library
├── config-enhanced.json           # Configuration template
├── README-MCP-EMAIL.md            # This documentation
├── package.json                   # Dependencies and scripts
└── logs/                          # Log files (auto-created)
```

### Email File Format
The server uses a structured file format for email storage:

```markdown
---
{
  "id": "EMAIL_uuid",
  "type": "email",
  "status": "pending|approved|sent|failed",
  "priority": "medium",
  "category": "general",
  "created_at": "2026-02-24T10:00:00.000Z",
  "from": "sender@example.com",
  "recipients": "recipient@example.com",
  "subject": "Email Subject",
  "body": "Email body content",
  "encrypted_fields": ["sensitive_data"]
}
---

# Email Composition

## Email Details

**From:** sender@example.com
**To:** recipient@example.com
**Subject:** Email Subject

## Email Body

Email body content

## Processing Notes

- Email composed at: 2026-02-24T10:00:00.000Z
- Priority: medium
- Category: general
- Status: pending
```

## 🔒 Security Implementation

### Authentication
- Token-based authentication using HMAC-SHA256
- IP-based rate limiting and lockout mechanisms
- Secure token validation with request signing

### Data Protection
- AES-256 encryption for sensitive email content
- Domain-based recipient filtering
- Input validation and sanitization
- Secure logging without sensitive data exposure

### Rate Limiting
- Configurable requests per minute
- Automatic IP lockout after failed attempts
- Graceful degradation with informative errors

## 📊 Monitoring & Logging

### Logging
- Structured JSON logging with timestamps
- Error stack traces for debugging
- Request/response tracking
- Performance metrics collection

### Health Monitoring
- Automatic server health checks
- Performance metrics (active requests, response times)
- Error rate monitoring
- Resource usage tracking

## 🚀 Advanced Usage

### Batch Email Sending
```javascript
const emails = [
  {
    recipients: 'user1@example.com',
    subject: 'Batch Email 1',
    body: 'This is the first batch email'
  },
  {
    recipients: 'user2@example.com',
    subject: 'Batch Email 2',
    body: 'This is the second batch email'
  }
];

const results = await client.batchSendEmails(emails);
```

### Email Reports
```javascript
const startDate = new Date();
startDate.setDate(startDate.getDate() - 30);
const report = await client.generateEmailReport(
    startDate.getTime(),
    Date.now(),
    'sent'
);
```

### Retry Failed Emails
```javascript
const failedEmails = await client.listPendingEmails();
const retryResults = await client.retryFailedEmails(failedEmails, 3);
```

## 🚨 Error Handling

The server implements comprehensive error handling:

### Common Errors
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `AUTHENTICATION_FAILED`: Invalid authentication token
- `EMAIL_NOT_FOUND`: Email ID doesn't exist
- `INVALID_EMAIL_FORMAT`: Malformed email address
- `SMTP_CONNECTION_ERROR`: Email server connection issues
- `VALIDATION_FAILED`: Email content validation errors

### Error Recovery
- Automatic retry with exponential backoff
- Detailed error logging for debugging
- Graceful degradation for non-critical failures
- Email status updates for failed deliveries

## 🔄 Development

### Testing
```bash
# Run the test suite
npm test

# Run in development mode
npm run dev
```

### Debugging
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
npm start
```

### Environment Setup
```bash
# Copy and configure
cp config-enhanced.json config.json
cp .env.example .env

# Edit configuration files
nano config.json
nano .env
```

## 🐛 Troubleshooting

### Common Issues

#### SMTP Connection Failed
```bash
# Check SMTP settings in config.json
# Verify email credentials are correct
# Ensure app-specific passwords are used for Gmail
# Check firewall settings
```

#### Authentication Failed
```bash
# Verify MCP_AUTH_TOKEN environment variable
# Check client and server token consistency
# Ensure IP address is not locked out
```

#### Rate Limiting
```bash
# Reduce request frequency
# Check if IP is locked out (wait for lockoutDuration)
# Review security configuration
```

#### Email Not Sending
```bash
# Check email approval status
# Verify SMTP server connectivity
# Review email content validation errors
# Check file permissions in vault directory
```

### Logs
Check the server logs for detailed information:
```bash
tail -f mcp-email-server-enhanced.log
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 🆘 Support

For support and questions:
- Check the documentation in this README
- Review the server logs for error details
- Verify configuration settings
- Ensure all environment variables are set correctly

## 🚨 Production Deployment

### Security Considerations
- Change default encryption keys and auth tokens
- Use HTTPS for client-server communication
- Implement proper access controls
- Regular security audits and updates
- Monitor for unusual activity patterns

### Performance Optimization
- Adjust rate limiting for your use case
- Monitor server resource usage
- Implement connection pooling for SMTP
- Consider load balancing for high traffic
- Regular performance testing

### Backup & Recovery
- Regular backup of email files and configuration
- Test recovery procedures periodically
- Monitor disk space usage
- Implement log rotation and archival

---

**Note**: This is a production-ready MCP server implementation with comprehensive features, security, and reliability. Always test thoroughly before deploying to production environments.