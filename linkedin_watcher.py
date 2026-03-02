# LinkedIn Watcher - SESSION SAVING VERSION
# Login once, session saved for future runs

import time
import logging
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger('LinkedInWatcher')

class LinkedInWatcher:
    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path) if vault_path else Path(__file__).parent / 'AI_Silver_Employee_Vault'
        self.session_path = self.vault_path / 'linkedin_session'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.posts_dir = self.vault_path / 'Posts'
        self.logs_dir = self.vault_path / 'Logs'
        self.screenshots_dir = self.vault_path / 'Screenshots'
        self.notifications_dir = self.vault_path / 'Notifications'
        
        for directory in [self.needs_action, self.posts_dir, self.logs_dir, 
                          self.screenshots_dir, self.session_path, self.notifications_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        load_dotenv()
        self.company_name = os.getenv('COMPANY_NAME', 'Your Company')
        
        self.tracking_file = self.logs_dir / 'linkedin_tracking.json'
        self.load_tracking_data()
        
        self.last_post_time = datetime.now() - timedelta(hours=8)
        self.check_interval = 300  # 5 minutes
        self.post_interval = 8 * 3600  # 8 hours
        
        self.products = ['AI Automation Solutions', 'Business Consulting', 
                        'Digital Marketing Services', 'Custom Software Development']
        
        self.opportunity_keywords = ['looking for', 'hiring', 'need help', 
                                     'partnership', 'opportunity', 'seeking']
        
        self.browser = None
        self.context = None
        self.page = None
        
        logger.info('=' * 80)
        logger.info('LINKEDIN WATCHER - SESSION SAVING')
        logger.info('=' * 80)
        logger.info(f'Session saved in: {self.session_path}')
        logger.info('Login once, session will be saved!')
        logger.info('=' * 80)

    def load_tracking_data(self):
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_messages = set(data.get('messages', []))
                    self.processed_connections = set(data.get('connections', []))
                    self.processed_notifications = set(data.get('notifications', []))
                    self.processed_opportunities = set(data.get('opportunities', []))
                    last_post = data.get('last_post')
                    if last_post:
                        self.last_post_time = datetime.fromisoformat(last_post)
                logger.info(f'✓ Loaded tracking data')
            except:
                self.processed_messages = set()
                self.processed_connections = set()
                self.processed_notifications = set()
                self.processed_opportunities = set()
        else:
            self.processed_messages = set()
            self.processed_connections = set()
            self.processed_notifications = set()
            self.processed_opportunities = set()

    def save_tracking_data(self):
        data = {
            'messages': list(self.processed_messages),
            'connections': list(self.processed_connections),
            'notifications': list(self.processed_notifications),
            'opportunities': list(self.processed_opportunities),
            'last_post': self.last_post_time.isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def is_logged_in(self) -> bool:
        """Check if actually logged in by looking for logged-in indicators"""
        if not self.page:
            return False
        try:
            url = self.page.url.lower()
            
            # If on login page, definitely not logged in
            if 'login' in url or 'auth' in url or 'checkpoint' in url:
                return False
            
            # Check for actual logged-in indicators on the page
            try:
                # Look for profile menu (only visible when logged in)
                profile_menu = self.page.query_selector('[data-testid="me-dropdown"], [aria-label="Me"]')
                if profile_menu:
                    return True
                
                # Look for messaging icon (only visible when logged in)
                messaging_icon = self.page.query_selector('[aria-label*="Messaging"], [data-testid*="messaging"]')
                if messaging_icon:
                    return True
                
                # Look for notifications icon (only visible when logged in)
                notifications_icon = self.page.query_selector('[aria-label*="Notifications"], [data-testid*="notifications"]')
                if notifications_icon:
                    return True
                
                # Look for feed navigation
                if '/feed' in url or '/messaging' in url or '/mynetwork' in url:
                    # Check if page actually loaded (not redirecting to login)
                    time.sleep(1)
                    current_url = self.page.url.lower()
                    if 'login' not in current_url and 'auth' not in current_url:
                        return True
                
                return False
                
            except:
                return False
            
        except Exception as e:
            logger.debug(f'Login check error: {e}')
            return False

    def take_screenshot(self, name: str):
        try:
            path = self.screenshots_dir / f'{name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            self.page.screenshot(path=str(path), full_page=True)
            logger.info(f'📸 Screenshot: {path.name}')
        except Exception as e:
            logger.debug(f'Screenshot failed: {e}')

    def initialize_browser(self):
        """Initialize browser with SESSION PERSISTENCE - FIXED"""
        try:
            logger.info('🌐 Starting browser...')
            logger.info(f'  Session path: {self.session_path}')
            
            # Create session directory if it doesn't exist
            if not self.session_path.exists():
                self.session_path.mkdir(parents=True, exist_ok=True)
                logger.info('  ✓ Created session directory')
            else:
                logger.info('  ✓ Found saved session!')
            
            playwright = sync_playwright().start()
            
            # Launch with PERSISTENT context - saves cookies/localStorage
            self.context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),  # Session saved here
                headless=False,  # Visible browser
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-features=IsolateOrigins,site-per-process'
                ],
                timeout=120000
            )
            
            self.browser = self.context
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            self.page.set_viewport_size({'width': 1366, 'height': 768})
            
            # Go to LinkedIn
            logger.info('🔗 Opening LinkedIn...')
            self.page.goto('https://www.linkedin.com/', wait_until='domcontentloaded', timeout=120000)
            time.sleep(5)
            
            # Wait for page to fully load
            time.sleep(3)
            
            # Take screenshot for debugging
            self.take_screenshot('initial_page')
            
            # Check if already logged in (from saved session)
            if self.is_logged_in():
                logger.info('✅ Already logged in (session loaded)!')
                logger.info(f'   Current URL: {self.page.url}')
                self.take_screenshot('logged_in')
                return True
            
            # Not logged in - wait for manual login
            logger.warning('')
            logger.warning('=' * 80)
            logger.warning('⚠️  PLEASE LOGIN TO LINKEDIN')
            logger.warning('=' * 80)
            logger.warning('This is required only ONCE!')
            logger.warning('After login, session will be SAVED permanently.')
            logger.warning('Next time you run, NO login needed!')
            logger.warning('')
            logger.warning('You have 5 minutes (300 seconds)...')
            logger.warning('')
            
            for i in range(100):  # 5 minutes
                time.sleep(3)
                
                if self.is_logged_in():
                    logger.info('✅ Login detected!')
                    logger.info(f'   Logged in as: {self.page.url}')
                    self.take_screenshot('login_success')
                    time.sleep(5)  # Wait for session to save
                    logger.info('')
                    logger.info('✓✓✓ Session SAVED permanently! ✓✓✓')
                    logger.info('Next time: NO login required!')
                    return True
                
                elif i % 10 == 0:
                    logger.info(f'Waiting for login... ({i*3}s / 300s)')
                    # Take periodic screenshots for debugging
                    if i == 30:  # After 90 seconds
                        self.take_screenshot('waiting_login')
            
            logger.error('❌ Login timeout!')
            self.take_screenshot('login_timeout')
            return False
            
        except Exception as e:
            logger.error(f'❌ Browser error: {e}')
            import traceback
            logger.error(traceback.format_exc())
            return False

    def check_messages(self) -> List[Dict]:
        """Check ALL messages (Read + Unread)"""
        try:
            logger.info('')
            logger.info('📧 Checking LinkedIn Messages...')
            
            if not self.page or not self.is_logged_in():
                logger.error('❌ Not logged in!')
                return []
            
            messages = []
            
            # Navigate to messaging
            logger.info('  Opening messaging...')
            try:
                self.page.goto('https://www.linkedin.com/messaging/', 
                             wait_until='domcontentloaded', timeout=60000)
                time.sleep(5)
                self.take_screenshot('messages')
            except Exception as e:
                logger.error(f'  ❌ Failed: {e}')
                return []
            
            # Get all chat items
            logger.info('  Finding messages...')
            
            # Wait for messages to load
            try:
                self.page.wait_for_selector('[role="listitem"]', timeout=10000)
            except:
                logger.info('  ⚠️  No messages loaded')
                return []
            
            # Get all message threads
            all_chats = self.page.query_selector_all('[role="listitem"]')
            
            if not all_chats:
                logger.info('  No chats found')
                return []
            
            logger.info(f'  Found {len(all_chats)} chats')
            
            # Process each chat
            for idx, chat in enumerate(all_chats[:30]):
                try:
                    text = chat.inner_text()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    
                    if not lines or len(lines) < 2:
                        continue
                    
                    # Extract name and message
                    chat_name = lines[0][:50] if lines else ''
                    message_text = lines[-2] if len(lines) > 2 else (lines[-1] if lines else '')
                    
                    # Skip system
                    if not chat_name or chat_name in ['LinkedIn', 'Menu', '']:
                        continue
                    
                    # Check for unread
                    is_unread = False
                    try:
                        class_attr = chat.get_attribute('class') or ''
                        if 'unread' in class_attr.lower():
                            is_unread = True
                    except:
                        pass
                    
                    # Create message
                    msg_key = f"li_{chat_name}_{datetime.now().strftime('%Y%m%d')}"
                    
                    if msg_key not in self.processed_messages:
                        msg_data = {
                            'sender': chat_name,
                            'preview': message_text,
                            'is_unread': is_unread,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        messages.append(msg_data)
                        self.processed_messages.add(msg_key)
                        
                        status = "🔴 UNREAD" if is_unread else "⚪ READ"
                        logger.info(f'  {status}: {chat_name}')
                        if message_text:
                            logger.info(f'     {message_text[:60]}...')
                
                except Exception as e:
                    logger.debug(f'  Chat error: {e}')
                    continue
            
            logger.info(f'  Total: {len(messages)} messages')
            return messages
            
        except Exception as e:
            logger.error(f'❌ Message error: {e}')
            return []

    def check_notifications(self) -> List[Dict]:
        """Check notifications"""
        try:
            logger.info('')
            logger.info('🔔 Checking Notifications...')
            
            if not self.page or not self.is_logged_in():
                return []
            
            notifications = []
            
            try:
                self.page.goto('https://www.linkedin.com/notifications/', 
                             wait_until='domcontentloaded', timeout=60000)
                time.sleep(3)
            except Exception as e:
                logger.error(f'  ❌ Failed: {e}')
                return []
            
            items = self.page.query_selector_all('[class*="notification-item"]')
            
            if not items:
                logger.info('  No notifications')
                return []
            
            logger.info(f'  Found {len(items)} notifications')
            
            for item in items[:15]:
                try:
                    text_elem = item.query_selector('[dir="auto"], span')
                    text = text_elem.inner_text().strip() if text_elem else ''
                    
                    if not text or len(text) < 10:
                        continue
                    
                    is_unread = False
                    try:
                        class_attr = item.get_attribute('class') or ''
                        if 'unread' in class_attr.lower():
                            is_unread = True
                    except:
                        pass
                    
                    notif_key = f"notif_{text[:40]}_{datetime.now().strftime('%Y%m%d_%H%M')}"
                    
                    if notif_key not in self.processed_notifications:
                        notifications.append({
                            'text': text[:200],
                            'is_unread': is_unread,
                            'timestamp': datetime.now().isoformat()
                        })
                        self.processed_notifications.add(notif_key)
                        
                        status = "🔔 NEW" if is_unread else "⚪ READ"
                        logger.info(f'  {status}: {text[:60]}...')
                
                except:
                    continue
            
            return notifications
            
        except Exception as e:
            logger.error(f'❌ Notification error: {e}')
            return []

    def check_connections(self) -> List[Dict]:
        """Check connection requests"""
        try:
            logger.info('')
            logger.info('🤝 Checking Connections...')
            
            if not self.page or not self.is_logged_in():
                return []
            
            connections = []
            
            try:
                self.page.goto('https://www.linkedin.com/mynetwork/', 
                             wait_until='domcontentloaded', timeout=60000)
                time.sleep(3)
            except Exception as e:
                logger.error(f'  ❌ Failed: {e}')
                return []
            
            requests = self.page.query_selector_all('[class*="mn-invitation-card"]')
            
            if not requests:
                logger.info('  No pending requests')
                return []
            
            logger.info(f'  Found {len(requests)} pending requests')
            
            for req in requests[:10]:
                try:
                    accept_btn = req.query_selector('button:has-text("Accept")')
                    if not accept_btn:
                        continue
                    
                    name_elem = req.query_selector('[class*="mn-person-info__name"] a')
                    name = name_elem.inner_text().strip() if name_elem else 'Unknown'
                    
                    headline_elem = req.query_selector('[class*="headline"]')
                    headline = headline_elem.inner_text().strip() if headline_elem else ''
                    
                    if name != 'Unknown' and name not in self.processed_connections:
                        connections.append({
                            'name': name,
                            'headline': headline or 'No headline',
                            'timestamp': datetime.now().isoformat()
                        })
                        self.processed_connections.add(name)
                        logger.info(f'  📩 {name}')
                
                except:
                    continue
            
            return connections
            
        except Exception as e:
            logger.error(f'❌ Connection error: {e}')
            return []

    def check_opportunities(self) -> List[Dict]:
        """Check feed for opportunities"""
        try:
            logger.info('')
            logger.info('💼 Checking Opportunities...')
            
            if not self.page or not self.is_logged_in():
                return []
            
            opportunities = []
            
            try:
                self.page.goto('https://www.linkedin.com/feed/', 
                             wait_until='domcontentloaded', timeout=60000)
                time.sleep(3)
            except Exception as e:
                logger.error(f'  ❌ Failed: {e}')
                return []
            
            posts = self.page.query_selector_all('[class*="feed-shared-update"]')
            logger.info(f'  Found {len(posts)} posts')
            
            for post in posts[:20]:
                try:
                    text_elem = post.query_selector('[class*="update-components-text"]')
                    text = text_elem.inner_text().strip() if text_elem else ''
                    
                    if not text or len(text) < 20:
                        continue
                    
                    keywords = [kw for kw in self.opportunity_keywords if kw in text.lower()]
                    
                    if keywords:
                        author_elem = post.query_selector('[class*="feed-shared-actor-name"]')
                        author = author_elem.inner_text().strip() if author_elem else 'Unknown'
                        
                        opp_key = f"{author}_{text[:50]}"
                        
                        if opp_key not in self.processed_opportunities:
                            opportunities.append({
                                'author': author,
                                'text': text[:300],
                                'keywords': keywords,
                                'timestamp': datetime.now().isoformat()
                            })
                            self.processed_opportunities.add(opp_key)
                            logger.info(f'  💰 {author}: {keywords}')
                
                except:
                    continue
            
            return opportunities
            
        except Exception as e:
            logger.error(f'❌ Opportunity error: {e}')
            return []

    def generate_business_post(self) -> str:
        product = random.choice(self.products)
        templates = [
            f"🚀 Exciting news! Our {product} is helping businesses. #{self.company_name.replace(' ', '')} #Business",
            f"💡 {product} can increase efficiency by 40%! Message me. #{self.company_name.replace(' ', '')} #Growth"
        ]
        return random.choice(templates)

    def post_to_linkedin(self, content: str) -> bool:
        try:
            logger.info('')
            logger.info('📝 Posting to LinkedIn...')
            
            if not self.page:
                return False
            
            self.page.goto('https://www.linkedin.com/post/new', wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            editor = self.page.query_selector('div[role="textbox"][contenteditable="true"]')
            if not editor:
                logger.error('  ❌ No editor found')
                return False
            
            editor.click()
            time.sleep(1)
            editor.type(content, delay=30)
            time.sleep(2)
            
            post_button = self.page.query_selector('button[type="submit"]')
            if post_button:
                post_button.click()
                time.sleep(3)
                logger.info('  ✅ Post published!')
                self.save_post(content)
                return True
            
            logger.error('  ❌ No post button')
            return False
            
        except Exception as e:
            logger.error(f'  ❌ Post error: {e}')
            return False

    def save_post(self, content: str):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'LINKEDIN_POST_{timestamp}.md'
        filepath = self.posts_dir / filename
        content_md = f'''---
type: linkedin_post
posted: {datetime.now().isoformat()}
---
# LinkedIn Post
{content}
'''
        filepath.write_text(content_md, encoding='utf-8')

    def should_post_now(self) -> bool:
        return (datetime.now() - self.last_post_time).total_seconds() >= self.post_interval

    def create_message_file(self, msg: Dict):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_sender = "".join(c for c in msg['sender'] if c.isalnum() or c in ' -_').strip()
            status = "UNREAD" if msg['is_unread'] else "READ"
            filename = f'LINKEDIN_{status}_MESSAGE_{safe_sender}_{timestamp}.md'
            filepath = self.needs_action / filename
            
            content = f'''---
type: linkedin_{status.lower()}_message
created: {msg['timestamp']}
---
# {"🔴 UNREAD" if msg['is_unread'] else "⚪ READ"} LinkedIn Message

**From:** {msg['sender']}  
**Status:** {status}

## Preview
{msg['preview']}

## Actions
- [ ] {"Read and respond" if msg['is_unread'] else "Review"}
- [ ] Mark as done

---
*LinkedIn Watcher*
'''
            filepath.write_text(content, encoding='utf-8')
            logger.info(f'✓ Created: {filename}')
            
            if msg['is_unread']:
                logger.info(f'🔔🔔🔔 UNREAD: {msg["sender"]}')
                
        except Exception as e:
            logger.error(f'❌ File error: {e}')

    def create_notification_file(self, notif: Dict):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'LINKEDIN_NOTIFICATION_{timestamp}.md'
            filepath = self.needs_action / filename
            
            content = f'''---
type: notification
status: {"unread" if notif['is_unread'] else "read"}
---
# 🔔 Notification

**Received:** {notif['timestamp']}

## {notif['text']}

## Actions
- [ ] Review
- [ ] Mark as done

---
*LinkedIn Watcher*
'''
            filepath.write_text(content, encoding='utf-8')
            logger.info(f'✓ Created: {filename}')
        except Exception as e:
            logger.error(f'❌ File error: {e}')

    def create_connection_file(self, conn: Dict):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(c for c in conn['name'] if c.isalnum() or c in ' -_').strip()
            filename = f'LINKEDIN_CONNECTION_{safe_name}_{timestamp}.md'
            filepath = self.needs_action / filename
            
            content = f'''---
type: pending_connection
---
# 🤝 Connection Request

**From:** {conn['name']}  
**Headline:** {conn['headline']}

## Actions
- [ ] Accept or decline
- [ ] Mark as done

---
*LinkedIn Watcher*
'''
            filepath.write_text(content, encoding='utf-8')
            logger.info(f'✓ Created: {filename}')
        except Exception as e:
            logger.error(f'❌ File error: {e}')

    def create_opportunity_file(self, opp: Dict):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_author = "".join(c for c in opp['author'] if c.isalnum() or c in ' -_').strip()
            filename = f'LINKEDIN_OPPORTUNITY_{safe_author}_{timestamp}.md'
            filepath = self.needs_action / filename
            
            content = f'''---
type: opportunity
keywords: {', '.join(opp['keywords'])}
---
# 💼 Opportunity

**From:** {opp['author']}  
**Keywords:** {', '.join(opp['keywords'])}

## Post
{opp['text']}

## Actions
- [ ] Engage
- [ ] Mark as done

---
*LinkedIn Watcher*
'''
            filepath.write_text(content, encoding='utf-8')
            logger.info(f'✓ Created: {filename}')
        except Exception as e:
            logger.error(f'❌ File error: {e}')

    def run_check_cycle(self):
        try:
            logger.info('')
            logger.info('=' * 80)
            logger.info('🔄 CHECK CYCLE')
            logger.info('=' * 80)
            
            if not self.page or not self.is_logged_in():
                logger.error('❌ Not logged in!')
                return
            
            # Messages
            messages = self.check_messages()
            for msg in messages:
                self.create_message_file(msg)
            
            # Notifications
            notifications = self.check_notifications()
            for notif in notifications:
                self.create_notification_file(notif)
            
            # Connections
            connections = self.check_connections()
            for conn in connections:
                self.create_connection_file(conn)
            
            # Opportunities
            opportunities = self.check_opportunities()
            for opp in opportunities:
                self.create_opportunity_file(opp)
            
            # Post
            if self.should_post_now():
                content = self.generate_business_post()
                if self.post_to_linkedin(content):
                    self.last_post_time = datetime.now()
            
            self.save_tracking_data()
            
            logger.info('')
            logger.info('=' * 80)
            logger.info('✅ COMPLETE')
            logger.info(f'  Messages: {len(messages)}')
            logger.info(f'  Notifications: {len(notifications)}')
            logger.info(f'  Connections: {len(connections)}')
            logger.info(f'  Opportunities: {len(opportunities)}')
            logger.info('=' * 80)
            
        except Exception as e:
            logger.error(f'❌ Cycle error: {e}')

    def close(self):
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        self.browser = None
        self.context = None
        self.page = None

    def run(self):
        logger.info('')
        logger.info('=' * 80)
        logger.info('🚀 LINKEDIN WATCHER - SESSION SAVING')
        logger.info('=' * 80)
        logger.info('Features:')
        logger.info('  ✓ Login ONCE - session saved!')
        logger.info('  ✓ ALL Messages (Read + Unread)')
        logger.info('  ✓ ALL Notifications')
        logger.info('  ✓ Connection Requests')
        logger.info('  ✓ Business Opportunities')
        logger.info('  ✓ Auto-posting every 8 hours')
        logger.info('=' * 80)
        
        try:
            if not self.initialize_browser():
                logger.error('❌ Failed!')
                return
            
            logger.info('')
            logger.info('=' * 80)
            logger.info('✅ RUNNING - Session will be saved!')
            logger.info('=' * 80)
            logger.info('Press Ctrl+C to stop')
            logger.info('')
            
            while True:
                try:
                    self.run_check_cycle()
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f'Error: {e}')
                    time.sleep(10)
                    self.close()
                    self.initialize_browser()
                        
        except KeyboardInterrupt:
            logger.info('⏹️  Stopped')
        except Exception as e:
            logger.error(f'❌ Fatal: {e}')
        finally:
            self.close()
            self.save_tracking_data()


def main():
    load_dotenv()
    vault_path = os.getenv('VAULT_PATH', r'C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault')
    watcher = LinkedInWatcher(vault_path=vault_path)
    watcher.run()


if __name__ == '__main__':
    main()
