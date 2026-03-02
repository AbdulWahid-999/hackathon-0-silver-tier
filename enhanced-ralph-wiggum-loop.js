// Enhanced Ralph Wiggum Loop for Silver Tier Functional Assistant
// Implements stop hook mechanism with promise-based completion strategy and file movement detection
// Integrates with existing workflow and includes robust error handling and max iteration limits

const fs = require('fs').promises;
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const { spawn } = require('child_process');
const chokidar = require('chokidar');

// Configuration
const TASK_COMPLETE_PROMISE = 'TASK_COMPLETE';
const DEFAULT_MAX_ITERATIONS = 10;
const DEFAULT_CHECK_INTERVAL_MS = 3000; // 3 seconds

// Enhanced Ralph Wiggum Loop with improved integration
class EnhancedRalphWiggumLoop {
    constructor(options = {}) {
        // Configuration options with defaults
        this.maxIterations = options.maxIterations || DEFAULT_MAX_ITERATIONS;
        this.checkIntervalMs = options.checkIntervalMs || DEFAULT_CHECK_INTERVAL_MS;
        this.workingDirectory = options.workingDirectory || process.cwd();
        this.logFilePath = options.logFilePath || 'silver_assistant.log';
        this.taskCompletePromise = options.taskCompletePromise || TASK_COMPLETE_PROMISE;
        this.completionStrategies = options.completionStrategies || [
            'promise_file',
            'file_movement',
            'log_patterns'
        ];

        // Internal state
        this.iteration = 0;
        this.taskCompleted = false;
        this.exitHookInstalled = false;
        this.watcher = null;
        this.taskContext = null;
        this.completionLogPatterns = [
            'Task completed',
            'All tests completed',
            'Email sent successfully',
            'Process finished',
            'Operation successful',
            'Successfully completed',
            'TASK_COMPLETE'
        ];
        this.fileWatchPatterns = [
            'EMAIL_*.md',
            '*complete*',
            '*done*',
            '*success*',
            '*.complete',
            '*.done'
        ];
        this.lastFileState = {};
    }

    // Install the exit hook that intercepts Claude Code exit
    installExitHook() {
        if (this.exitHookInstalled) {
            return;
        }

        // Save original process exit
        const originalExit = process.exit;

        // Override process.exit to intercept termination
        process.exit = (code = 0) => {
            console.log('\n🎭 Ralph Wiggum Loop Activated: Task not yet complete!');
            console.log('⏳ Checking for task completion...');

            // Check if task is complete
            this.checkTaskCompletion()
                .then((completed) => {
                    if (completed) {
                        console.log('\n✅ Task completed! Exiting gracefully...');
                        originalExit.call(process, code);
                    } else {
                        // Feed prompt back and restart
                        console.log('\n🔄 Feeding prompt back into the loop...');
                        this.restartClaudeCode();
                    }
                })
                .catch((error) => {
                    console.error('\n❌ Error checking task completion:', error);
                    console.log('\n🔄 Feeding prompt back into the loop...');
                    this.restartClaudeCode();
                });
        };

        this.exitHookInstalled = true;
        console.log('✅ Enhanced Ralph Wiggum exit hook installed');
    }

    // Start the loop with initial prompt
    async startLoop(initialPrompt, context = {}) {
        this.iteration = 0;
        this.taskCompleted = false;
        this.taskContext = context;

        console.log('\n🚀 Enhanced Ralph Wiggum Loop Started');
        console.log(`📁 Working Directory: ${this.workingDirectory}`);
        console.log(`📝 Initial Prompt: ${initialPrompt.substring(0, 100)}...`);
        console.log(`🔄 Max Iterations: ${this.maxIterations}`);
        console.log(`🔍 Completion Strategies: ${this.completionStrategies.join(', ')}`);

        // Install exit hook
        this.installExitHook();

        // Set up file watcher for task completion detection
        this.setupFileWatcher();

        // Start first iteration
        await this.executeIteration(initialPrompt);
    }

    // Execute a single iteration of the loop
    async executeIteration(prompt) {
        this.iteration++;
        console.log(`\n🔄 Iteration ${this.iteration}/${this.maxIterations}`);
        console.log(`📝 Prompt: ${prompt.substring(0, 100)}...`);

        try {
            // Create task start marker
            await this.createTaskMarker(prompt, 'in_progress');

            // Spawn Claude Code with the prompt
            const result = await this.spawnClaudeCode(prompt);

            console.log('✅ Claude Code execution completed');
            console.log('📋 Result:', result.substring(0, 200), '...');

            // Check if task is complete
            const completed = await this.checkTaskCompletion();

            if (completed) {
                console.log('\n✅ Task completed successfully!');
                this.taskCompleted = true;
                await this.createTaskMarker(prompt, 'complete');
                await this.cleanup();
                return;
            } else {
                console.log('⚠️  Task not yet complete, continuing loop...');

                // Prepare next prompt with context
                const nextPrompt = this.generateNextPrompt(prompt, result);

                // Continue loop if max iterations not reached
                if (this.iteration < this.maxIterations) {
                    await this.executeIteration(nextPrompt);
                } else {
                    console.log('❌ Max iterations reached. Task may not be complete.');
                    await this.createTaskMarker(prompt, 'incomplete');
                    await this.cleanup();
                }
            }

        } catch (error) {
            console.error('\n❌ Error in iteration:', error.message);
            console.error('Stack trace:', error.stack);

            // Log error
            await this.logError(error, prompt);

            // Continue loop on error unless max iterations reached
            if (this.iteration < this.maxIterations) {
                const nextPrompt = this.generateErrorRecoveryPrompt(prompt, error);
                await this.executeIteration(nextPrompt);
            } else {
                console.log('❌ Max iterations reached due to errors.');
                await this.createTaskMarker(prompt, 'error');
                await this.cleanup();
            }
        }
    }

    // Spawn Claude Code process with the given prompt
    async spawnClaudeCode(prompt) {
        return new Promise((resolve, reject) => {
            const claudeCode = spawn('claude', ['code', '--prompt', prompt], {
                cwd: this.workingDirectory,
                stdio: 'pipe',
                shell: true,
                env: { ...process.env, NODE_OPTIONS: '--max-old-space-size=4096' }
            });

            let output = '';
            let errorOutput = '';

            claudeCode.stdout.on('data', (data) => {
                output += data.toString();
                process.stdout.write(data.toString());
            });

            claudeCode.stderr.on('data', (data) => {
                errorOutput += data.toString();
                process.stderr.write(data.toString());
            });

            claudeCode.on('close', (code) => {
                if (code === 0) {
                    resolve(output.trim());
                } else {
                    reject(new Error(`Claude Code exited with code ${code}: ${errorOutput.trim()}`));
                }
            });

            claudeCode.on('error', (error) => {
                reject(error);
            });
        });
    }

    // Check if task is complete using multiple strategies
    async checkTaskCompletion() {
        try {
            // Strategy 1: Check for TASK_COMPLETE promise
            if (this.completionStrategies.includes('promise_file')) {
                const promiseComplete = await this.checkForTaskCompletePromise();
                if (promiseComplete) return true;
            }

            // Strategy 2: Check for file movement/deletion patterns
            if (this.completionStrategies.includes('file_movement')) {
                const fileMovementComplete = await this.checkFileMovementCompletion();
                if (fileMovementComplete) return true;
            }

            // Strategy 3: Check for completion markers in logs
            if (this.completionStrategies.includes('log_patterns')) {
                const logComplete = await this.checkLogCompletion();
                if (logComplete) return true;
            }

            // Strategy 4: Check for status completion in files
            if (this.completionStrategies.includes('status_files')) {
                const statusComplete = await this.checkStatusCompletion();
                if (statusComplete) return true;
            }

            return false;

        } catch (error) {
            console.error('❌ Error checking task completion:', error);
            return false;
        }
    }

    // Check for TASK_COMPLETE promise in output
    async checkForTaskCompletePromise() {
        try {
            // Read recent logs or output files
            const logFiles = await this.getRecentLogFiles();

            for (const logFile of logFiles) {
                const content = await fs.readFile(logFile, 'utf8');
                if (content.includes(this.taskCompletePromise)) {
                    console.log(`✅ TASK_COMPLETE promise found in ${logFile}`);
                    return true;
                }
            }

            return false;
        } catch (error) {
            return false;
        }
    }

    // Check for file movement completion (e.g., email moved to Done folder)
    async checkFileMovementCompletion() {
        try {
            // Check for significant file changes
            const currentFiles = await this.getCurrentFilesState();
            const previousFiles = this.lastFileState || {};

            // Detect file movements (deletions, creations, modifications)
            const createdFiles = Object.keys(currentFiles).filter(file =>
                !previousFiles[file]
            );

            const deletedFiles = Object.keys(previousFiles).filter(file =>
                !currentFiles[file]
            );

            const modifiedFiles = Object.keys(currentFiles).filter(file =>
                previousFiles[file] &&
                previousFiles[file] !== currentFiles[file]
            );

            // Log changes
            if (createdFiles.length > 0) {
                console.log(`📁 Created files: ${createdFiles.join(', ')}`);
            }
            if (deletedFiles.length > 0) {
                console.log(`🗑️  Deleted files: ${deletedFiles.join(', ')}`);
            }
            if (modifiedFiles.length > 0) {
                console.log(`📋 Modified files: ${modifiedFiles.join(', ')}`);
            }

            // Update file state
            this.lastFileState = currentFiles;

            // Simple completion logic: if significant file changes detected
            const totalChanges = createdFiles.length + deletedFiles.length + modifiedFiles.length;
            if (totalChanges > 3) { // Threshold for completion
                console.log(`✅ Significant file changes detected (${totalChanges} changes)`);
                return true;
            }

            return false;
        } catch (error) {
            return false;
        }
    }

    // Check for completion markers in logs
    async checkLogCompletion() {
        try {
            const logFiles = await this.getRecentLogFiles();

            for (const logFile of logFiles) {
                const content = await fs.readFile(logFile, 'utf8');

                // Check for common completion patterns
                const matches = this.completionLogPatterns.filter(pattern =>
                    content.includes(pattern)
                );

                if (matches.length > 0) {
                    console.log(`✅ Completion pattern found in ${logFile}: ${matches.join(', ')}`);
                    return true;
                }
            }

            return false;
        } catch (error) {
            return false;
        }
    }

    // Check for status completion in files
    async checkStatusCompletion() {
        try {
            // Check for status files or markers
            const statusFiles = [
                'task_status.json',
                'completion_marker.txt',
                'task_complete.flag',
                'status_complete.txt'
            ];

            for (const statusFile of statusFiles) {
                const filePath = path.join(this.workingDirectory, statusFile);
                if (await this.fileExists(filePath)) {
                    const content = await fs.readFile(filePath, 'utf8');
                    if (content.trim().toLowerCase() === 'complete') {
                        console.log(`✅ Task status marked as complete in ${statusFile}`);
                        return true;
                    }
                }
            }

            return false;
        } catch (error) {
            return false;
        }
    }

    // Set up file watcher for real-time completion detection
    setupFileWatcher() {
        const watcher = chokidar.watch(this.workingDirectory, {
            persistent: true,
            ignoreInitial: true,
            awaitWriteFinish: {
                stabilityThreshold: 2000,
                pollInterval: 100
            }
        });

        watcher.on('add', async (filePath) => {
            const fileName = path.basename(filePath);

            // Check for completion patterns in new files
            if (this.fileWatchPatterns.some(pattern => fileName.match(pattern))) {
                console.log(`✅ Completion marker detected: ${fileName}`);
                this.taskCompleted = true;
            }
        });

        watcher.on('change', async (filePath) => {
            const fileName = path.basename(filePath);

            // Check for status changes that indicate completion
            const statusFiles = [
                'task_status.json',
                'completion_marker.txt',
                'task_complete.flag'
            ];

            if (statusFiles.some(pattern => fileName === pattern)) {
                const content = await fs.readFile(filePath, 'utf8');
                if (content.trim().toLowerCase() === 'complete') {
                    console.log(`✅ Task status marked as complete in ${fileName}`);
                    this.taskCompleted = true;
                }
            }
        });

        watcher.on('unlink', async (filePath) => {
            const fileName = path.basename(filePath);

            // Check for deletion of task files (indicating completion)
            if (fileName.startsWith('EMAIL_') && fileName.endsWith('.md')) {
                console.log(`✅ Task email file processed and removed: ${fileName}`);
                this.taskCompleted = true;
            }
        });

        console.log('👀 File watcher set up for task completion detection');
        this.watcher = watcher;
    }

    // Create task marker file
    async createTaskMarker(prompt, status) {
        const markerContent = {
            taskId: uuidv4(),
            prompt: prompt,
            iteration: this.iteration,
            status: status,
            timestamp: new Date().toISOString(),
            context: this.taskContext
        };

        const markerFile = path.join(this.workingDirectory, `task_marker_${this.iteration}.json`);

        try {
            await fs.writeFile(markerFile, JSON.stringify(markerContent, null, 2), 'utf8');
            console.log(`📝 Created task marker: ${markerFile}`);
        } catch (error) {
            console.error('❌ Failed to create task marker:', error);
        }
    }

    // Generate next prompt based on previous result
    generateNextPrompt(previousPrompt, previousResult) {
        // Enhanced strategy with context preservation
        return `${previousPrompt}\n\n---\n\nIteration ${this.iteration + 1}: Continuing from previous work\n\nPrevious result: ${previousResult.substring(0, 150)}...\n\nContext: ${JSON.stringify(this.taskContext, null, 2)}`;
    }

    // Generate error recovery prompt
    generateErrorRecoveryPrompt(previousPrompt, error) {
        return `${previousPrompt}\n\n---\n\nERROR ENCOUNTERED: ${error.message}\n\nPlease retry the operation with error handling and recovery procedures. Context: ${JSON.stringify(this.taskContext, null, 2)}`;
    }

    // Cleanup resources
    async cleanup() {
        if (this.watcher) {
            this.watcher.close();
            console.log('👋 File watcher closed');
        }

        // Restore original process.exit
        if (this.exitHookInstalled) {
            process.exit = originalExit;
            this.exitHookInstalled = false;
        }

        // Create final task completion marker
        if (this.taskCompleted) {
            await this.createTaskCompletionMarker();
        }
    }

    // Create task completion marker
    async createTaskCompletionMarker() {
        const completionContent = {
            taskId: this.taskContext?.taskId || uuidv4(),
            completedAt: new Date().toISOString(),
            status: 'complete',
            iterations: this.iteration,
            taskCompleted: this.taskCompleted,
            context: this.taskContext
        };

        const completionFile = path.join(this.workingDirectory, 'task_completion_marker.json');

        try {
            await fs.writeFile(completionFile, JSON.stringify(completionContent, null, 2), 'utf8');
            console.log(`✅ Created task completion marker: ${completionFile}`);
        } catch (error) {
            console.error('❌ Failed to create task completion marker:', error);
        }
    }

    // Get recent log files
    async getRecentLogFiles() {
        try {
            const files = await fs.readdir(this.workingDirectory);
            return files.filter(file =>
                file.endsWith('.log') ||
                file.includes('output') ||
                file.includes('result')
            ).slice(-5); // Get last 5 log files
        } catch (error) {
            return [];
        }
    }

    // Get current files state with timestamps
    async getCurrentFilesState() {
        const files = {};

        try {
            const dirEntries = await fs.readdir(this.workingDirectory, { withFileTypes: true });

            for (const entry of dirEntries) {
                if (entry.isFile()) {
                    const stats = await fs.stat(path.join(this.workingDirectory, entry.name));
                    files[entry.name] = stats.mtime.toISOString();
                }
            }
        } catch (error) {
            console.error('❌ Failed to read directory state:', error);
        }

        return files;
    }

    // Utility methods
    async fileExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }

    async directoryExists(dirPath) {
        try {
            const stats = await fs.stat(dirPath);
            return stats.isDirectory();
        } catch {
            return false;
        }
    }

    // Log error to file
    async logError(error, prompt) {
        try {
            const errorContent = {
                timestamp: new Date().toISOString(),
                error: error.message,
                stack: error.stack,
                prompt: prompt.substring(0, 200),
                iteration: this.iteration
            };

            const errorFile = path.join(this.workingDirectory, `error_${Date.now()}.json`);
            await fs.writeFile(errorFile, JSON.stringify(errorContent, null, 2), 'utf8');
            console.log(`❌ Error logged to: ${errorFile}`);
        } catch (logError) {
            console.error('❌ Failed to log error:', logError);
        }
    }

    // Restart Claude Code with the same prompt
    async restartClaudeCode() {
        console.log('🚀 Restarting Claude Code with the same prompt...');

        // Get the last task marker to extract the prompt
        const markers = await this.getTaskMarkers();
        const lastMarker = markers[markers.length - 1];

        if (lastMarker && lastMarker.prompt) {
            await this.executeIteration(lastMarker.prompt);
        } else {
            console.error('❌ Could not find previous prompt to restart');
            process.exit(1);
        }
    }

    // Get all task markers
    async getTaskMarkers() {
        try {
            const files = await fs.readdir(this.workingDirectory);
            const markerFiles = files.filter(file =>
                file.startsWith('task_marker_') && file.endsWith('.json')
            );

            const markers = [];
            for (const file of markerFiles) {
                const filePath = path.join(this.workingDirectory, file);
                const content = await fs.readFile(filePath, 'utf8');
                markers.push(JSON.parse(content));
            }

            return markers.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        } catch (error) {
            console.error('❌ Failed to read task markers:', error);
            return [];
        }
    }
}

// Export the enhanced loop class
module.exports = {
    EnhancedRalphWiggumLoop,
    // Integration function
    integrateWithWorkflow: async (prompt, context = {}) => {
        console.log('\n⚙️  Integrating Enhanced Ralph Wiggum Loop with workflow...');

        try {
            const loop = new EnhancedRalphWiggumLoop({
                maxIterations: 8,
                checkIntervalMs: 2000,
                completionStrategies: ['promise_file', 'file_movement', 'log_patterns']
            });

            // Execute with stop hook
            await loop.startLoop(prompt, context);

            console.log('\n✅ Workflow integration successful!');
            return true;

        } catch (error) {
            console.error('\n❌ Integration error:', error.message);
            return false;
        }
    }
};

// Example usage (for demonstration purposes)
if (require.main === module) {
    const examplePrompt = 'Generate a comprehensive test report with file analysis and email composition';

    const loop = new EnhancedRalphWiggumLoop({
        maxIterations: 5,
        completionStrategies: ['promise_file', 'file_movement']
    });

    loop.startLoop(examplePrompt, { userId: 'test-user', taskType: 'email-composition' });
}