"""
Human-in-the-Loop (HITL) Approval Workflow
Manages approval requests for sensitive actions

This module handles:
1. Creating approval requests for sensitive actions
2. Monitoring approval queue (Pending_Approval folder)
3. Processing approved/rejected items
4. Audit logging for all approval actions
"""

import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('approval_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ApprovalWorkflow')

# Vault paths
VAULT_BASE = r"C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault"
NEEDS_ACTION = Path(VAULT_BASE) / 'Needs_Action'
PENDING_APPROVAL = Path(VAULT_BASE) / 'Pending_Approval'
APPROVED = Path(VAULT_BASE) / 'Approved'
REJECTED = Path(VAULT_BASE) / 'Rejected'
DONE = Path(VAULT_BASE) / 'Done'
LOGS = Path(VAULT_BASE) / 'Logs'

# Ensure directories exist
for directory in [PENDING_APPROVAL, APPROVED, REJECTED, LOGS]:
    directory.mkdir(parents=True, exist_ok=True)


@dataclass
class ApprovalRequest:
    """Represents an approval request"""
    request_id: str
    action_type: str
    description: str
    priority: str
    created_at: str
    expires_at: str
    metadata: Dict[str, Any]
    status: str = 'pending'
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None


class ApprovalWorkflow:
    """Manages human-in-the-loop approval workflow"""
    
    def __init__(self):
        self.auto_approve_thresholds = {
            'payment': 50.0,  # Auto-approve payments under $50
            'email_known_contact': True,  # Auto-approve emails to known contacts
            'file_operation': True,  # Auto-approve file operations
        }
        self.known_contacts = self._load_known_contacts()
    
    def _load_known_contacts(self) -> set:
        """Load known contacts from configuration"""
        # In production, this would load from a config file or database
        return {
            'example@gmail.com',
            'colleague@company.com',
        }
    
    def create_approval_request(
        self,
        action_type: str,
        description: str,
        metadata: Dict[str, Any],
        priority: str = 'medium',
        expires_in_hours: int = 24
    ) -> Optional[Path]:
        """
        Create an approval request file
        
        Args:
            action_type: Type of action (email, payment, social_post, etc.)
            description: Human-readable description
            metadata: Action-specific metadata
            priority: low, medium, high, urgent
            expires_in_hours: When the request expires
            
        Returns:
            Path to the approval request file, or None if auto-approved
        """
        # Check if auto-approve applies
        if self._should_auto_approve(action_type, metadata):
            logger.info(f'Auto-approved: {action_type} - {description}')
            return None
        
        # Create approval request
        request_id = f"APPROVAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        now = datetime.now()
        
        request = ApprovalRequest(
            request_id=request_id,
            action_type=action_type,
            description=description,
            priority=priority,
            created_at=now.isoformat(),
            expires_at=(now.replace(hour=now.hour + expires_in_hours)).isoformat(),
            metadata=metadata,
            status='pending'
        )
        
        # Create approval request file
        file_path = PENDING_APPROVAL / f'{request_id}.md'
        content = self._format_approval_request(request)
        file_path.write_text(content, encoding='utf-8')
        
        logger.info(f'Created approval request: {file_path.name}')
        self._log_approval_event('created', request)
        
        return file_path
    
    def _should_auto_approve(self, action_type: str, metadata: Dict[str, Any]) -> bool:
        """Determine if action should be auto-approved"""
        
        # Payment auto-approval
        if action_type == 'payment':
            amount = metadata.get('amount', float('inf'))
            if amount < self.auto_approve_thresholds['payment']:
                return True
        
        # Email to known contact
        if action_type == 'email':
            recipients = metadata.get('recipients', [])
            if isinstance(recipients, str):
                recipients = [recipients]
            
            all_known = all(
                recipient in self.known_contacts 
                for recipient in recipients
            )
            if all_known and self.auto_approve_thresholds['email_known_contact']:
                return True
        
        # File operations
        if action_type in ['file_move', 'file_delete', 'file_copy']:
            return self.auto_approve_thresholds['file_operation']
        
        return False
    
    def _format_approval_request(self, request: ApprovalRequest) -> str:
        """Format approval request as markdown file"""
        metadata_json = json.dumps(request.metadata, indent=2)
        
        return f"""---
{{
  "request_id": "{request.request_id}",
  "action_type": "{request.action_type}",
  "description": "{request.description}",
  "priority": "{request.priority}",
  "created_at": "{request.created_at}",
  "expires_at": "{request.expires_at}",
  "status": "{request.status}",
  "metadata": {metadata_json}
}}
---

# Approval Request

## Request Details
- **Request ID**: {request.request_id}
- **Action Type**: {request.action_type}
- **Priority**: {request.priority.capitalize()}
- **Created**: {request.created_at}
- **Expires**: {request.expires_at}

## Description
{request.description}

## Action Details
{self._format_action_details(request.action_type, request.metadata)}

## Instructions

### To Approve
Move this file to the `/Approved` folder

### To Reject
Move this file to the `/Rejected` folder with a note explaining why

### To Request More Information
Add a comment to this file with your questions

## Review Section
<!-- This section will be filled when reviewed -->
- **Reviewed By**: _Pending_
- **Reviewed At**: _Pending_
- **Review Notes**: _Pending_
"""
    
    def _format_action_details(self, action_type: str, metadata: Dict[str, Any]) -> str:
        """Format action-specific details"""
        if action_type == 'email':
            return f"""
- **To**: {metadata.get('recipients', 'Unknown')}
- **Subject**: {metadata.get('subject', 'No subject')}
- **Body Preview**: {metadata.get('body', '')[:200]}...
"""
        elif action_type == 'payment':
            return f"""
- **Amount**: ${metadata.get('amount', 0):.2f}
- **Recipient**: {metadata.get('recipient', 'Unknown')}
- **Reason**: {metadata.get('reason', 'No reason provided')}
- **Reference**: {metadata.get('reference', 'N/A')}
"""
        elif action_type == 'social_post':
            return f"""
- **Platform**: {metadata.get('platform', 'Unknown')}
- **Content**: {metadata.get('content', '')[:200]}...
- **Scheduled Time**: {metadata.get('scheduled_time', 'Immediate')}
"""
        else:
            return f"""
- **Details**: {json.dumps(metadata, indent=2)}
"""
    
    def process_approved_queue(self) -> List[Dict[str, Any]]:
        """
        Process items in the Approved queue
        
        Returns:
            List of processed items with results
        """
        results = []
        approved_files = list(APPROVED.glob('*.md'))
        
        for file_path in approved_files:
            try:
                result = self._process_approved_item(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f'Error processing {file_path.name}: {e}')
                results.append({
                    'file': str(file_path),
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def _process_approved_item(self, file_path: Path) -> Dict[str, Any]:
        """Process a single approved item"""
        content = file_path.read_text(encoding='utf-8')
        metadata = self._extract_metadata(content)
        
        if not metadata:
            return {'file': str(file_path), 'status': 'error', 'error': 'Invalid metadata'}
        
        action_type = metadata.get('action_type', 'unknown')
        request_id = metadata.get('request_id', 'unknown')
        
        logger.info(f'Processing approved {action_type}: {request_id}')
        
        # Process based on action type
        if action_type == 'email':
            result = self._process_approved_email(file_path, metadata)
        elif action_type == 'payment':
            result = self._process_approved_payment(file_path, metadata)
        elif action_type == 'social_post':
            result = self._process_approved_social_post(file_path, metadata)
        else:
            result = self._process_generic_approved_item(file_path, metadata)
        
        # Update status
        result['processed_at'] = datetime.now().isoformat()
        self._log_approval_event('processed', metadata, result)
        
        return result
    
    def _process_approved_email(self, file_path: Path, metadata: Dict) -> Dict[str, Any]:
        """Process approved email - trigger MCP email server"""
        try:
            # In production, this would call the MCP email server
            # For now, simulate sending
            logger.info(f'Sending email to {metadata.get("metadata", {}).get("recipients")}')
            
            # Move to Done
            dest = DONE / file_path.name
            shutil.move(str(file_path), str(dest))
            
            return {
                'file': str(file_path),
                'action_type': 'email',
                'status': 'sent',
                'destination': str(dest)
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'action_type': 'email',
                'status': 'error',
                'error': str(e)
            }
    
    def _process_approved_payment(self, file_path: Path, metadata: Dict) -> Dict[str, Any]:
        """Process approved payment - trigger payment gateway"""
        try:
            # In production, this would call payment API
            amount = metadata.get('metadata', {}).get('amount', 0)
            recipient = metadata.get('metadata', {}).get('recipient', 'Unknown')
            
            logger.info(f'Processing payment of ${amount:.2f} to {recipient}')
            
            # Move to Done
            dest = DONE / file_path.name
            shutil.move(str(file_path), str(dest))
            
            return {
                'file': str(file_path),
                'action_type': 'payment',
                'status': 'processed',
                'amount': amount,
                'recipient': recipient
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'action_type': 'payment',
                'status': 'error',
                'error': str(e)
            }
    
    def _process_approved_social_post(self, file_path: Path, metadata: Dict) -> Dict[str, Any]:
        """Process approved social media post"""
        try:
            platform = metadata.get('metadata', {}).get('platform', 'Unknown')
            content = metadata.get('metadata', {}).get('content', '')[:50]
            
            logger.info(f'Posting to {platform}: {content}...')
            
            # Move to Done
            dest = DONE / file_path.name
            shutil.move(str(file_path), str(dest))
            
            return {
                'file': str(file_path),
                'action_type': 'social_post',
                'status': 'posted',
                'platform': platform
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'action_type': 'social_post',
                'status': 'error',
                'error': str(e)
            }
    
    def _process_generic_approved_item(self, file_path: Path, metadata: Dict) -> Dict[str, Any]:
        """Process generic approved item"""
        try:
            # Move to Done
            dest = DONE / file_path.name
            shutil.move(str(file_path), str(dest))
            
            return {
                'file': str(file_path),
                'action_type': metadata.get('action_type', 'unknown'),
                'status': 'completed',
                'destination': str(dest)
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'status': 'error',
                'error': str(e)
            }
    
    def process_rejected_queue(self) -> List[Dict[str, Any]]:
        """Process items in the Rejected queue"""
        results = []
        rejected_files = list(REJECTED.glob('*.md'))
        
        for file_path in rejected_files:
            try:
                # Log rejection and archive
                content = file_path.read_text(encoding='utf-8')
                metadata = self._extract_metadata(content)
                
                logger.info(f'Rejected: {metadata.get("action_type", "unknown")} - {file_path.name}')
                
                # Move to Logs/Rejected archive
                archive_dir = LOGS / 'Rejected'
                archive_dir.mkdir(parents=True, exist_ok=True)
                dest = archive_dir / file_path.name
                shutil.move(str(file_path), str(dest))
                
                results.append({
                    'file': str(file_path),
                    'status': 'archived',
                    'destination': str(dest)
                })
                
            except Exception as e:
                results.append({
                    'file': str(file_path),
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def check_expired_requests(self) -> List[str]:
        """Check for expired approval requests"""
        expired = []
        pending_files = list(PENDING_APPROVAL.glob('*.md'))
        now = datetime.now()
        
        for file_path in pending_files:
            content = file_path.read_text(encoding='utf-8')
            metadata = self._extract_metadata(content)
            
            if metadata:
                expires_at = metadata.get('expires_at')
                if expires_at:
                    try:
                        expiry = datetime.fromisoformat(expires_at)
                        if expiry < now:
                            logger.warning(f'Expired approval request: {file_path.name}')
                            expired.append(str(file_path))
                            
                            # Move to Rejected with note
                            self._reject_expired_request(file_path)
                            
                    except ValueError:
                        pass
        
        return expired
    
    def _reject_expired_request(self, file_path: Path):
        """Move expired request to Rejected with note"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Add expiry note
            updated_content = content.replace(
                '## Review Section',
                f'## Expiry Notice\n\nThis request expired at {datetime.now().isoformat()} and was automatically rejected.\n\n## Review Section'
            )
            
            # Write updated content
            file_path.write_text(updated_content, encoding='utf-8')
            
            # Move to Rejected
            dest = REJECTED / file_path.name
            shutil.move(str(file_path), str(dest))
            
            self._log_approval_event('expired', {'file': str(file_path)})
            
        except Exception as e:
            logger.error(f'Error rejecting expired request: {e}')
    
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
    
    def _log_approval_event(self, event_type: str, data: Dict, result: Dict = None):
        """Log approval event for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data,
            'result': result
        }
        
        # Append to daily log
        log_file = LOGS / f'approval_{datetime.now().strftime("%Y-%m-%d")}.json'
        
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')
    
    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get list of pending approval requests"""
        requests = []
        pending_files = list(PENDING_APPROVAL.glob('*.md'))
        
        for file_path in pending_files:
            content = file_path.read_text(encoding='utf-8')
            metadata = self._extract_metadata(content)
            
            if metadata:
                requests.append({
                    'file': str(file_path),
                    'request_id': metadata.get('request_id'),
                    'action_type': metadata.get('action_type'),
                    'description': metadata.get('description'),
                    'priority': metadata.get('priority'),
                    'created_at': metadata.get('created_at'),
                    'expires_at': metadata.get('expires_at')
                })
        
        # Sort by priority and creation time
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        requests.sort(key=lambda x: (
            priority_order.get(x.get('priority', 'medium'), 2),
            x.get('created_at', '')
        ))
        
        return requests
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get approval workflow statistics"""
        return {
            'pending': len(list(PENDING_APPROVAL.glob('*.md'))),
            'approved_today': len([
                f for f in APPROVED.glob('*.md')
                if self._is_today(f)
            ]),
            'rejected_today': len([
                f for f in REJECTED.glob('*.md')
                if self._is_today(f)
            ]),
            'processed': len(list(DONE.glob('APPROVAL_*.md')))
        }
    
    def _is_today(self, file_path: Path) -> bool:
        """Check if file was modified today"""
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            return mtime.date() == datetime.now().date()
        except Exception:
            return False


# Singleton instance
_workflow_instance: Optional[ApprovalWorkflow] = None


def get_approval_workflow() -> ApprovalWorkflow:
    """Get singleton approval workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = ApprovalWorkflow()
    return _workflow_instance


# Convenience functions
def request_approval(
    action_type: str,
    description: str,
    metadata: Dict[str, Any],
    priority: str = 'medium'
) -> Optional[Path]:
    """Request approval for an action"""
    return get_approval_workflow().create_approval_request(
        action_type, description, metadata, priority
    )


def process_approval_queue() -> List[Dict[str, Any]]:
    """Process the approved queue"""
    return get_approval_workflow().process_approved_queue()


def get_pending_approvals() -> List[Dict[str, Any]]:
    """Get pending approval requests"""
    return get_approval_workflow().get_pending_requests()


if __name__ == "__main__":
    # Test the approval workflow
    workflow = ApprovalWorkflow()
    
    print("Approval Workflow Test")
    print("=" * 50)
    
    # Test creating approval request
    result = workflow.create_approval_request(
        action_type='email',
        description='Send newsletter to subscribers',
        metadata={
            'recipients': ['subscriber@example.com'],
            'subject': 'Monthly Newsletter',
            'body': 'Here is our monthly update...'
        },
        priority='medium'
    )
    
    if result:
        print(f"Created approval request: {result}")
    else:
        print("Action was auto-approved")
    
    # Test getting pending requests
    pending = workflow.get_pending_requests()
    print(f"\nPending requests: {len(pending)}")
    
    # Test statistics
    stats = workflow.get_statistics()
    print(f"\nStatistics: {stats}")
