# Gmail Watcher for Silver Tier Functional Assistant

This module monitors Gmail for unread/important emails and creates action files in the Needs_Action folder following the existing format.

## Features

- **OAuth2 Authentication**: Secure Google API authentication with token refresh
- **Email Monitoring**: Checks for unread and important emails every 60 seconds
- **Priority Detection**: Automatically determines email priority (low/medium/high)
- **Metadata Extraction**: Extracts sender, subject, date, and email content
- **Action File Creation**: Creates markdown files in Needs_Action folder following the established format
- **Error Handling**: Comprehensive error handling with retry logic
- **Logging**: Detailed logging for monitoring and debugging

## Setup Instructions

### 1. Enable Gmail API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Select "Desktop application"
   - Download the JSON file and save it as `gmail_credentials.json`

### 2. Install Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 3. Configure Vault Path

Edit the `gmail_watcher.py` file and set the correct `vault_path`:

```python
vault_path = "C:\\Users\\goku\\MyWebsiteProjects\\hackathon-0\\Silver-Tier\\AI_Silver_Employee_Vault"
```

### 4. Run the Watcher

```bash
python gmail_watcher.py
```

The first time you run it, you'll be prompted to authenticate with Google. Follow the instructions in your browser.

## File Format

The watcher creates files in the `Needs_Action` folder with this format:

```markdown
---
{
  "type": "email",
  "id": "<email_id>",
  "from": "sender@example.com",
  "to": "recipient@example.com",
  "subject": "Email Subject",
  "priority": "medium",
  "status": "pending",
  "created": "2026-02-23T12:34:56Z"
}
---

# New Email Received

## Email Information
- **From**: sender@example.com
- **To**: recipient@example.com
- **Subject**: Email Subject
- **Received**: Wed, 23 Feb 2026 12:34:56 -0500
- **Priority**: Medium

## Email Preview
This is a preview of the email content...

## Suggested Actions
- [ ] Read full email content
- [ ] Respond to sender if necessary
- [ ] Categorize email type (client, internal, etc.)
- [ ] Create follow-up task if needed
- [ ] Archive or move to appropriate folder
- [ ] Update Dashboard with email status

## Processing Notes
- Email ID: <email_id>
- Processing priority: medium
- File created at: 2026-02-23T12:35:00Z
```

## Integration with Existing Architecture

The Gmail Watcher integrates seamlessly with the existing file system watcher:

1. **Uses Same Folder Structure**: Creates files in the existing `Needs_Action` folder
2. **Follows Same Format**: Uses the same metadata structure and markdown format
3. **Compatible with AI Employee**: Files are processed by the same AI Employee logic
4. **Shared Logging**: Uses the same logging configuration
5. **Token Persistence**: Stores OAuth tokens for future use

## Configuration Options

You can customize the watcher behavior by modifying the `GmailWatcher` class initialization:

```python
# Default configuration
watcher = GmailWatcher(
    vault_path="path/to/vault",
    credentials_file="gmail_credentials.json",
    token_file="token.json",
    check_interval=60  # seconds
)
```

## Error Handling

The watcher includes comprehensive error handling:

- **Authentication Errors**: Handles expired tokens and refreshes them automatically
- **API Errors**: Catches and logs Gmail API errors
- **File System Errors**: Handles file creation errors gracefully
- **Network Errors**: Retries on network failures
- **Email Parsing Errors**: Handles malformed emails without crashing

## Monitoring

Logs are written to `gmail_watcher.log` and the console. You can monitor the watcher's activity by checking the log file.

## Security Considerations

- OAuth tokens are stored locally in `token.json`
- Credentials are never stored in plain text
- Uses Google's secure OAuth2 flow
- Only read access to Gmail is requested
- Logs don't contain sensitive email content

## Troubleshooting

### "gmail_credentials.json not found"
- Make sure you've downloaded the credentials from Google Cloud Console
- Ensure the file is in the same directory as the script

### Authentication fails
- Make sure you're using the correct Google account
- Check that the Gmail API is enabled for your project
- Ensure your browser allows pop-ups for the authentication flow

### No emails are detected
- Check that the query string is correct: `newer_than:1d is:unread OR is:important`
- Verify your Gmail account has unread/important emails
- Check the log file for any errors

### Files aren't being created
- Check that the `Needs_Action` folder exists and is writable
- Verify the vault path is correct
- Check the log file for any file system errors

## Future Enhancements

- Support for additional email providers (Outlook, Yahoo, etc.)
- Advanced filtering and categorization
- Integration with calendar events
- Sentiment analysis of email content
- Automated response templates