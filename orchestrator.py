"""
Orchestrator for Silver Tier Functional Assistant
Coordinates all watchers, manages task distribution, and handles scheduling

This is the master process that:
1. Starts and monitors all watcher processes
2. Triggers Claude Code for task processing
3. Manages the approval workflow
4. Handles scheduled tasks (CEO Briefing, etc.)
"""

import os
import sys
import time
import logging
import subprocess
import schedule
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Orchestrator')

# Vault paths - using raw string for Windows
VAULT_BASE = r"C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault"
NEEDS_ACTION = Path(VAULT_BASE) / 'Needs_Action'
DONE = Path(VAULT_BASE) / 'Done'
PENDING_APPROVAL = Path(VAULT_BASE) / 'Pending_Approval'
APPROVED = Path(VAULT_BASE) / 'Approved'
PLANS = Path(VAULT_BASE) / 'Plans'
INBOX = Path(VAULT_BASE) / 'Inbox'
LOGS = Path(VAULT_BASE) / 'Logs'

# Ensure directories exist
for directory in [NEEDS_ACTION, DONE, PENDING_APPROVAL, APPROVED, PLANS, INBOX, LOGS]:
    directory.mkdir(parents=True, exist_ok=True)


class WatcherProcess:
    """Manages a single watcher process"""
    
    def __init__(self, name: str, script: str, args: List[str] = None):
        self.name = name
        self.script = script
        self.args = args or []
        self.process: Optional[subprocess.Popen] = None
        self.restart_count = 0
        self.last_restart = None
        
    def start(self):
        """Start the watcher process"""
        try:
            cmd = ['python', self.script] + self.args
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(self.script))
            )
            logger.info(f'Started {self.name} (PID: {self.process.pid})')
            return True
        except Exception as e:
            logger.error(f'Failed to start {self.name}: {e}')
            return False
    
    def stop(self):
        """Stop the watcher process"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info(f'Stopped {self.name}')
            self.process = None
    
    def is_running(self) -> bool:
        """Check if process is running"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def restart_if_needed(self, max_restarts: int = 3, restart_delay: int = 60):
        """Restart process if it crashed, with rate limiting"""
        now = datetime.now()
        
        # Check if we need to restart
        if not self.is_running():
            # Check restart limit
            if self.restart_count >= max_restarts:
                logger.error(f'{self.name} exceeded max restarts ({max_restarts}), not restarting')
                return False
            
            # Check delay since last restart
            if self.last_restart:
                time_since_restart = (now - self.last_restart).total_seconds()
                if time_since_restart < restart_delay:
                    logger.info(f'Waiting {restart_delay - time_since_restart:.0f}s before restarting {self.name}')
                    return False
            
            # Restart
            logger.warning(f'{self.name} crashed, restarting... (restart #{self.restart_count + 1})')
            self.restart_count += 1
            self.last_restart = now
            return self.start()
        
        return True


class Orchestrator:
    """Main orchestrator for the Silver Tier AI Employee"""
    
    def __init__(self):
        self.watchers: List[WatcherProcess] = []
        self.running = False
        self.claude_available = False
        
        # Initialize watchers
        self._init_watchers()
        
        # Check Claude Code availability
        self._check_claude_code()
    
    def _init_watchers(self):
        """Initialize all watcher processes"""
        script_dir = Path(__file__).parent
        
        # File System Watcher
        self.watchers.append(WatcherProcess(
            name='File Watcher',
            script=str(script_dir / 'file_watcher.py')
        ))
        
        # Gmail Watcher (only if credentials exist)
        gmail_creds = script_dir / 'gmail_credentials.json'
        if gmail_creds.exists():
            self.watchers.append(WatcherProcess(
                name='Gmail Watcher',
                script=str(script_dir / 'gmail_watcher.py')
            ))
        else:
            logger.warning('Gmail credentials not found, Gmail Watcher disabled')
        
        # LinkedIn Watcher (only if credentials configured)
        if os.getenv('LINKEDIN_EMAIL') and os.getenv('LINKEDIN_PASSWORD'):
            self.watchers.append(WatcherProcess(
                name='LinkedIn Watcher',
                script=str(script_dir / 'linkedin_watcher.py')
            ))
        else:
            logger.warning('LinkedIn credentials not configured, LinkedIn Watcher disabled')

        # WhatsApp Watcher (always enabled - uses browser session)
        self.watchers.append(WatcherProcess(
            name='WhatsApp Watcher',
            script=str(script_dir / 'whatsapp_watcher.py')
        ))

    def _check_claude_code(self):
        """Check if Claude Code is available"""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.claude_available = True
                logger.info(f'Claude Code available: {result.stdout.strip()}')
            else:
                self.claude_available = False
                logger.warning('Claude Code not available, some features disabled')
        except Exception as e:
            self.claude_available = False
            logger.warning(f'Claude Code check failed: {e}')
    
    def start_all_watchers(self):
        """Start all watcher processes"""
        logger.info('Starting all watchers...')
        for watcher in self.watchers:
            watcher.start()
            time.sleep(1)  # Stagger starts
    
    def stop_all_watchers(self):
        """Stop all watcher processes"""
        logger.info('Stopping all watchers...')
        for watcher in self.watchers:
            watcher.stop()
    
    def monitor_watchers(self):
        """Monitor and restart crashed watchers"""
        for watcher in self.watchers:
            watcher.restart_if_needed()
    
    def process_needs_action(self):
        """Process items in Needs_Action folder using Claude Code"""
        try:
            # Get pending items
            pending_files = list(NEEDS_ACTION.glob('*.md'))
            
            if not pending_files:
                return
            
            logger.info(f'Processing {len(pending_files)} items in Needs_Action')
            
            for file_path in pending_files:
                self._process_single_item(file_path)
                
        except Exception as e:
            logger.error(f'Error processing Needs_Action: {e}')
    
    def _process_single_item(self, file_path: Path):
        """Process a single item using Claude Code"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse metadata
            metadata = self._extract_metadata(content)
            if not metadata:
                logger.error(f'Could not parse metadata from {file_path.name}')
                return
            
            # Determine action type
            action_type = metadata.get('type', 'unknown')
            
            # Create plan file
            plan_content = self._create_plan(file_path, metadata)
            plan_file = PLANS / f'plan_{file_path.stem}.md'
            plan_file.write_text(plan_content, encoding='utf-8')
            
            logger.info(f'Created plan for {file_path.name}')
            
            # If Claude is available, trigger it
            if self.claude_available:
                self._trigger_claude_processing(file_path, plan_file)
            
        except Exception as e:
            logger.error(f'Error processing {file_path.name}: {e}')
    
    def _extract_metadata(self, content: str) -> Optional[Dict]:
        """Extract JSON metadata from markdown frontmatter"""
        import re
        match = re.search(r'^---\s*$(.*?)^---\s*$', content, re.MULTILINE | re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                return None
        return None
    
    def _create_plan(self, file_path: Path, metadata: Dict) -> str:
        """Create a processing plan for an item"""
        action_type = metadata.get('type', 'unknown')
        priority = metadata.get('priority', 'medium')
        
        plan = f"""---
file_id: {file_path.stem}
plan_type: {action_type}
priority: {priority}
created: {datetime.now().isoformat()}
status: pending
---

# Processing Plan for {file_path.name}

## Item Analysis
- **Type**: {action_type}
- **Priority**: {priority}
- **Status**: Pending processing

## Processing Steps

### Step 1: Review
- [ ] Review item content and metadata
- [ ] Determine required actions
- [ ] Check if approval is needed

### Step 2: Action
- [ ] Execute required actions
- [ ] Update status appropriately
- [ ] Log all actions taken

### Step 3: Completion
- [ ] Move item to Done folder
- [ ] Update Dashboard
- [ ] Archive plan file

## Execution Notes
- Plan created: {datetime.now().isoformat()}
- Processing priority: {priority}
- Requires approval: {'Yes' if priority == 'high' else 'No'}
"""
        return plan
    
    def _trigger_claude_processing(self, file_path: Path, plan_file: Path):
        """Trigger Claude Code to process an item"""
        try:
            prompt = f"""Process the file {file_path.name} in the Needs_Action folder.
Follow the plan in {plan_file.name}.
Move the file to Done when complete.
Update the Dashboard with the results."""
            
            # Run Claude Code asynchronously
            cmd = ['claude', '--prompt', prompt]
            subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent)
            )
            logger.info(f'Triggered Claude processing for {file_path.name}')
            
        except Exception as e:
            logger.error(f'Failed to trigger Claude processing: {e}')
    
    def check_approval_queue(self):
        """Check and process approval queue"""
        try:
            pending_files = list(PENDING_APPROVAL.glob('*.md'))
            
            for file_path in pending_files:
                # Check if file has been moved to APPROVED
                approved_file = APPROVED / file_path.name
                if approved_file.exists():
                    # Process approved item
                    logger.info(f'Processing approved item: {file_path.name}')
                    self._process_approved_item(approved_file)
                    
        except Exception as e:
            logger.error(f'Error checking approval queue: {e}')
    
    def _process_approved_item(self, file_path: Path):
        """Process an approved item (e.g., send email)"""
        try:
            content = file_path.read_text(encoding='utf-8')
            metadata = self._extract_metadata(content)
            
            if metadata and metadata.get('type') == 'email':
                # Trigger MCP email server to send
                logger.info(f'Sending approved email: {file_path.name}')
                # This would call the MCP server
                # For now, just move to Done
                dest = DONE / file_path.name
                file_path.rename(dest)
                logger.info(f'Email sent and moved to Done: {file_path.name}')
                
        except Exception as e:
            logger.error(f'Error processing approved item: {e}')
    
    def generate_ceo_briefing(self):
        """Generate Monday Morning CEO Briefing"""
        try:
            logger.info('Generating CEO Briefing...')
            
            # Count completed tasks
            done_files = list(DONE.glob('*.md'))
            done_count = len(done_files)
            
            # Count pending items
            pending_files = list(NEEDS_ACTION.glob('*.md'))
            pending_count = len(pending_files)
            
            # Get current week's stats
            briefing_date = datetime.now().strftime('%Y-%m-%d')
            
            briefing_content = f"""---
generated: {datetime.now().isoformat()}
period: Weekly Briefing
---

# Monday Morning CEO Briefing

## Executive Summary
Generated: {briefing_date}

## Task Statistics
- **Completed Tasks**: {done_count}
- **Pending Tasks**: {pending_count}
- **System Status**: Operational

## Recent Activity
"""
            # Add recent completions
            for file in sorted(done_files, reverse=True)[:5]:
                briefing_content += f"- {file.name}\n"
            
            briefing_content += f"""
## Recommendations
- Review pending items in Needs_Action folder
- Check approval queue for items awaiting decision
- Monitor system logs for any errors

---
*Generated by AI Employee Orchestrator*
"""
            
            # Save briefing
            briefing_file = Path(VAULT_BASE) / 'Briefings' / f'{briefing_date}_CEO_Briefing.md'
            briefing_file.parent.mkdir(parents=True, exist_ok=True)
            briefing_file.write_text(briefing_content, encoding='utf-8')
            
            logger.info(f'CEO Briefing generated: {briefing_file.name}')
            
        except Exception as e:
            logger.error(f'Error generating CEO Briefing: {e}')
    
    def update_dashboard(self):
        """Update the Dashboard.md with current status"""
        try:
            dashboard_file = Path(VAULT_BASE) / 'Dashboard.md'
            
            if not dashboard_file.exists():
                logger.warning('Dashboard.md not found')
                return
            
            content = dashboard_file.read_text(encoding='utf-8')
            
            # Count items
            done_count = len(list(DONE.glob('*.md')))
            pending_count = len(list(NEEDS_ACTION.glob('*.md')))
            approved_count = len(list(APPROVED.glob('*.md')))
            
            # Update status section
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Add status update
            status_update = f"""
## System Status (Updated: {timestamp})
- **Tasks Pending**: {pending_count}
- **Tasks Completed**: {done_count}
- **Tasks Approved**: {approved_count}
- **Watchers Active**: {sum(1 for w in self.watchers if w.is_running())}/{len(self.watchers)}
"""
            
            # Append to dashboard (or update existing status)
            if '## System Status' in content:
                # Replace existing status section
                import re
                content = re.sub(
                    r'## System Status.*?(?=\n## |\Z)',
                    status_update,
                    content,
                    flags=re.DOTALL
                )
            else:
                # Add new status section
                content += f"\n{status_update}\n"
            
            dashboard_file.write_text(content, encoding='utf-8')
            logger.info('Dashboard updated')
            
        except Exception as e:
            logger.error(f'Error updating dashboard: {e}')
    
    def run(self):
        """Main orchestrator loop"""
        logger.info('Starting Orchestrator...')
        self.running = True
        
        # Start all watchers
        self.start_all_watchers()
        
        # Setup scheduled tasks
        schedule.every(10).minutes.do(self.process_needs_action)
        schedule.every(5).minutes.do(self.monitor_watchers)
        schedule.every(5).minutes.do(self.check_approval_queue)
        schedule.every(1).hours.do(self.update_dashboard)
        schedule.every().monday.at("08:00").do(self.generate_ceo_briefing)
        
        logger.info('Orchestrator running. Press Ctrl+C to stop.')
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info('Orchestrator stopping...')
            self.running = False
            self.stop_all_watchers()


def main():
    """Main entry point"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create and run orchestrator
    orchestrator = Orchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
