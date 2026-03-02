# AI Agent Skills Documentation

## Overview

This document describes all AI Agent Skills implemented in the Silver Tier Functional Assistant. These skills enable Claude Code to autonomously manage personal and business affairs.

## Skill Categories

### 1. Perception Skills (Watchers)

#### FILE_WATCHER
**Purpose**: Monitor filesystem for new files requiring processing

**Trigger**: New file created in `Inbox/` folder

**Action**: Creates action file in `Needs_Action/` with metadata

**Configuration**:
```python
VAULT_PATH = r"C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault"
WATCH_FOLDER = VAULT_PATH / 'Inbox'
CHECK_INTERVAL = 1 second (continuous)
```

**Output Format**:
```markdown
---
{
  "type": "file_drop",
  "original_name": "filename.txt",
  "size": 1024,
  "status": "pending",
  "priority": "medium"
}
---

# File Drop Detected
## File Information
- **Name**: filename.txt
- **Size**: 1.0 KB
- **Type**: .txt

## Suggested Actions
- [ ] Analyze file content
- [ ] Categorize appropriately
- [ ] Process according to file type
```

---

#### GMAIL_WATCHER
**Purpose**: Monitor Gmail for unread/important emails

**Trigger**: New email matching criteria (unread, important, newer than 1 day)

**Action**: Creates action file in `Needs_Action/` with email details

**Configuration**:
```python
CHECK_INTERVAL = 120 seconds
QUERY = 'newer_than:1d is:unread OR is:important'
MAX_RESULTS = 50
```

**Prerequisites**:
- Gmail API credentials (`gmail_credentials.json`)
- OAuth2 token (`token.json`)

**Output Format**:
```markdown
---
{
  "type": "email",
  "id": "email_gmail_id",
  "from": "sender@example.com",
  "subject": "Email Subject",
  "priority": "high",
  "status": "pending"
}
---

# New Email Received
## Email Information
- **From**: sender@example.com
- **Subject**: Email Subject
- **Priority**: High

## Suggested Actions
- [ ] Read full email content
- [ ] Respond to sender if necessary
- [ ] Archive after processing
```

---

#### LINKEDIN_WATCHER
**Purpose**: Monitor LinkedIn for messages, connections, and business opportunities

**Trigger**: New messages, connection requests, or scheduled post time

**Actions**:
- Auto-accept connection requests (configurable)
- Auto-respond to messages (configurable)
- Generate and post business content
- Create action files for all activities

**Configuration**:
```python
CHECK_INTERVAL = 3600 seconds (1 hour)
AUTO_ACCEPT_CONNECTIONS = true
AUTO_RESPOND_MESSAGES = true
AUTO_POST_CONTENT = true
POST_FREQUENCY_HOURS = 8
MAX_POSTS_PER_DAY = 3
```

**Business Content Templates**:
```
"Check out our latest {product}! {description}"
"Exciting news! We're launching {product}. {details}"
"{product} is now available! Transform your {industry} business with {benefit}"
```

---

### 2. Reasoning Skills (Claude Code)

#### CREATE_PLAN
**Purpose**: Create processing plan for items in Needs_Action

**Trigger**: Orchestrator detects new item in Needs_Action

**Input**: Action file metadata

**Output**: Plan file in `Plans/` folder

**Plan Structure**:
```markdown
---
file_id: item_name
plan_type: email|file_drop|linkedin_message
priority: high|medium|low
created: 2026-02-24T10:00:00
status: pending
---

# Processing Plan for {item_name}

## Item Analysis
- **Type**: {type}
- **Priority**: {priority}

## Processing Steps
### Step 1: Review
- [ ] Review item content
- [ ] Determine required actions
- [ ] Check if approval needed

### Step 2: Action
- [ ] Execute required actions
- [ ] Update status

### Step 3: Completion
- [ ] Move to Done folder
- [ ] Update Dashboard
```

---

#### ANALYZE_AND_CATEGORIZE
**Purpose**: Analyze content and determine appropriate category

**Input**: File content or email body

**Categories**:
- `client_communication`: Client emails/messages
- `internal`: Internal notes
- `financial`: Invoices, payments
- `social`: Social media interactions
- `system`: System files/logs

**Decision Rules**:
```python
if 'invoice' in content or 'payment' in content:
    category = 'financial'
elif 'client' in sender_domain:
    category = 'client_communication'
elif from_address in known_contacts:
    category = 'internal'
```

---

#### GENERATE_RESPONSE
**Purpose**: Generate appropriate response to communications

**Input**: Original message, context, tone guidelines

**Output**: Draft response

**Response Templates**:

**Email Response**:
```
Dear {name},

Thank you for your message regarding {topic}.

{response_body}

Best regards,
{company}
```

**LinkedIn Message**:
```
Thanks for reaching out! I'm excited to explore how we can work together.
```

---

### 3. Action Skills (MCP Servers)

#### COMPOSE_EMAIL
**Purpose**: Compose email with proper formatting and metadata

**Input**:
```json
{
  "recipients": "to@example.com",
  "subject": "Email Subject",
  "body": "Email body content",
  "priority": "medium",
  "category": "general"
}
```

**Output**: Email file in `Needs_Action/` or `Pending_Approval/`

**MCP Method**: `compose-email`

---

#### SEND_EMAIL
**Purpose**: Send email via SMTP

**Input**: Email ID or file path

**Process**:
1. Extract email metadata
2. Check approval status
3. Send via SMTP
4. Move to Done folder
5. Log action

**MCP Method**: `send-email`

**Approval Required**:
- New contacts (not in known_contacts)
- Bulk sends (>10 recipients)
- Contains attachments

---

#### MOVE_FILE
**Purpose**: Move files between vault folders

**Input**: Source path, destination path

**Destinations**:
- `Needs_Action/` → `Done/` (completed)
- `Needs_Action/` → `Pending_Approval/` (needs review)
- `Pending_Approval/` → `Approved/` (human approved)
- `Pending_Approval/` → `Rejected/` (human rejected)

---

#### UPDATE_DASHBOARD
**Purpose**: Update Dashboard.md with current status

**Triggers**:
- Task completion
- Scheduled intervals (hourly)
- CEO Briefing generation

**Updates**:
- Task counts
- Recent activity log
- System health status

---

### 4. Approval Workflow Skills

#### REQUEST_APPROVAL
**Purpose**: Create approval request for sensitive actions

**Thresholds**:
```python
PAYMENT_THRESHOLD = 50.00  # Auto-approve under $50
EMAIL_KNOWN_CONTACT = True  # Auto-approve to known contacts
FILE_OPERATIONS = True  # Auto-approve file moves
```

**Approval Request Format**:
```markdown
---
{
  "request_id": "APPROVAL_20260224_100000",
  "action_type": "email|payment|social_post",
  "description": "Send newsletter to subscribers",
  "priority": "medium",
  "created_at": "2026-02-24T10:00:00",
  "expires_at": "2026-02-25T10:00:00",
  "metadata": {...}
}
---

# Approval Request

## Instructions
- **To Approve**: Move to `/Approved` folder
- **To Reject**: Move to `/Rejected` folder

## Action Details
{action_specific_details}
```

---

#### PROCESS_APPROVAL_QUEUE
**Purpose**: Process approved items from Approved folder

**Triggers**: File appears in `Approved/`

**Actions by Type**:
- **Email**: Send via MCP, move to Done
- **Payment**: Process payment, move to Done
- **Social Post**: Publish to platform, move to Done

**Audit Logging**: All actions logged to `Logs/approval_YYYY-MM-DD.json`

---

### 5. Scheduling Skills

#### GENERATE_CEO_BRIEFING
**Purpose**: Generate Monday Morning CEO Briefing

**Schedule**: Every Monday at 8:00 AM

**Content**:
- Task statistics (completed, pending)
- Revenue summary (if accounting integrated)
- Bottlenecks identified
- Proactive suggestions
- System health check

**Output**: `Briefings/YYYY-MM-DD_CEO_Briefing.md`

---

#### GENERATE_DAILY_SUMMARY
**Purpose**: Generate daily activity summary

**Schedule**: Every day at 6:00 PM

**Content**:
- Today's completions
- Pending items count
- Brief analysis

**Output**: `Logs/YYYY-MM-DD_Daily_Summary.md`

---

#### CLEANUP_OLD_FILES
**Purpose**: Archive or delete old files

**Schedule**: Every Sunday at 2:00 AM

**Retention**:
- Logs: 30 days
- Done: 90 days
- Briefings: 365 days

---

### 6. Ralph Wiggum Loop (Persistence)

#### START_LOOP
**Purpose**: Keep Claude Code working until task completion

**Configuration**:
```json
{
  "maxIterations": 5,
  "checkIntervalMs": 5000,
  "taskCompletePromise": "TASK_COMPLETE",
  "doneFolderPath": "AI_Silver_Employee_Vault/Done"
}
```

**Completion Detection**:
1. File movement to Done folder
2. TASK_COMPLETE marker in logs
3. Status file updates
4. Completion pattern matching

---

#### CHECK_COMPLETION
**Purpose**: Verify task completion before allowing exit

**Strategies**:
- File pattern matching
- Log analysis
- Status file monitoring
- Directory change detection

---

## Skill Integration Examples

### Example 1: Email Processing Flow

```
1. GMAIL_WATCHER detects new email
   ↓
2. Creates EMAIL_*.md in Needs_Action/
   ↓
3. ORCHESTRATOR triggers CREATE_PLAN
   ↓
4. Creates plan_*.md in Plans/
   ↓
5. ANALYZE_AND_CATEGORIZE determines response needed
   ↓
6. GENERATE_RESPONSE creates draft
   ↓
7. REQUEST_APPROVAL (if new contact)
   ↓
8. Human moves to Approved/
   ↓
9. PROCESS_APPROVAL_QUEUE sends email
   ↓
10. MOVE_FILE to Done/
   ↓
11. UPDATE_DASHBOARD
```

### Example 2: LinkedIn Auto-Posting

```
1. SCHEDULER triggers (every 8 hours)
   ↓
2. LINKEDIN_WATCHER generates business content
   ↓
3. ANALYZE_AND_CATEGORIZE selects template
   ↓
4. GENERATE_RESPONSE creates post content
   ↓
5. REQUEST_APPROVAL (if first time)
   ↓
6. Human approves or auto-approve enabled
   ↓
7. Post to LinkedIn via Selenium/Playwright
   ↓
8. CREATE_ACTION_FILE in Needs_Action/
   ↓
9. UPDATE_DASHBOARD
```

---

## Configuration Reference

### Environment Variables (.env)
```bash
# Email
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# LinkedIn
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password

# Vault
VAULT_PATH=C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault

# Ralph Wiggum
RALPH_MAX_ITERATIONS=5
RALPH_CHECK_INTERVAL_MS=5000
```

### Auto-Approve Thresholds (approval_workflow.py)
```python
auto_approve_thresholds = {
    'payment': 50.0,
    'email_known_contact': True,
    'file_operation': True,
}
```

### Watcher Intervals (orchestrator.py)
```python
FILE_WATCHER_INTERVAL = 'continuous'
GMAIL_WATCHER_INTERVAL = 120  # seconds
LINKEDIN_WATCHER_INTERVAL = 3600  # seconds
```

---

## Monitoring and Debugging

### Log Files
- `file_watcher.log` - File system monitoring
- `gmail_watcher.log` - Gmail API operations
- `linkedin_watcher.log` - LinkedIn automation
- `orchestrator.log` - Coordination events
- `approval_workflow.log` - Approval actions
- `scheduler.log` - Scheduled tasks
- `mcp-email-server.log` - Email operations

### Key Metrics
- Tasks pending in Needs_Action/
- Tasks completed (Done/ count)
- Approval queue size
- Average processing time
- Error rate

### Health Checks
```bash
# Check watchers running
tasklist | findstr python

# Check MCP server
netstat -an | findstr 8080

# Check recent logs
tail -f orchestrator.log
```

---

## Extending Agent Skills

### Adding New Watcher
1. Create `new_watcher.py` following BaseWatcher pattern
2. Implement `check_for_updates()` and `create_action_file()`
3. Add to orchestrator.py watcher list
4. Update this documentation

### Adding New MCP Tool
1. Add handler in `mcp-email-server.js`
2. Implement tool logic
3. Update client if needed
4. Document in Agent Skills

### Adding New Approval Type
1. Add to `ApprovalRequest` dataclass
2. Implement `_process_approved_*` method
3. Update approval request template
4. Configure auto-approve thresholds

---

*Last Updated: 2026-02-24*
*Version: 1.0 (Silver Tier)*
