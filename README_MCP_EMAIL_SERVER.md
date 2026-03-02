# MCP Email Server

This MCP (Model Context Protocol) server provides email functionality for the Silver Tier Functional Assistant with integration to the existing file-based approval workflow.

## Features

- **Email Composition**: Create and save emails in the approval workflow
- **Email Sending**: Send emails with proper authentication and error handling
- **Approval Workflow Integration**: Emails are saved to `Needs_Action` folder for approval
- **Template System**: Pre-defined email templates for common scenarios
- **Status Tracking**: Monitor email status (pending, approved, sent, failed)
- **Resend Capability**: Easily resend emails to new recipients
- **Logging**: Comprehensive logging with Winston
- **Configuration**: Flexible SMTP and server configuration

## Quick Start

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Configure Email**
   Update `config.json` with your SMTP settings or set environment variables:
   ```bash
   export EMAIL_USER="your-email@gmail.com"
   export EMAIL_PASS="your-app-password"
   ```

3. **Start the Server**
   ```bash
   npm start
   ```

4. **Use MCP Tools**
   The server listens on port 8080 for MCP requests.

## MCP Tools

### 1. compose-email
Compose a new email that will be saved to the approval workflow.

**Parameters:**
- `recipients` (string, required): Email address(es) to send to
- `subject` (string, required): Email subject
- `body` (string, required): Email body text
- `htmlBody` (string, optional): HTML version of the email
- `from` (string, optional): Sender email address
- `priority` (string, optional): Priority level (low, medium, high)
- `category` (string, optional): Email category
- `attachments` (array, optional): File paths to attach

**Returns:**
- `emailId`: Unique identifier for the email
- `filePath`: Path to the created email file
- `status`: Current status (pending)

### 2. send-email
Send an email by ID. If approval is not provided, the email will be automatically approved.

**Parameters:**
- `emailId` (string, required): ID of the email to send
- `approval` (boolean, optional): Require manual approval

**Returns:**
- `emailId`: ID of the sent email
- `status`: Current status (sent)

### 3. get-email-templates
Get pre-defined email templates.

**Parameters:**
- `category` (string, optional): Template category (general, business)

**Returns:**
- Array of template objects with name, subject, and body

### 4. get-approval-status
Check the approval status of an email.

**Parameters:**
- `emailId` (string, required): ID of the email to check

**Returns:**
- `emailId`: ID of the email
- `status`: Current status (pending, approved, sent, failed)
- `filePath`: Path to the email file
- `metadata`: Full email metadata

### 5. list-pending-emails
List all emails pending approval.

**Returns:**
- Array of pending email objects with metadata

### 6. resend-email
Resend an existing email to new recipients.

**Parameters:**
- `emailId` (string, required): ID of the original email
- `newRecipients` (string, optional): New recipient(s)

**Returns:**
- `originalEmailId`: ID of the original email
- `newEmailId`: ID of the new email
- `newFilePath`: Path to the new email file
- `status`: Current status (pending)

## File Structure

When an email is composed, it's saved as a markdown file in the `Needs_Action` folder:

```
Needs_Action/
├── EMAIL_{uuid}.md
```

Each file contains YAML front matter with metadata:

```yaml
---
{
  "id": "EMAIL_123456",
  "type": "email",
  "status": "pending",
  "priority": "medium",
  "category": "general",
  "created_at": "2026-02-24T10:00:00.000Z",
  "from": "sender@example.com",
  "recipients": "recipient@example.com",
  "subject": "Welcome",
  "body": "Dear user...",
  "attachments": []
}
---

# Email Composition

## Email Details

**From:** sender@example.com
**To:** recipient@example.com
**Subject:** Welcome

## Email Body

Dear user...
```

## Configuration

### SMTP Settings
Configure in `config.json`:
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

### Environment Variables
```bash
# SMTP credentials
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Server configuration
MCP_PORT=8080
VAULT_PATH=/path/to/your/vault
```

## Error Handling

The server implements comprehensive error handling:

- **Email Transport Errors**: Logs and marks emails as failed
- **File System Errors**: Handles directory creation and file operations
- **Invalid Requests**: Returns meaningful error messages
- **Network Issues**: Retries and logs connection problems

## Logging

Logs are written to `mcp-email-server.log` and include:
- Email composition events
- Sending attempts and results
- File system operations
- Error conditions
- Server startup/shutdown

## Security Considerations

- Use app-specific passwords for SMTP authentication
- Store credentials securely using environment variables
- Validate email addresses before sending
- Implement rate limiting for email sending
- Monitor for unusual email patterns

## Integration

The MCP Email Server integrates with the existing Silver Tier workflow:

1. **File Monitoring**: Watches the `Needs_Action` folder for new/updated emails
2. **Approval Workflow**: Emails start as "pending" and move to "approved" when processed
3. **Status Tracking**: Updates email status based on sending results
4. **Directory Structure**: Uses existing `Needs_Action` and `Done` folders

## Testing

To test the server:

1. **Start the server**: `npm start`
2. **Send a test request**:
   ```bash
   curl -X POST http://localhost:8080 \
     -H "Content-Type: application/json" \
     -d '{
       "method": "compose-email",
       "params": {
         "recipients": "test@example.com",
         "subject": "Test Email",
         "body": "This is a test email."
       }
     }'
   ```

## Troubleshooting

### Common Issues

1. **Email not sending**: Check SMTP credentials and network connectivity
2. **File permissions**: Ensure the server has write access to the vault directories
3. **Port conflicts**: Change MCP_PORT if port 8080 is in use
4. **Missing dependencies**: Run `npm install` to install required packages

### Logs

Check `mcp-email-server.log` for detailed error information and debugging.

## Development

### Adding New Features

1. Add new MCP tool handler in `MCPServer` class
2. Update `initializeHandlers()` method
3. Add tool documentation to this README
4. Test with curl or MCP client

### Testing

Use the provided test scripts or create new ones in the `test` directory.

## License

MIT License - see LICENSE file for details.