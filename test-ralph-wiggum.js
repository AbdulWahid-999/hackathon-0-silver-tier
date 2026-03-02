// Test script for Ralph Wiggum Loop integration
// This tests the integration with the MCP Email Server

const { RalphWiggumLoop } = require('./ralph-wiggum-loop');
const { MCPServer } = require('./mcp-email-server');
const http = require('http');

// Test function to demonstrate Ralph Wiggum loop with email server
async function testRalphWiggumWithEmailServer() {
    console.log('🚀 Testing Ralph Wiggum Loop with MCP Email Server');
    console.log('=================================================');

    try {
        // Initialize MCP server
        const server = new MCPServer();

        // Create Ralph Wiggum loop instance
        const ralphWiggum = new RalphWiggumLoop();
        ralphWiggum.installExitHook();

        console.log('✅ MCP Server and Ralph Wiggum loop initialized');

        // Register hooks for email monitoring
        ralphWiggum.registerHook('emailMonitor', async (prompt) => {
            // Check for new emails in Needs_Action folder
            const fs = require('fs').promises;
            const path = require('path');

            try {
                const needsActionPath = path.join(process.cwd(), 'AI_Employee_Vault', 'Needs_Action');
                if (await fs.exists(needsActionPath)) {
                    const files = await fs.readdir(needsActionPath);
                    const emailFiles = files.filter(file =>
                        file.startsWith('EMAIL_') && file.endsWith('.md')
                    );

                    return {
                        pendingEmails: emailFiles.length,
                        emailFiles,
                        timestamp: new Date().toISOString()
                    };
                }
            } catch (error) {
                return { error: 'Failed to monitor emails' };
            }
        });

        // Test 1: Compose an email
        console.log('\n📝 Test 1: Composing an email...');

        const composeResult = await server.handleRequest('compose-email', {
            recipients: 'test@example.com',
            subject: 'Test Email from Ralph Wiggum Demo',
            body: 'This is a test email to demonstrate the Ralph Wiggum loop integration with the MCP Email Server.'
        });

        if (composeResult.success) {
            console.log('✅ Email composed successfully');
            console.log(`   Email ID: ${composeResult.result.emailId}`);
            console.log(`   File Path: ${composeResult.result.filePath}`);
        } else {
            console.log('❌ Failed to compose email:', composeResult.error);
            return;
        }

        // Start Ralph Wiggum loop for this task
        const taskId = composeResult.result.emailId;
        const taskConfig = {
            prompt: `Monitor and complete email task: ${taskId}`,
            targetFiles: [
                `AI_Employee_Vault/Needs_Action/EMAIL_${taskId}.md`,
                `AI_Employee_Vault/Done/EMAIL_${taskId}.md`
            ],
            maxIterations: 15
        };

        console.log('\n🔄 Starting Ralph Wiggum loop for email task...');
        const loopResult = await ralphWiggum.startLoop(taskConfig.prompt, process.cwd());
        console.log(`✅ Ralph Wiggum loop completed: ${loopResult}`);

        // Test 2: Check email status
        console.log('\n🔍 Test 2: Checking email status...');

        const statusResult = await server.handleRequest('get-approval-status', {
            emailId: taskId
        });

        if (statusResult.success) {
            console.log('✅ Status check successful');
            console.log(`   Status: ${statusResult.result.status}`);
            console.log(`   File Path: ${statusResult.result.filePath}`);
        } else {
            console.log('❌ Failed to check status:', statusResult.error);
        }

        // Test 3: List pending emails
        console.log('\n📋 Test 3: Listing pending emails...');

        const pendingResult = await server.handleRequest('list-pending-emails');

        if (pendingResult.success) {
            console.log('✅ Pending emails retrieved');
            console.log(`   Count: ${pendingResult.result.length}`);
            if (pendingResult.result.length > 0) {
                console.log('   First email:', pendingResult.result[0]);
            }
        } else {
            console.log('❌ Failed to list pending emails:', pendingResult.error);
        }

        // Test 4: Send the email
        console.log('\n🚃 Test 4: Sending the email...');

        const sendResult = await server.handleRequest('send-email', {
            emailId: taskId,
            approval: true
        });

        if (sendResult.success) {
            console.log('✅ Email sent successfully');
            console.log(`   Status: ${sendResult.result.status}`);
            console.log(`   Message: ${sendResult.result.message}`);
        } else {
            console.log('❌ Failed to send email:', sendResult.error);
        }

        // Test 5: Verify email moved to Done folder
        console.log('\n🔍 Test 5: Verifying email moved to Done folder...');

        const donePath = path.join(process.cwd(), 'AI_Employee_Vault', 'Done');
        const fs = require('fs').promises;

        try {
            const files = await fs.readdir(donePath);
            const movedEmail = files.find(file =>
                file.startsWith(`EMAIL_${taskId}`) && file.endsWith('.md')
            );

            if (movedEmail) {
                console.log('✅ Email successfully moved to Done folder');
                console.log(`   File: ${movedEmail}`);
            } else {
                console.log('❌ Email not found in Done folder');
            }
        } catch (error) {
            console.log('❌ Error checking Done folder:', error.message);
        }

        console.log('\n✅ All tests completed!');

    } catch (error) {
        console.error('
❌ Test failed:', error);
    }
}

// Standalone test to demonstrate exit hook
async function testExitHook() {
    console.log('🚀 Testing Exit Hook...');
    console.log('========================');

    const ralphWiggum = new RalphWiggumLoop();
    ralphWiggum.installExitHook();

    console.log('⏸️  Simulating task in progress...');
    console.log('Press Ctrl+C to test the exit hook...');

    // Simulate a long-running task
    let counter = 0;
    const interval = setInterval(() => {
        counter++;
        console.log(`Working... (${counter}s)`);

        // Create a completion marker after 10 seconds to simulate task completion
        if (counter === 10) {
            const fs = require('fs').promises;
            fs.writeFile('task_completion_marker.txt', 'Task completed successfully')
                .then(() => console.log('✅ Created completion marker file'))
                .catch(console.error);
        }
    }, 1000);

    // Clean up interval on exit
    process.on('exit', () => {
        clearInterval(interval);
        console.log('\n⏹️  Task cleanup completed');
    });
}

// Run tests
async function runTests() {
    console.log('🧪 Running Ralph Wiggum Loop Tests\n');

    await testRalphWiggumWithEmailServer();
    console.log('\n' + '='.repeat(50) + '\n');

    // Uncomment to test exit hook (will block execution)
    // await testExitHook();
}

// Run if this file is executed directly
if (require.main === module) {
    runTests().catch(console.error);
}

module.exports = { testRalphWiggumWithEmailServer, testExitHook };