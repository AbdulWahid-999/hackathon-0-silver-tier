# Ralph Wiggum Loop Implementation

This document explains the Ralph Wiggum loop implementation for the Silver Tier functional assistant.

## Overview

The Ralph Wiggum loop is a stop hook mechanism that intercepts Claude Code exit and feeds the prompt back until task completion. It implements a promise-based completion strategy with multiple detection methods.

## Key Features

### 1. Stop Hook Mechanism
- Intercepts `process.exit()` calls
- Checks task completion before allowing exit
- Automatically restarts Claude Code if task is incomplete
- Graceful shutdown when task is complete

### 2. Promise-Based Completion Strategy
- `TASK_COMPLETE` promise detection
- File movement detection (e.g., email moved to Done folder)
- Log completion pattern matching
- Status file monitoring

### 3. File System Monitoring
- Real-time file watching using `chokidar`
- Detection of completion markers
- Monitoring of task-specific file patterns
- Automatic task status updates

### 4. Error Handling & Retry
- Configurable retry limits
- Error recovery prompts
- Graceful failure handling
- Max iteration limits to prevent infinite loops

## Integration with MCP Email Server

### Email Task Monitoring
1. **Compose Email**: Starts Ralph Wiggum loop for each composed email
2. **Send Email**: Monitors email movement to Done folder
3. **Approval Workflow**: Tracks approval status changes
4. **File Watching**: Monitors `Needs_Action` and `Done` folders

### Task Detection Strategies
- Email files with `EMAIL_` prefix
- Status changes in email metadata
- Movement between directories
- Completion markers in logs

## Usage Examples

### Basic Usage
```javascript
const { RalphWiggumLoop } = require('./ralph-wiggum-loop');

const ralphWiggum = new RalphWiggumLoop();
ralphWiggum.installExitHook();

// Start loop for a task
await ralphWiggum.startLoop(
    'Create a task completion marker file',
    process.cwd()
);
```

### With Email Server
```javascript
// In MCP Email Server methods
await this.startRalphWiggumLoop(emailId, {
    prompt: `Complete email task: ${emailId}`,
    targetFiles: [`Done/EMAIL_${emailId}.md`],
    maxIterations: 15
});
```

## Configuration Options

### Loop Parameters
- `maxIterations`: Maximum loop iterations (default: 100)
- `checkIntervalMs`: Time between completion checks (default: 5000ms)
- `timeout`: Promise timeout duration (default: 30000ms)

### Detection Strategies
1. **File Pattern Matching**: Glob patterns for target files
2. **Log Analysis**: Search for completion keywords
3. **Status Files**: Monitor specific status files
4. **Directory Changes**: Track file movements

## Testing

### Demonstration Scripts
- `ralph-wiggum-demo.js`: Complete demonstration suite
- `test-ralph-wiggum.js`: Integration tests with email server

### Test Commands
```bash
node ralph-wiggum-demo.js
node test-ralph-wiggum.js
```

## Error Handling

### Automatic Recovery
- Retry mechanism with configurable attempts
- Error-specific recovery prompts
- Graceful degradation on persistent failures

### Monitoring
- Real-time error logging
- Performance metrics
- Task completion statistics

## Best Practices

1. **Task Isolation**: Each task should have unique identifiers
2. **Clear Completion Criteria**: Define specific file patterns or markers
3. **Resource Management**: Clean up temporary files and markers
4. **Monitoring**: Use multiple detection strategies for reliability
5. **Error Recovery**: Implement specific recovery procedures for common failures

## File Structure

```
Silver-Tier/
├── ralph-wiggum-loop.js        # Core implementation
├── ralph-wiggum-demo.js        # Demonstration suite
├── test-ralph-wiggum.js        # Integration tests
└── README-RALPH-WIGGUM.md      # This documentation
```

## Integration Points

### MCP Server Methods
- `composeEmail()`: Starts loop for composed emails
- `sendEmail()`: Monitors email sending completion
- `getApprovalStatus()`: Tracks approval workflow
- `listPendingEmails()`: Monitors pending tasks

### File System Hooks
- `setupFileWatcher()`: Real-time file monitoring
- `checkTaskCompletion()`: Multiple completion strategies
- `createTaskCompletionMarker()`: Completion tracking

## Monitoring & Debugging

### Statistics
- Total tasks processed
- Pending vs completed tasks
- Iteration counts
- Error rates

### Logging
- Detailed task progress
- Completion detection events
- Error conditions and recoveries

This implementation provides robust task completion monitoring for the Silver Tier functional assistant, ensuring tasks are properly completed before allowing system exit.