# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Bronze Tier implementation of a Personal AI Employee system - an autonomous digital assistant that manages personal and business affairs with 24/7 availability while maintaining security and privacy.

## Architecture

### Core Components
- **Brain**: Claude Code (reasoning engine)
- **Memory**: Obsidian vault (local storage)
- **Sensors**: Watchers (file system monitoring)
- **Hands**: MCP servers (external actions - Gmail, browser automation)

### Workflow System
1. **File Drops**: Files placed in `AI_Employee_Vault/Inbox/`
2. **Detection**: File System Watcher detects new files
3. **Processing**: Creates markdown action items in `Needs_Action/`
4. **Planning**: Claude Code reads action items and creates plans
5. **Execution**: Plans are reviewed and executed
6. **Completion**: Files moved to `Done/`, dashboard updated

## Common Development Tasks

### Installation
```bash
pip install -r requirements.txt
```

### Running the System
```bash
# Start file system watcher
python file_watcher.py

# Start Claude Code integration
claude --cwd AI_Employee_Vault
```

### Testing
1. Drop test files into `AI_Employee_Vault/Inbox/`
2. Verify files appear in `Needs_Action/` as markdown
3. Use Claude Code to read and process action items
4. Check files move to `Done/` and dashboard updates

## Key Files

- `file_watcher.py`: Main file system monitoring script
- `requirements.txt`: Dependencies (watchdog==3.0.0)
- `AI_Employee_Vault/`: Obsidian vault containing all data
- `AI_Employee_Vault/Dashboard.md`: Real-time system status
- `AI_Employee_Vault/Company_Handbook.md`: Rules and guidelines

## Security Protocols

- Local-first architecture (no cloud storage)
- Human-in-the-loop approval for sensitive actions
- Audit logging for all actions
- Credential management through environment variables

## Decision Framework

### Risk Levels
- **Low Risk**: Auto-approve (file operations, internal notes)
- **Medium Risk**: Require review (emails to known contacts)
- **High Risk**: Require explicit approval (payments, new contacts)

## Folder Structure
```
AI_Employee_Vault/
├── Inbox/                    # Drop folder for files
├── Needs_Action/             # Items requiring processing
├── Done/                     # Completed items
├── Plans/                    # Action plans created by AI
├── Pending_Approval/         # Items waiting for human approval
├── Approved/                 # Approved items
└── Rejected/                 # Rejected items
```

## Development Notes

- The system uses watchdog for file system monitoring
- All file operations are logged to `file_watcher.log`
- Plans follow a standardized markdown format in the Plans folder
- Dashboard is updated automatically after task completion
- Company handbook contains all rules and decision frameworks

## Next Steps (Silver Tier)
Implement:
- Gmail Watcher for email processing
- WhatsApp Watcher for messaging
- MCP servers for external actions
- Automated approval workflows
- Scheduling system