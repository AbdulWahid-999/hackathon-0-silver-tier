# Ralph Wiggum Loop Implementation

## Overview

The Ralph Wiggum Loop is a stop hook mechanism that intercepts Claude Code exit and feeds the prompt back until task completion. This implementation provides a robust loop system with promise-based completion strategy, file movement detection, and integration with existing workflows.

## Features

### Core Functionality
- **Stop Hook Mechanism**: Intercepts Claude Code exit and prevents premature termination
- **Promise-Based Completion**: Uses `TASK_COMPLETE` promise for task completion detection
- **File Movement Detection**: Monitors file operations to detect task completion
- **Multi-Strategy Detection**: Combines multiple detection strategies for reliability
- **Error Handling**: Comprehensive error handling with recovery mechanisms
- **Iteration Limits**: Configurable maximum iteration limits to prevent infinite loops

### Detection Strategies
1. **Task Complete Promise**: Looks for `TASK_COMPLETE` in logs/output
2. **File Movement**: Detects when files are moved to completion directories
3. **Log Patterns**: Matches common completion patterns in logs
4. **Status Files**: Checks for explicit completion status files
5. **File Watching**: Real-time monitoring of file system changes

## Installation and Usage

### Prerequisites
- Node.js 16+
- npm or yarn
- Claude Code CLI

### Setup
1. Install dependencies:
```bash
npm install
```

2. Configure the system (optional):
```bash
# Edit config.json for email settings
```

### Basic Usage
```javascript
const { RalphWiggumLoop } = require('./ralph-wiggum-loop');

const loop = new RalphWiggumLoop();
await loop.startLoop('Your prompt here', 'working-directory');
```

### Example
```javascript
const TEST_PROMPT = `Implement a comprehensive email workflow system with the following requirements:`;

const loop = new RalphWiggumLoop();
await loop.startLoop(TEST_PROMPT, process.cwd());
```

## Configuration

The loop can be configured through the following parameters:

```javascript
const loop = new RalphWiggumLoop({
    maxIterations: 5,           // Maximum number of iterations
    checkInterval: 5000,        // Check interval in milliseconds
    workingDirectory: process.cwd()  // Working directory
});
```

## Integration with Existing Workflow

### MCP Email Server Integration
The Ralph Wiggum Loop integrates seamlessly with the existing MCP Email Server:

1. **Email Workflow Detection**: Detects when emails are moved to the `Done` folder
2. **Log Monitoring**: Monitors server logs for completion messages
3. **Status Tracking**: Uses the existing metadata system for completion tracking

### File-Based Detection
The loop monitors the following patterns:

- **Email Files**: `EMAIL_*.md` files in the `Needs_Action` folder
- **Completion Markers**: Files containing "complete", "done", or "success"
- **Status Files**: JSON files with completion status
- **Log Files**: Server logs for completion patterns

## API Reference

### RalphWiggumLoop Class

#### Constructor
```javascript
new RalphWiggumLoop(options)
```

**Options:**
- `maxIterations` (Number): Maximum loop iterations (default: 5)
- `checkInterval` (Number): Time between completion checks (default: 5000ms)
- `workingDirectory` (String): Working directory (default: current directory)

#### Methods

- `installExitHook()`: Install the exit hook to intercept Claude Code termination
- `startLoop(prompt, workingDirectory)`: Start the loop with initial prompt
- `executeIteration(prompt)`: Execute a single loop iteration
- `checkTaskCompletion()`: Check if task is complete using all strategies
- `cleanup()`: Clean up resources and create completion markers

#### Detection Methods
- `checkForTaskCompletePromise()`: Look for TASK_COMPLETE promise
- `checkFileMovementCompletion()`: Check for file movement patterns
- `checkLogCompletion()`: Check logs for completion patterns
- `checkStatusCompletion()`: Check status files for completion

## Error Handling

The loop implements comprehensive error handling:

1. **Iteration Error Recovery**: Automatically retries on errors
2. **Exit Hook Safety**: Graceful handling of exit hook failures
3. **File Operation Safety**: Robust file operation error handling
4. **Process Safety**: Safe process spawning and termination

## Testing

### Unit Tests
```bash
# Run the test script
node test_ralph_wiggum.js
```

### Manual Testing
1. Start the MCP Email Server
2. Run the Ralph Wiggum Loop
3. Observe the loop behavior and completion detection

## Troubleshooting

### Common Issues

#### Loop Not Exiting
- Check if task completion detection is working
- Verify that completion markers are being created
- Check log files for completion patterns

#### File Watching Not Working
- Ensure proper permissions for the working directory
- Check if chokidar is properly installed
- Verify that file patterns are correct

#### Process Spawning Issues
- Check Node.js version compatibility
- Verify that Claude Code is installed and accessible
- Check working directory permissions

### Debug Mode
Enable debug logging by setting the environment variable:
```bash
DEBUG=ralph-wiggum node your-script.js
```

## Best Practices

1. **Set Appropriate Iteration Limits**: Prevent infinite loops with reasonable limits
2. **Use Specific Prompts**: Clear, specific prompts help with completion detection
3. **Monitor Logs**: Regularly check log files for debugging
4. **Test Thoroughly**: Test with different scenarios and edge cases
5. **Handle Errors Gracefully**: Implement proper error recovery mechanisms

## Performance Considerations

- **File Watching**: Monitor only necessary directories to reduce overhead
- **Check Intervals**: Adjust check intervals based on task complexity
- **Memory Usage**: Monitor memory usage during long-running tasks
- **Process Management**: Properly clean up child processes

## Security Considerations

- **File Permissions**: Ensure proper file system permissions
- **Process Isolation**: Run in isolated environments when possible
- **Input Validation**: Validate all inputs and prompts
- **Error Logging**: Avoid logging sensitive information

## Future Enhancements

- [ ] Add webhooks for external completion notifications
- [ ] Implement adaptive iteration strategies
- [ ] Add progress tracking and reporting
- [ ] Integrate with CI/CD pipelines
- [ ] Add distributed loop coordination
- [ ] Implement machine learning for completion prediction

## License

This implementation is provided as part of the Silver Tier Functional Assistant project.