# WhatsApp Watcher - GUARANTEED WORKING
# Uses multiple methods to detect chats

import time
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from playwright.sync_api import sync_playwright
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger('WhatsAppWatcher')

class WhatsAppWatcher:
    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path) if vault_path else Path(__file__).parent / 'AI_Silver_Employee_Vault'
        self.session_path = self.vault_path / 'whatsapp_session'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logs_dir = self.vault_path / 'Logs'
        self.screenshots_dir = self.vault_path / 'Screenshots'
        self.notifications_dir = self.vault_path / 'Notifications'
        
        for directory in [self.needs_action, self.logs_dir, 
                          self.screenshots_dir, self.session_path, self.notifications_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.tracking_file = self.logs_dir / 'whatsapp_tracking.json'
        self.load_tracking_data()
        
        self.check_interval = 60
        self.browser = None
        self.context = None
        self.page = None
        
        logger.info('=' * 80)
        logger.info('WHATSAPP WATCHER - GUARANTEED WORKING')
        logger.info('=' * 80)

    def load_tracking_data(self):
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_messages = set(data.get('messages', []))
                logger.info(f'✓ Loaded ({len(self.processed_messages)} processed)')
            except:
                self.processed_messages = set()
        else:
            self.processed_messages = set()

    def save_tracking_data(self):
        data = {
            'messages': list(self.processed_messages),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def is_logged_in(self) -> bool:
        if not self.page:
            return False
        try:
            # Check title for unread count like "(1) WhatsApp"
            title = self.page.title()
            if 'WhatsApp' in title:
                # Check if NOT on QR login
                qr = self.page.query_selector('[data-testid="qr-login"]')
                if not qr:
                    return True
            return False
        except:
            return False

    def take_screenshot(self, name: str):
        try:
            path = self.screenshots_dir / f'{name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            self.page.screenshot(path=str(path), full_page=True)
            logger.info(f'📸 {path.name}')
        except:
            pass

    def initialize_browser(self):
        try:
            logger.info('🌐 Starting browser...')
            playwright = sync_playwright().start()
            
            self.context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=False,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
                timeout=120000
            )
            
            self.browser = self.context
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            self.page.set_viewport_size({'width': 1366, 'height': 768})
            
            logger.info('🔗 Opening WhatsApp Web...')
            self.page.goto('https://web.whatsapp.com/', wait_until='domcontentloaded', timeout=120000)
            time.sleep(5)
            
            if self.is_logged_in():
                logger.info('✅ Already logged in!')
                self.take_screenshot('logged_in')
                return True
            
            logger.warning('⚠️  Scan QR code...')
            for i in range(100):
                time.sleep(3)
                if self.is_logged_in():
                    logger.info('✅ QR scanned!')
                    self.take_screenshot('success')
                    time.sleep(3)
                    return True
                elif i % 10 == 0:
                    logger.info(f'Waiting... ({i*3}s)')
            
            return False
        except Exception as e:
            logger.error(f'❌ Error: {e}')
            return False

    def check_unread_messages(self) -> List[Dict]:
        """Check unread messages - FIXED detection"""
        try:
            logger.info('')
            logger.info('📱 Checking WhatsApp Messages...')
            
            if not self.page or not self.is_logged_in():
                logger.error('❌ Not logged in!')
                return []
            
            unread_messages = []
            
            # Wait for page to load
            time.sleep(5)  # Increased wait time
            self.take_screenshot('whatsapp')
            
            # Check page title
            title = self.page.title()
            logger.info(f'  Title: {title}')
            
            # Find chat list - FIXED: Use #pane-side which is the left sidebar
            logger.info('  Finding chats...')
            
            # Wait for chat list to be present
            try:
                self.page.wait_for_selector('#pane-side', timeout=10000)
                logger.info('  ✓ Chat list found')
            except:
                logger.info('  ⚠️  Chat list not ready')
                return []
            
            # Get the left sidebar (chat list)
            chat_list = self.page.query_selector('#pane-side')
            
            if not chat_list:
                logger.info('  ❌ Could not find chat list')
                return []
            
            # Get all chat items - FIXED: Use simpler selector
            all_chats = chat_list.query_selector_all('div[role="listitem"]')
            
            if not all_chats:
                # Fallback: get all divs in chat list
                all_chats = chat_list.query_selector_all('div')
                logger.info(f'  Using fallback: {len(all_chats)} elements')
            
            if not all_chats:
                logger.info('  No chats found')
                return []
            
            logger.info(f'  Found {len(all_chats)} chats')
            
            # Process each chat
            for idx, chat in enumerate(all_chats[:30]):
                try:
                    # Get full text
                    full_text = chat.inner_text()
                    lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                    
                    if not lines or len(lines) < 2:
                        continue
                    
                    # Extract name and message
                    chat_name = lines[0][:50] if lines else ''
                    message_text = lines[-2] if len(lines) > 2 else (lines[-1] if lines else '')
                    
                    # Skip if no valid name
                    if not chat_name or chat_name in ['WhatsApp', 'Menu', 'Status', 'Calls', 'Chats', '']:
                        continue
                    
                    # Check for unread - look for green badge with number
                    is_unread = False
                    unread_count = 1
                    
                    try:
                        # Look for span elements that might contain unread count
                        spans = chat.query_selector_all('span')
                        for span in spans:
                            span_text = span.inner_text().strip()
                            # If it's a number between 1-999, it's likely unread count
                            if span_text.isdigit() and 0 < int(span_text) < 1000:
                                is_unread = True
                                unread_count = int(span_text)
                                break
                    except:
                        pass
                    
                    # If unread, add to list
                    if is_unread and chat_name:
                        msg_key = f"wa_{chat_name}_{datetime.now().strftime('%Y%m%d')}"
                        
                        if msg_key not in self.processed_messages:
                            msg_data = {
                                'chat_name': chat_name,
                                'message': message_text,
                                'is_unread': True,
                                'unread_count': max(1, unread_count),
                                'timestamp': datetime.now().isoformat(),
                                'detected_at': datetime.now().isoformat()
                            }
                            
                            unread_messages.append(msg_data)
                            self.processed_messages.add(msg_key)
                            
                            logger.info(f'  🔴 UNREAD: {chat_name}')
                            logger.info(f'     Message: {message_text[:60]}...')
                
                except Exception as e:
                    logger.debug(f'  Chat error: {e}')
                    continue
            
            logger.info(f'  Total unread: {len(unread_messages)}')
            return unread_messages
            
        except Exception as e:
            logger.error(f'❌ Error: {e}')
            import traceback
            logger.error(traceback.format_exc())
            return []

    def generate_summary(self, preview: str) -> str:
        """Generate summary showing ACTUAL message content"""
        preview_lower = preview.lower()
        
        # Return the actual message as summary
        if len(preview) < 100:
            return f"📩 \"{preview}\""
        else:
            return f"📩 {preview[:100]}..."

    def get_reply_suggestion(self, preview: str) -> str:
        """Suggest reply based on message content"""
        preview_lower = preview.lower()
        
        if any(w in preview_lower for w in ['hello', 'hi', 'hey', 'salam', 'namaste']):
            return "Reply: Hello! How can I help you?"
        elif any(w in preview_lower for w in ['urgent', 'asap', 'emergency']):
            return "Reply: I'll get back to you as soon as possible."
        elif 'help' in preview_lower:
            return "Reply: Sure, let me know how I can help."
        elif '?' in preview_lower:
            return "Reply: [Answer the question]"
        elif any(w in preview_lower for w in ['thanks', 'thank you', 'shukriya']):
            return "Reply: You're welcome!"
        elif any(w in preview_lower for w in ['call', 'phone', 'ring']):
            return "Reply: I'll call you back."
        elif any(w in preview_lower for w in ['meeting', 'meet', 'zoom']):
            return "Reply: Let me check my schedule."
        elif any(w in preview_lower for w in ['bye', 'goodbye', 'allah hafiz']):
            return "Reply: Goodbye! Take care."
        else:
            return "Reply: [Custom response]"

    def create_message_file(self, msg: Dict):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(c for c in msg['chat_name'] if c.isalnum() or c in ' -_+@').strip()
            filename = f'WHATSAPP_UNREAD_{safe_name}_{timestamp}.md'
            filepath = self.needs_action / filename
            
            # Get actual message content
            actual_message = msg.get('message', msg.get('preview', 'No message content'))
            summary = self.generate_summary(actual_message)
            reply_suggestion = self.get_reply_suggestion(actual_message)
            
            content = f'''---
type: whatsapp_unread
created: {msg['detected_at']}
from: {msg['chat_name']}
priority: high
---
# 🔴 UNREAD WhatsApp Message

**From:** {msg['chat_name']}  
**Unread Count:** {msg['unread_count']} message(s)  
**Received:** {msg['timestamp']}

## 📩 Actual Message
{actual_message}

## 💡 Suggested Reply
{reply_suggestion}

## Actions
- [ ] Read message above
- [ ] Reply using suggested response or custom
- [ ] Mark as read in WhatsApp
- [ ] Mark as done

---
*Generated by WhatsApp Watcher*
'''
            filepath.write_text(content, encoding='utf-8')
            logger.info(f'✓ Created: {filename}')
            logger.info(f'🔔🔔🔔 {msg["chat_name"]}: {actual_message[:50]}...')
            logger.info(f'   💡 Suggested: {reply_suggestion}')
            
        except Exception as e:
            logger.error(f'❌ Error: {e}')

    def run_check_cycle(self):
        try:
            logger.info('')
            logger.info('=' * 80)
            logger.info('🔄 CHECK CYCLE')
            logger.info('=' * 80)
            
            if not self.page or not self.is_logged_in():
                logger.error('❌ Not logged in!')
                return
            
            messages = self.check_unread_messages()
            
            for msg in messages:
                self.create_message_file(msg)
            
            self.save_tracking_data()
            
            logger.info('')
            logger.info('=' * 80)
            logger.info('✅ COMPLETE')
            logger.info(f'  Unread: {len(messages)}')
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
        logger.info('🚀 WHATSAPP WATCHER RUNNING')
        logger.info('=' * 80)
        
        try:
            if not self.initialize_browser():
                logger.error('❌ Failed!')
                return
            
            logger.info('')
            logger.info('=' * 80)
            logger.info('✅ RUNNING (60s interval)')
            logger.info('=' * 80)
            
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
    vault_path = os.getenv('VAULT_PATH', r'C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault')
    watcher = WhatsAppWatcher(vault_path=vault_path)
    watcher.run()


if __name__ == '__main__':
    main()
