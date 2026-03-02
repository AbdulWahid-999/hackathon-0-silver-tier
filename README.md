# LinkedIn Watcher for Silver Tier Functional Assistant

A comprehensive Python script that monitors LinkedIn for business opportunities, messages, and connection requests. Automatically posts business content about products/services to generate sales.

## Features

- **Authentication**: Secure login to LinkedIn
- **Message Monitoring**: Automatically detects and responds to new messages
- **Connection Request Handling**: Auto-accepts relevant connection requests
- **Content Generation**: Creates engaging business posts
- **Post Scheduling**: Automated posting at optimal times
- **Action Files**: Generates action files in Needs_Action folder
- **Error Handling**: Robust retry logic and error management
- **Logging**: Comprehensive logging for monitoring and debugging

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (optional):
   ```bash
   export LINKEDIN_EMAIL="your-email@example.com"
   export LINKEDIN_PASSWORD="your-password"
   export COMPANY_NAME="Your Company"
   ```

3. **Configure the application**:
   Edit `config.json` with your business details and preferences.

## Configuration

The `config.json` file contains all configurable settings:

```json
{
  "linkedin": {
    "email": "your-email@example.com",
    "password": "your-password",
    "profile_url": "https://www.linkedin.com",
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5
  },
  "business": {
    "company_name": "Your Company",
    "products_services": ["AI Solutions", "Business Automation", "Data Analytics"],
    "target_industries": ["Technology", "Finance", "Healthcare"],
    "target_locations": ["Global"]
  },
  "automation": {
    "auto_accept_connections": true,
    "auto_respond_to_messages": true,
    "auto_post_content": true,
    "post_frequency_hours": 8,
    "max_posts_per_day": 3,
    "content_types": ["text", "article", "post"]
  }
}
```

## Usage

### Basic Usage
```bash
python linkedin_watcher.py
```

### With Environment Variables
```bash
LINKEDIN_EMAIL="your-email@example.com" LINKEDIN_PASSWORD="your-password" python linkedin_watcher.py
```

### Background Execution
```bash
nohup python linkedin_watcher.py > linkedin_watcher.log 2>&1 &
```

## Generated Files

### Action Files (Needs_Action folder)
Generated files for tracking actions:
- `action_message_response_YYYYMMDD_HHMMSS.json`
- `action_connection_request_YYYYMMDD_HHMMSS.json`
- `action_scheduled_post_YYYYMMDD_HHMMSS.json`

### Content Files (Content folder)
Generated content drafts:
- `content_post_YYYYMMDD_HHMMSS.json`

### Logs (Logs folder)
Comprehensive logging:
- `linkedin_watcher.log`

## Post Templates

The system uses customizable templates for generating content:

### Post Templates
```
Check out our latest {product}! {description}
Exciting news! We're launching {product}. {details}
{product} is now available! Transform your {industry} business with {benefit}
Don't miss out on {product}! Limited time offer: {deal}
```

### Response Templates
```
Connection Request: "Thanks for connecting! I'm excited to explore how we can work together."
Sales Inquiry: "Thank you for your interest in {product}! I'd love to discuss how we can help your business."
Partnership: "Great to hear from you! Let's explore collaboration opportunities between our companies."
```

## Automation Features

### Connection Request Handling
- Auto-accepts connection requests
- Creates action files for each request
- Logs all connection activities

### Message Response Automation
- Auto-responds to incoming messages
- Generates appropriate responses based on message content
- Creates action files for all responses

### Content Posting
- Generates engaging business content
- Posts at scheduled intervals
- Creates action files for all posts
- Uses templates for consistency

## Error Handling

The system includes robust error handling:

- **Retry Logic**: Automatically retries failed operations
- **Timeouts**: Configurable timeout settings
- **Exception Handling**: Catches and logs all exceptions
- **Fallback Mechanisms**: Alternative approaches for failed operations

## Monitoring

### Logs
All activities are logged in `linkedin_watcher.log` with timestamps and severity levels.

### Status Monitoring
The system provides real-time status updates through logging and can be monitored using:
```bash
tail -f linkedin_watcher.log
```

## Security Considerations

- **Credentials**: Store credentials securely using environment variables
- **Data Privacy**: All data is stored locally, no external data transmission
- **Rate Limiting**: Built-in rate limiting to avoid LinkedIn restrictions

## Maintenance

### Regular Tasks
- Monitor logs for errors
- Review action files in Needs_Action folder
- Update business information as needed
- Check for software updates

### Troubleshooting
Common issues and solutions:

1. **Authentication Failed**: Check credentials and LinkedIn security settings
2. **Element Not Found**: Update CSS selectors for LinkedIn UI changes
3. **Rate Limited**: Reduce automation frequency

## Development

### Extending Functionality
To add new features:

1. Add new methods to `LinkedInWatcher` class
2. Update configuration structure if needed
3. Add corresponding templates or responses
4. Update documentation

### Testing
Run tests using:
```bash
python -m pytest
```

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the logs in `linkedin_watcher.log`
2. Review action files in `Needs_Action` folder
3. Verify LinkedIn account status and security settings
4. Ensure all dependencies are installed correctly"# hackathon-0-silver-tier" 
