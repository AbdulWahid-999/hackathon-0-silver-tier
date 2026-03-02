# Gmail Watcher for Silver Tier Functional Assistant
# Monitors Gmail for unread/important emails and creates action files

import time
import logging
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailWatcher:
    def __init__(self, vault_path: str, credentials_file: str = 'gmail_credentials.json',
                 token_file: str = 'token.json', check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file)
        self.check_interval = check_interval
        self.logger = logging.getLogger('GmailWatcher')
        self.service = None
        self.last_check_time = datetime.utcnow() - timedelta(hours=1)

        # Create directories if they don't exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.done.mkdir(parents=True, exist_ok=True)

        # Initialize Gmail service
        self.initialize_service()

    def initialize_service(self):
        """Initialize Gmail API service with OAuth2 authentication"""
        try:
            creds = None

            # Check if token file exists
            if self.token_file.exists():
                self.logger.info('Loading existing credentials')
                creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)

                # Refresh token if expired
                if creds.expired and creds.refresh_token:
                    self.logger.info('Refreshing credentials')
                    creds.refresh(Request())
                elif creds.expired:
                    self.logger.info('Credentials expired, starting new authentication')
                    creds = None

            # If no valid credentials, start authentication flow
            if not creds or not creds.valid:
                self.logger.info('Starting OAuth2 authentication flow')
                if self.credentials_file.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), SCOPES)
                    creds = flow.run_local_server(port=0)

                    # Save credentials for next time
                    with open(self.token_file, 'w') as token:
                        token.write(creds.to_json())
                else:
                    self.logger.error('Credentials file not found. Please download from Google Cloud Console.')
                    raise FileNotFoundError('gmail_credentials.json not found')

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info('Gmail API service initialized successfully')

        except Exception as e:
            self.logger.error(f'Failed to initialize Gmail service: {e}')
            raise

    def check_emails(self) -> List[Dict]:
        """Check for new emails since last check"""
        try:
            self.logger.info('Checking for new emails')

            # Get current time
            current_time = datetime.utcnow()

            # Prepare Gmail API query
            query = f'newer_than:1d is:unread OR is:important'

            # Call Gmail API
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                self.logger.info('No new emails found')
                return []

            self.logger.info(f'Found {len(messages)} new emails')

            # Fetch email details
            email_data = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    email_info = self.parse_email(message)
                    email_data.append(email_info)

                except HttpError as e:
                    self.logger.error(f'Failed to fetch email {msg[\"id\"]}: {e}')
                    continue

            # Update last check time
            self.last_check_time = current_time

            return email_data

        except Exception as e:
            self.logger.error(f'Error checking emails: {e}')
            return []

    def parse_email(self, message: Dict) -> Dict:
        """Parse email message and extract relevant information"""
        try:
            # Extract headers
            headers = {header['name'].lower(): header['value']
                      for header in message.get('payload', {}).get('headers', [])}

            # Extract email parts
            payload = message.get('payload', {})
            body = ''

            # Check for text/plain part
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        body = self.decode_part(part)
                        break
            elif 'body' in payload:
                body = self.decode_part(payload)

            # Extract metadata
            email_info = {
                'id': message.get('id'),
                'from': headers.get('from', 'Unknown'),
                'to': headers.get('to', 'Unknown'),
                'subject': headers.get('subject', 'No Subject'),
                'date': headers.get('date', 'Unknown'),
                'snippet': message.get('snippet', ''),
                'body': body[:500] if body else '',  # Limit to first 500 chars
                'priority': self.determine_priority(headers),
                'status': 'pending',
                'created': datetime.utcnow().isoformat() + 'Z'
            }

            return email_info

        except Exception as e:
            self.logger.error(f'Error parsing email: {e}')
            return {
                'id': message.get('id'),
                'subject': 'Error parsing email',
                'priority': 'medium',
                'status': 'pending',
                'created': datetime.utcnow().isoformat() + 'Z'
            }

    def decode_part(self, part: Dict) -> str:
        """Decode email part content"""
        try:
            data = part.get('body', {}).get('data', '')
            if data:
                import base64
                import email
                decoded = base64.urlsafe_b64decode(data.encode('utf-8')).decode('utf-8', errors='ignore')
                return decoded
        except Exception as e:
            self.logger.error(f'Error decoding email part: {e}')
        return ''

    def determine_priority(self, headers: Dict) -> str:
        """Determine email priority based on headers and content"""
        # Check for priority headers
        priority = headers.get('x-priority', '')
        importance = headers.get('importance', '').lower()

        if 'high' in priority.lower() or 'high' in importance:
            return 'high'
        elif 'urgent' in headers.get('subject', '').lower():
            return 'high'
        elif 'low' in priority.lower() or 'low' in importance:
            return 'low'
        else:
            return 'medium'

    def create_action_file(self, email_info: Dict):
        """Create action file for email in Needs_Action folder"""
        try:
            # Create filename
            subject_safe = email_info['subject'].replace(' ', '_').replace('/', '_').replace(':', '_')
            if len(subject_safe) > 50:
                subject_safe = subject_safe[:47] + '...' + str(hash(email_info['id']))[:3]

            action_file = self.needs_action / f'EMAIL_{subject_safe}.md'

            # Create markdown content
            content = f"""---
{{
  "type": "email",
  "id": "{email_info['id']}",
  "from": "{email_info['from']}",
  "to": "{email_info['to']}",
  "subject": "{email_info['subject']}",
  "priority": "{email_info['priority']}",
  "status": "{email_info['status']}",
  "created": "{email_info['created']}"
}}
---

# New Email Received

## Email Information
- **From**: {email_info['from']}
- **To**: {email_info['to']}
- **Subject**: {email_info['subject']}
- **Received**: {email_info['date']}
- **Priority**: {email_info['priority'].capitalize()}

## Email Preview
{email_info['snippet']}

## Suggested Actions
- [ ] Read full email content
- [ ] Respond to sender if necessary
- [ ] Categorize email type (client, internal, etc.)
- [ ] Create follow-up task if needed
- [ ] Archive or move to appropriate folder
- [ ] Update Dashboard with email status

## Processing Notes
- Email ID: {email_info['id']}
- Processing priority: {email_info['priority']}
- File created at: {datetime.utcnow().isoformat() + 'Z'}
"""

            # Write file
            action_file.write_text(content, encoding='utf-8')
            self.logger.info(f'Created action file: {action_file.name}')

        except Exception as e:
            self.logger.error(f'Error creating action file: {e}')

    def run(self, iterations: Optional[int] = None):
        """Run the Gmail watcher continuously"""
        try:
            count = 0
            while True:
                # Check for new emails
                emails = self.check_emails()

                # Create action files for new emails
                for email in emails:
                    self.create_action_file(email)

                # Wait for next check
                self.logger.info(f'Sleeping for {self.check_interval} seconds')
                time.sleep(self.check_interval)

                count += 1
                if iterations and count >= iterations:
                    break

        except KeyboardInterrupt:
            self.logger.info('Gmail Watcher stopped by user')
        except Exception as e:
            self.logger.error(f'Error in Gmail Watcher: {e}')
            raise

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('gmail_watcher.log'),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    # Setup logging
    setup_logging()

    # Initialize and run Gmail Watcher
    # Use raw string for Windows path
    vault_path = r"C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault"

    watcher = GmailWatcher(vault_path)
    watcher.run()