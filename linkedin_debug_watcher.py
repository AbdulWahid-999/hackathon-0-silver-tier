# LinkedIn Watcher - DEBUG VERSION
# This will help us identify the correct selectors

import time
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger('LinkedInWatcher')

class LinkedInWatcher:
    def __init__(self, vault_path: str = None, session_path: str = None):
        self.vault_path = Path(vault_path) if vault_path else Path(__file__).parent / 'AI_Silver_Employee_Vault'
        self.session_path = Path(session_path) if session_path else self.vault_path / 'linkedin_session'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logs_dir = self.vault_path / 'Logs'
        self.screenshots_dir = self.vault_path / 'Screenshots'
        
        for directory in [self.needs_action, self.logs_dir, self.screenshots_dir, self.session_path]:
            directory.mkdir(parents=True, exist_ok=True)
        
        load_dotenv()
        self.tracking_file = self.logs_dir / 'linkedin_debug_tracking.json'
        self.processed_messages = set()
        
        self.browser = None
        self.context = None
        self.page = None
        
        logger.info('=' * 80)
        logger.info('LINKEDIN WATCHER - DEBUG MODE')
        logger.info('=' * 80)

    def is_logged_in(self) -> bool:
        if not self.page:
            return False
        try:
            if 'linkedin.com' in self.page.url and 'login' not in self.page.url:
                return True
            return False
        except:
            return False

    def initialize_browser(self):
        """Initialize and wait for login"""
        try:
            logger.info('Starting browser...')
            playwright = sync_playwright().start()
            
            self.context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            self.browser = self.context
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            
            logger.info('Going to LinkedIn messaging...')
            self.page.goto('https://www.linkedin.com/messaging/', wait_until='domcontentloaded', timeout=90000)
            time.sleep(10)  # Wait for page to fully load
            
            # Take screenshot
            screenshot_path = self.screenshots_dir / f'messaging_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f'Screenshot saved: {screenshot_path}')
            
            return True
        except Exception as e:
            logger.error(f'Error: {e}')
            return False

    def debug_page_content(self):
        """Debug: Print everything we can find on the page"""
        try:
            logger.info('')
            logger.info('=' * 80)
            logger.info('DEBUGGING PAGE CONTENT')
            logger.info('=' * 80)
            
            # Get page URL
            logger.info(f'Current URL: {self.page.url}')
            
            # Get page title
            title = self.page.title()
            logger.info(f'Page Title: {title}')
            
            # Get all list items (common message container)
            all_selectors = [
                '[class*="msg"]',
                '[class*="message"]',
                '[class*="thread"]',
                '[class*="conversation"]',
                '[role="listitem"]',
                'li',
                '[class*="list-item"]'
            ]
            
            for selector in all_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        logger.info(f'✓ Found {len(elements)} elements for: {selector[:50]}')
                        
                        # Print first 3 elements content
                        for idx, elem in enumerate(elements[:3]):
                            try:
                                text = elem.inner_text()[:100]
                                classes = elem.get_attribute('class')[:100] if elem.get_attribute('class') else 'no-class'
                                logger.info(f'  [{idx}] Text: {text}')
                                logger.info(f'      Classes: {classes}')
                            except:
                                pass
                except Exception as e:
                    logger.debug(f'Selector failed {selector}: {e}')
            
            # Get page HTML (first 2000 chars)
            try:
                content = self.page.content()
                logger.info(f'Page HTML length: {len(content)} chars')
                logger.info(f'First 500 chars: {content[:500]}')
            except:
                pass
            
            # Save full HTML
            html_path = self.logs_dir / f'page_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.page.content())
            logger.info(f'Full HTML saved to: {html_path}')
            
            logger.info('=' * 80)
            
        except Exception as e:
            logger.error(f'Debug error: {e}')

    def check_messages_manual(self) -> List[Dict]:
        """Manually check for messages with every possible selector"""
        try:
            logger.info('')
            logger.info('📧 Checking messages with ALL possible selectors...')
            
            messages = []
            
            # EVERY possible selector for message threads
            selectors = [
                '[class*="msg-thread-list-item"]',
                '.msg-thread-list-item',
                '[data-testid="msg-thread-list-item"]',
                'li[class*="msg"]',
                '.msg-conversations-container [role="listitem"]',
                '[role="listitem"]',
                '.msg-thread-list__item',
                '.msg-thread-list-item',
                '[class*="msg-sender"]',
                '[class*="message-item"]',
                '.msg-thread',
                '[class*="conversation-item"]',
                '.artdeco-list__item',
                '[class*="feed-shared-update"]',
                'div[role="listitem"]',
                'li.artdeco-list__item',
                '.msg-thread-list li',
                '[class*="MjVList"]',  # LinkedIn's internal class
                '[class*="msg-conversations"]',
                '*']  # Wildcard - get everything
            
            for selector in selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        logger.info(f'✓ {len(elements)} elements found: {selector}')
                        
                        for idx, elem in enumerate(elements[:5]):
                            try:
                                text = elem.inner_text()[:150]
                                if text.strip():  # Only if has text
                                    logger.info(f'  [{idx}] {text}')
                                    
                                    # Try to extract sender
                                    sender = 'Unknown'
                                    preview = ''
                                    
                                    # Try multiple ways to get sender
                                    name_elems = elem.query_selector_all('[dir="auto"]')
                                    if name_elems:
                                        sender = name_elems[0].inner_text().strip()[:50]
                                        if len(name_elems) > 1:
                                            preview = name_elems[-1].inner_text().strip()[:100]
                                    
                                    if sender != 'Unknown' and sender not in ['LinkedIn', '']:
                                        msg_key = f"msg_{sender}_{preview[:20]}"
                                        if msg_key not in self.processed_messages:
                                            messages.append({
                                                'sender': sender,
                                                'preview': preview or 'No preview',
                                                'timestamp': datetime.now().isoformat()
                                            })
                                            self.processed_messages.add(msg_key)
                                            logger.info(f'    → MESSAGE DETECTED: {sender}')
                            except Exception as e:
                                logger.debug(f'Element error: {e}')
                                continue
                except Exception as e:
                    logger.debug(f'Selector error {selector[:30]}: {e}')
                    continue
            
            logger.info(f'Total messages found: {len(messages)}')
            return messages
            
        except Exception as e:
            logger.error(f'Message check error: {e}')
            return []

    def create_message_file(self, message: Dict):
        """Create file for detected message"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_sender = "".join(c for c in message['sender'] if c.isalnum() or c in ' -_').strip()
            filename = f'LINKEDIN_MESSAGE_{safe_sender}_{timestamp}.md'
            filepath = self.needs_action / filename
            
            content = f'''---
type: linkedin_message
created: {message['timestamp']}
---

# LinkedIn Message Detected

**From:** {message['sender']}  
**Detected:** {message['timestamp']}

## Preview
{message['preview']}

---
*Generated by LinkedIn Debug Watcher*
'''
            filepath.write_text(content, encoding='utf-8')
            logger.info(f'✓ Created: {filename}')
            
        except Exception as e:
            logger.error(f'File error: {e}')

    def run(self):
        """Run debug session"""
        logger.info('')
        logger.info('=' * 80)
        logger.info('STARTING DEBUG SESSION')
        logger.info('=' * 80)
        logger.info('This will:')
        logger.info('1. Open LinkedIn Messaging')
        logger.info('2. Take screenshots')
        logger.info('3. Try EVERY selector to find messages')
        logger.info('4. Save page HTML for analysis')
        logger.info('5. Create files for any messages found')
        logger.info('')
        logger.info('Please login to LinkedIn when browser opens...')
        logger.info('=' * 80)
        logger.info('')
        
        try:
            if not self.initialize_browser():
                logger.error('Failed to initialize!')
                return
            
            logger.info('Browser opened. Waiting 30 seconds for you to verify...')
            time.sleep(30)
            
            # Debug page content
            self.debug_page_content()
            
            # Check messages
            messages = self.check_messages_manual()
            
            # Create files for found messages
            for msg in messages:
                self.create_message_file(msg)
            
            logger.info('')
            logger.info('=' * 80)
            logger.info('DEBUG SESSION COMPLETE')
            logger.info('=' * 80)
            logger.info(f'Messages found: {len(messages)}')
            logger.info('')
            logger.info('Check these files for analysis:')
            logger.info(f'  - Logs: {self.logs_dir}')
            logger.info(f'  - Screenshots: {self.screenshots_dir}')
            logger.info(f'  - Message files: {self.needs_action}')
            logger.info('')
            logger.info('Press Enter to close browser...')
            input()
            
        except KeyboardInterrupt:
            logger.info('Stopped')
        except Exception as e:
            logger.error(f'Error: {e}')
        finally:
            if self.browser:
                self.browser.close()


def main():
    load_dotenv()
    vault_path = os.getenv('VAULT_PATH', r'C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault')
    watcher = LinkedInWatcher(vault_path=vault_path)
    watcher.run()


if __name__ == '__main__':
    main()
