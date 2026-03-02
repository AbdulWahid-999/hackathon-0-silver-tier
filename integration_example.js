// Integration Example: Using Ralph Wiggum Loop with MCP Email Server
// This demonstrates how to integrate the Ralph Wiggum Loop with the existing MCP Email Server

const { RalphWiggumLoop } = require('./ralph-wiggum-loop');
const fs = require('fs').promises;
const path = require('path');

// Integration configuration
const INTEGRATION_CONFIG = {
    mcpServerPath: 'C:\\Users\\goku\\MyWebsiteProjects\\hackathon-0\\Silver-Tier\\mcp-email-server.js',
    vaultPath: 'C:\\Users\\goku\\MyWebsiteProjects\\hackathon-0\\Bronze-Tier\\AI_Employee_Vault',
    needsActionPath: 'Needs_Action',
    donePath: 'Done',
    logFile: 'mcp-email-server.log',
    taskCompletePromise: 'TASK_COMPLETE',
    maxIterations: 5,
    checkInterval: 5000
};

class MCPRalphIntegration {
    constructor() {
        this.loop = new RalphWiggumLoop();
        this.config = INTEGRATION_CONFIG;
    }

    // Initialize the integration
    async initialize() {
        console.log('🚀 Initializing MCP Ralph Wiggum Integration...');

        // Ensure directories exist
        await this.ensureDirectories();

        // Configure the loop with MCP-specific settings
        this.configureLoop();

        console.log('✅ Integration initialized successfully');
    }

    // Ensure required directories exist
    async ensureDirectories() {
        const directories = [
            path.join(this.config.vaultPath, this.config.needsActionPath),
            path.join(this.config.vaultPath, this.config.donePath)
        ];

        for (const dir of directories) {
            try {
                await fs.mkdir(dir, { recursive: true });
                console.log(`✅ Created directory: ${dir}`);
            } catch (error) {
                console.log(`⚠️  Directory exists: ${dir}`);
            }
        }
    }

    // Configure the Ralph Wiggum Loop for MCP integration
    configureLoop() {
        // Override default configuration with MCP-specific settings
        this.loop.maxIterations = this.config.maxIterations;
        this.loop.checkInterval = this.config.checkInterval;

        // Set up custom completion detection for MCP
        this.loop.checkTaskCompletion = async () => {
            try {
                // MCP-specific completion strategies
                const mcpComplete = await this.checkMcpCompletion();
                if (mcpComplete) return true;

                // Fall back to default strategies
                return await RalphWiggumLoop.prototype.checkTaskCompletion.call(this.loop);
            } catch (error) {
                console.error('Error in MCP completion check:', error);
                return false;
            }
        };
    }

    // MCP-specific completion detection
    async checkMcpCompletion() {
        try {
            // Check if MCP server is running and processing emails
            const serverLogFile = path.join(this.config.vaultPath, this.config.logFile);

            if (await this.fileExists(serverLogFile)) {
                const content = await fs.readFile(serverLogFile, 'utf8');

                // Check for MCP-specific completion patterns
                const mcpPatterns = [
                    'Email sent successfully',
                    'All tests completed',
                    'MCP client disconnected',
                    'Server running on port',
                    this.config.taskCompletePromise
                ];

                return mcpPatterns.some(pattern => content.includes(pattern));
            }

            return false;
        } catch (error) {
            console.error('Error checking MCP completion:', error);
            return false;
        }
    }

    // Start the integrated workflow
    async startWorkflow(initialPrompt) {
        console.log('🚀 Starting MCP Ralph Wiggum Workflow...');
        console.log(`📝 Initial Prompt: ${initialPrompt.substring(0, 100)}...`);

        try {
            // Start the Ralph Wiggum Loop
            await this.loop.startLoop(initialPrompt, this.config.mcpServerPath);

            console.log('✅ Workflow completed successfully');

        } catch (error) {
            console.error('❌ Workflow failed:', error);
            throw error;
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

    // Start MCP Email Server
    async startMcpServer() {
        console.log('🚀 Starting MCP Email Server...');

        const { spawn } = require('child_process');

        return new Promise((resolve, reject) => {
            const mcpProcess = spawn('node', [this.config.mcpServerPath], {
                cwd: this.config.mcpServerPath,
                stdio: 'pipe',
                shell: true
            });

            let output = '';
            let errorOutput = '';

            mcpProcess.stdout.on('data', (data) => {
                output += data.toString();
                process.stdout.write(data.toString());

                // Check for server startup
                if (output.includes('MCP Email Server running on port')) {
                    console.log('✅ MCP Email Server started successfully');
                    resolve(mcpProcess);
                }
            });

            mcpProcess.stderr.on('data', (data) => {
                errorOutput += data.toString();
                process.stderr.write(data.toString());
            });

            mcpProcess.on('close', (code) => {
                if (code === 0) {
                    console.log('✅ MCP Email Server stopped gracefully');
                } else {
                    console.error('❌ MCP Email Server exited with error:', errorOutput.trim());
                    reject(new Error(`MCP server exited with code ${code}`));
                }
            });

            mcpProcess.on('error', (error) => {
                console.error('❌ Failed to start MCP Email Server:', error);
                reject(error);
            });
        });
    }

    // Stop MCP Email Server gracefully
    async stopMcpServer(process) {
        console.log('🛑 Stopping MCP Email Server...');

        if (process && process.kill) {
            process.kill('SIGTERM');
            return true;
        }

        return false;
    }

    // Main integration workflow
    async runIntegration() {
        try {
            // Initialize integration
            await this.initialize();

            // Start MCP Email Server
            const mcpProcess = await this.startMcpServer();

            // Create a comprehensive test prompt
            const testPrompt = `Implement and test a complete email workflow system with the following requirements:

1. Set up the MCP Email Server with proper configuration
2. Create a test email workflow with approval process
3. Implement comprehensive logging and monitoring
4. Add error handling and recovery mechanisms
5. Create test cases for all functionality
6. Document the complete system
7. Ensure the system is production-ready

The system should handle email composition, approval workflows, sending, and comprehensive error handling.`;

            // Start the Ralph Wiggum Loop with the test prompt
            await this.startWorkflow(testPrompt);

            // Stop the MCP server
            await this.stopMcpServer(mcpProcess);

            console.log('🎉 Integration workflow completed successfully');

        } catch (error) {
            console.error('❌ Integration failed:', error);
            throw error;
        }
    }
}

// Run the integration if this file is executed directly
if (require.main === module) {
    const integration = new MCPRalphIntegration();
    integration.runIntegration()
        .then(() => {
            console.log('✅ Integration test completed');
            process.exit(0);
        })
        .catch((error) => {
            console.error('❌ Integration test failed:', error);
            process.exit(1);
        });
}

module.exports = { MCPRalphIntegration };