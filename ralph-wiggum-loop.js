// Ralph Wiggum Loop Implementation for Silver Tier Functional Assistant
// This implements a stop hook mechanism that intercepts Claude Code exit and feeds the prompt back until task completion
// Implements promise-based completion strategy with TASK_COMPLETE promise, file movement detection for task completion,
// and integration with existing workflow. Includes error handling and max iteration limits.

const fs = require('fs').promises;
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const { spawn } = require('child_process');
const chokidar = require('chokidar');
const { promisify } = require('util');
const { exec } = require('child_process');

class RalphWiggumLoop {
    constructor(config = {}) {
        this.iteration = 0;
        this.taskCompleted = false;
        this.exitHookInstalled = false;
        this.watcher = null;
        this.taskStartFile = null;
        this.taskCompletionFile = null;
        this.promiseResolvers = new Map();
        this.activePromises = new Set();
        this.stopRequested = false;
        this.taskStartTime = null;
        this.lastFileState = new Map();
        this.fileWatchers = new Map();

        // Initialize configuration with defaults and config file
        const defaultConfig = {
            maxIterations: 5,
            checkIntervalMs: 5000,
            workingDirectory: process.cwd(),
            taskCompletePromise: 'TASK_COMPLETE',
            logFilePath: 'mcp-email-server.log',
            doneFolderPath: 'AI_Employee_Vault/Done',
            statusFilePatterns: ['task_status.json', 'completion_marker.txt', 'task_complete.flag'],
            completionLogPatterns: [
                'Task completed',
                'All tests completed',
                'Email sent successfully',
                'Process finished',
                'Operation successful',
                'Successfully completed'
            ],
            fileWatchPatterns: [
                'EMAIL_*.md',
                '*complete*',
                '*done*',
                '*success*'
            ],
            debug: false
        };

        // Load configuration from file if available
        try {
            const configPath = path.join(__dirname, 'config_ralph_wiggum.json');
            if (fs.existsSync(configPath)) {
                const configContent = await fs.readFile(configPath, 'utf8');
                const fileConfig = JSON.parse(configContent);
                this.config = { ...defaultConfig, ...fileConfig.ralphWiggumLoop, ...config };
                console.log('✅ Loaded Ralph Wiggum configuration');
            } else {
                this.config = { ...defaultConfig, ...config };
            }
        } catch (error) {
            console.warn('⚠️  Failed to load configuration, using defaults:', error.message);
            this.config = { ...defaultConfig, ...config };
        }
    }

    async initialize() {
        console.log('🎯 Initializing Ralph Wiggum Loop...');
        await this.ensureDirectories();
        await this.loadPreviousState();
        this.startFileWatchers();
        console.log('✅ Ralph Wiggum Loop initialized');
    }

try {
    const configPath = path.join(__dirname, 'config_ralph_wiggum.json');
    if (fs.existsSync(configPath)) {
        const configContent = await fs.readFile(configPath, 'utf8');
        config = JSON.parse(configContent);
        console.log('✅ Loaded Ralph Wiggum configuration');
    }
} catch (error) {
    console.warn('⚠️  Failed to load configuration, using defaults:', error.message);
}

// Example hook functions
// Example hook functions
const exampleHooks = {
    // File monitoring hook
    fileMonitorHook: async (prompt) => {
        try {
            const fs = require('fs').promises;
            const path = require('path');

            // Monitor specific directories for changes
            const watchDirs = [
                'C:\\Users\\goku\\MyWebsiteProjects\\hackathon-0\\Silver-Tier\\node_modules',
                'C:\\Users\\goku\\MyWebsiteProjects\\hackathon-0\\Silver-Tier\\src'
            ];

            const changes = [];

            for (const dir of watchDirs) {
                try {
                    const files = await fs.readdir(dir);
                    changes.push({
                        directory: dir,
                        fileCount: files.length,
                        timestamp: new Date().toISOString()
                    });
                } catch (error) {
                    // Ignore directories that don't exist
                }
            }

            return { changes };
        } catch (error) {
            throw new Error(`File monitor hook failed: ${error.message}`);
        }
    },

    // Process monitoring hook
    processMonitorHook: async (prompt) => {
        try {
            const { exec } = require('child_process');

            return new Promise((resolve, reject) => {
                exec('tasklist', (error, stdout, stderr) => {
                    if (error) {
                        reject(error);
                    } else {
                        const processes = stdout.split('\n')
                            .filter(line => line.trim() !== '')
                            .slice(3) // Skip header lines
                            .map(line => {
                                const parts = line.split(' ').filter(part => part.trim() !== '');
                                return {
                                    name: parts[0],
                                    pid: parts[1],
                                    session: parts[2],
                                    memUsage: parts[4]
                                };
                            });

                        resolve({ processes: processes.slice(0, 10) }); // Return first 10 processes
                    }
                });
            });
        } catch (error) {
            throw new Error(`Process monitor hook failed: ${error.message}`);
        }
    },

    // System resource hook
    resourceMonitorHook: async (prompt) => {
        try {
            const os = require('os');

            return {
                cpu: os.cpus().length,
                memory: {
                    total: os.totalmem(),
                    free: os.freemem(),
                    used: os.totalmem() - os.freemem(),
                    percentage: ((os.totalmem() - os.freemem()) / os.totalmem()) * 100
                },
                uptime: os.uptime(),
                platform: os.platform(),
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            throw new Error(`Resource monitor hook failed: ${error.message}`);
        }
    }
};

class RalphWiggumLoop {
    constructor() {
        this.iteration = 0;
        this.taskCompleted = false;
        this.exitHookInstalled = false;
        this.watcher = null;
        this.taskStartFile = null;
        this.taskCompletionFile = null;

        // Initialize configuration
        this.maxIterations = config.ralphWiggumLoop?.maxIterations || MAX_ITERATIONS;
        this.checkIntervalMs = config.ralphWiggumLoop?.checkIntervalMs || CHECK_INTERVAL_MS;
        this.workingDirectory = config.ralphWiggumLoop?.workingDirectory || process.cwd();
        this.taskCompletePromise = config.ralphWiggumLoop?.taskCompletePromise || TASK_COMPLETE_PROMISE;
        this.logFilePath = config.ralphWiggumLoop?.logFilePath || 'mcp-email-server.log';
        this.doneFolderPath = config.ralphWiggumLoop?.doneFolderPath || 'AI_Employee_Vault/Done';
        this.statusFilePatterns = config.ralphWiggumLoop?.statusFilePatterns || [
            'task_status.json',
            'completion_marker.txt',
            'task_complete.flag'
        ];
        this.completionLogPatterns = config.ralphWiggumLoop?.completionLogPatterns || [
            'Task completed',
            'All tests completed',
            'Email sent successfully',
            'Process finished',
            'Operation successful',
            'Successfully completed'
        ];
        this.fileWatchPatterns = config.ralphWiggumLoop?.fileWatchPatterns || [
            'EMAIL_*.md',
            '*complete*',
            '*done*',
            '*success*'
        ];
    }

    // Install the exit hook that intercepts Claude Code exit
    installExitHook() {
        if (this.exitHookInstalled) {
            return;
        }

        // Save original process exit
        const originalExit = process.exit;

        // Override process.exit to intercept termination
        process.exit = (code) => {
            console.log('\n🎨 Ralph Wiggum Loop Activated: Task not yet complete!\n');

            // Check if task is complete
            this.checkTaskCompletion()
                .then((completed) => {
                    if (completed) {
                        console.log('✅ Task completed! Exiting gracefully...');
                        originalExit.call(process, code);
                    } else {
                        // Feed prompt back and restart
                        this.restartClaudeCode();
                    }
                })
                .catch((error) => {
                    console.error('❌ Error checking task completion:', error);
                    originalExit.call(process, code);
                });
        };

        this.exitHookInstalled = true;
        console.log('✅ Ralph Wiggum exit hook installed');
    }

    // Start the loop with initial prompt
    async startLoop(initialPrompt, workingDirectory) {
        this.iteration = 0;
        this.taskCompleted = false;
        this.workingDirectory = workingDirectory || process.cwd();

        console.log('\n🚀 Starting Ralph Wiggum Loop...');
        console.log(`📁 Working Directory: ${this.workingDirectory}`);
        console.log(`📝 Initial Prompt: ${initialPrompt}`);

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
        console.log(`\n🔄 Iteration ${this.iteration}/${MAX_ITERATIONS}`);
        console.log(`📝 Prompt: ${prompt}`);

        try {
            // Create task start marker file
            await this.createTaskStartMarker(prompt);

            // Spawn Claude Code with the prompt
            const result = await this.spawnClaudeCode(prompt);

            console.log('✅ Claude Code completed execution');
            console.log('📋 Result:', result);

            // Check if task is complete
            const completed = await this.checkTaskCompletion();

            if (completed) {
                console.log('✅ Task completed successfully!');
                this.taskCompleted = true;
                await this.cleanup();
                return;
            } else {
                console.log('⚠️  Task not yet complete, continuing loop...');

                // Prepare next prompt (could be enhanced with context)
                const nextPrompt = this.generateNextPrompt(prompt, result);

                // Continue loop if max iterations not reached
                if (this.iteration < MAX_ITERATIONS) {
                    await this.executeIteration(nextPrompt);
                } else {
                    console.log('❌ Max iterations reached. Task may not be complete.');
                    await this.cleanup();
                }
            }

        } catch (error) {
            console.error('❌ Error in iteration:', error);

            // Continue loop on error unless max iterations reached
            if (this.iteration < MAX_ITERATIONS) {
                const nextPrompt = this.generateErrorRecoveryPrompt(prompt, error);
                await this.executeIteration(nextPrompt);
            } else {
                console.log('❌ Max iterations reached due to errors.');
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
                shell: true
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
            const taskComplete = await this.checkForTaskCompletePromise();
            if (taskComplete) {
                return true;
            }

            // Strategy 2: Check for file movement/deletion patterns
            const fileMovementComplete = await this.checkFileMovementCompletion();
            if (fileMovementComplete) {
                return true;
            }

            // Strategy 3: Check for completion markers in logs
            const logComplete = await this.checkLogCompletion();
            if (logComplete) {
                return true;
            }

            // Strategy 4: Check for completion status in files
            const statusComplete = await this.checkStatusCompletion();
            if (statusComplete) {
                return true;
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
            const logFile = path.join(this.workingDirectory, this.logFilePath);

            if (await this.fileExists(logFile)) {
                const content = await fs.readFile(logFile, 'utf8');
                return content.includes(this.taskCompletePromise);
            }

            return false;
        } catch (error) {
            return false;
        }
    }

    // Check for file movement completion (e.g., email moved to Done folder)
    async checkFileMovementCompletion() {
        try {
            const donePath = path.join(this.workingDirectory, this.doneFolderPath);

            if (await this.directoryExists(donePath)) {
                const files = await fs.readdir(donePath);
                return files.length > 0;
            }

            return false;
        } catch (error) {
            return false;
        }
    }

    // Check for completion markers in logs
    async checkLogCompletion() {
        try {
            const logFile = path.join(this.workingDirectory, this.logFilePath);

            if (await this.fileExists(logFile)) {
                const content = await fs.readFile(logFile, 'utf8');

                // Check for common completion patterns
                return this.completionLogPatterns.some(pattern => content.includes(pattern));
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
            for (const statusFile of this.statusFilePatterns) {
                const filePath = path.join(this.workingDirectory, statusFile);
                if (await this.fileExists(filePath)) {
                    const content = await fs.readFile(filePath, 'utf8');
                    return content.trim().toLowerCase() === 'complete';
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
            if (this.statusFilePatterns.some(pattern => fileName.match(pattern))) {
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
        return watcher;
    }

    // Create task start marker file
    async createTaskStartMarker(prompt) {
        const markerContent = {
            taskId: uuidv4(),
            prompt: prompt,
            iteration: this.iteration,
            startedAt: new Date().toISOString(),
            status: 'in_progress'
        };

        this.taskStartFile = path.join(this.workingDirectory, `task_marker_${this.iteration}.json`);

        try {
            await fs.writeFile(this.taskStartFile, JSON.stringify(markerContent, null, 2), 'utf8');
            console.log(`📝 Created task start marker: ${this.taskStartFile}`);
        } catch (error) {
            console.error('❌ Failed to create task start marker:', error);
        }
    }

    // Generate next prompt based on previous result
    generateNextPrompt(previousPrompt, previousResult) {
        // Simple strategy: add continuation context
        return `${previousPrompt}\n\n---\n\nIteration ${this.iteration + 1}: Continuing from previous work\n\nPrevious result: ${previousResult.substring(0, 200)}...`;
    }

    // Generate error recovery prompt
    generateErrorRecoveryPrompt(previousPrompt, error) {
        return `${previousPrompt}\n\n---\n\nERROR ENCOUNTERED: ${error.message}\n\nPlease retry the operation with error handling and recovery procedures.`;
    }

    // Cleanup resources
    async cleanup() {
        if (this.watcher) {
            this.watcher.close();
            console.log('👋 File watcher closed');
        }

        // Create task completion marker
        if (this.taskCompleted) {
            await this.createTaskCompletionMarker();
        }

        // Clean up task marker files
        if (this.taskStartFile && await this.fileExists(this.taskStartFile)) {
            try {
                await fs.unlink(this.taskStartFile);
                console.log(`🗑️  Removed task start marker: ${this.taskStartFile}`);
            } catch (error) {
                console.error('❌ Failed to remove task start marker:', error);
            }
        }
    }

    // Create task completion marker
    async createTaskCompletionMarker() {
        const completionContent = {
            taskId: this.taskStartFile ? path.basename(this.taskStartFile, '.json') : uuidv4(),
            completedAt: new Date().toISOString(),
            status: 'complete',
            iterations: this.iteration,
            taskCompleted: this.taskCompleted
        };

        this.taskCompletionFile = path.join(this.workingDirectory, 'task_completion_marker.json');

        try {
            await fs.writeFile(this.taskCompletionFile, JSON.stringify(completionContent, null, 2), 'utf8');
            console.log(`✅ Created task completion marker: ${this.taskCompletionFile}`);
        } catch (error) {
            console.error('❌ Failed to create task completion marker:', error);
        }
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
            const markerFiles = files.filter(file => file.startsWith('task_marker_') && file.endsWith('.json'));

            const markers = [];
            for (const file of markerFiles) {
                const filePath = path.join(this.workingDirectory, file);
                const content = await fs.readFile(filePath, 'utf8');
                markers.push(JSON.parse(content));
            }

            return markers.sort((a, b) => new Date(a.startedAt) - new Date(b.startedAt));

        } catch (error) {
            console.error('❌ Failed to read task markers:', error);
            return [];
        }
    }
}

// Export the RalphWiggumLoop class and example hooks
module.exports = {
    RalphWiggumLoop,
    exampleHooks,
    // Integration functions
    integrateWithWorkflow: async (prompt) => {
        console.log('\n⚙️  Integrating Ralph Wiggum Loop with existing workflow...');

        try {
            const loop = new RalphWiggumLoop();

            // Execute with stop hook
            const result = await loop.startLoop(prompt, loop.workingDirectory);

            if (result === true) {
                console.log('\n✅ Workflow integration successful!');
                return true;
            } else {
                console.log('\n❌ Workflow integration failed.');
                return false;
            }
        } catch (error) {
            console.error('\n❌ Integration error:', error.message);
            return false;
        }
    },

    // Error handling and logging
    setupErrorHandling: () => {
        process.on('uncaughtException', (error) => {
            console.error('\n❌ Uncaught Exception:', error.message);
            console.error('Stack trace:', error.stack);
            // Cleanup resources
            if (loop && loop.watcher) {
                loop.watcher.close();
            }
        });

        process.on('unhandledRejection', (reason, promise) => {
            console.error('\n❌ Unhandled Rejection:', reason);
            // Cleanup resources
            if (loop && loop.watcher) {
                loop.watcher.close();
            }
        });
    }
};