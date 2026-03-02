const { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } = require('@jest/globals');
const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

// Import the client
const { EnhancedMCPClient } = require('../mcp-email-client-enhanced.js');

// Integration test configuration
describe('MCP Email Server Integration', () => {
    let serverProcess;
    let client;
    let testVaultPath;
    let needsActionPath;
    let donePath;

    beforeAll(async () => {
        // Setup test environment
        testVaultPath = path.join(__dirname, 'integration-test-vault');
        needsActionPath = path.join(testVaultPath, 'Needs_Action');
        donePath = path.join(testVaultPath, 'Done');

        // Set environment variables for testing
        process.env.VAULT_PATH = testVaultPath;
        process.env.EMAIL_USER = 'test@example.com';
        process.env.EMAIL_PASS = 'test-password';
        process.env.MCP_AUTH_TOKEN = 'test-token';
        process.env.SECURITY_KEY = 'test-security-key';

        // Create test vault structure
        await fs.mkdir(testVaultPath, { recursive: true });
        await fs.mkdir(needsActionPath, { recursive: true });
        await fs.mkdir(donePath, { recursive: true });

        // Start the server process
        serverProcess = spawn('node', ['mcp-email-server-enhanced.js'], {
            cwd: path.join(__dirname, '..'),
            stdio: 'pipe',
            env: process.env
        });

        // Wait for server to start
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Create client
        client = new EnhancedMCPClient();
    });

    afterAll(async () => {
        // Stop the server process
        serverProcess.kill();

        // Clean up test environment
        await fs.rm(testVaultPath, { recursive: true, force: true });
    });

    beforeEach(async () => {
        // Clean up test vault before each test
        await fs.rm(needsActionPath, { recursive: true, force: true });
        await fs.mkdir(needsActionPath, { recursive: true });
        await fs.rm(donePath, { recursive: true, force: true });
        await fs.mkdir(donePath, { recursive: true });
    });

    it('should start the server successfully', async () => {
        // Check if server process is running
        expect(serverProcess.pid).toBeDefined();
        expect(serverProcess.connected).toBe(true);

        // Check server output for startup message
        let output = '';
        serverProcess.stdout.on('data', (data) => {
            output += data.toString();
        });

        // Wait a bit for startup message
        await new Promise(resolve => setTimeout(resolve, 1000));

        expect(output).toContain('Enhanced MCP Email Server running on port');
    });

    it('should handle basic email composition and sending', async () => {
        // Compose an email
        const composedEmail = await client.composeEmail({
            recipients: 'integration-test@example.com',
            subject: 'Integration Test Email',
            body: 'This is an integration test email',
            priority: 'high',
            category: 'testing'
        });

        expect(composedEmail).toBeDefined();
        expect(composedEmail.emailId).toBeDefined();
        expect(composedEmail.status).toBe('pending');

        // Check if file was created
        const emailFilePath = path.join(needsActionPath, `${composedEmail.emailId}.md`);
        const fileExists = await fs.access(emailFilePath).then(() => true).catch(() => false);
        expect(fileExists).toBe(true);

        // Send the email
        const sendResult = await client.sendEmail({
            emailId: composedEmail.emailId,
            approval: true
        });

        expect(sendResult).toBeDefined();
        expect(sendResult.emailId).toBe(composedEmail.emailId);
        expect(sendResult.status).toBe('sent');

        // Check if file moved to done folder
        const doneFiles = await fs.readdir(donePath);
        const emailFileInDone = doneFiles.find(file => file.startsWith(`EMAIL_${composedEmail.emailId}`));
        expect(emailFileInDone).toBeDefined();
    });

    it('should handle email scheduling', async () => {
        const composedEmail = await client.composeEmail({
            recipients: 'schedule-test@example.com',
            subject: 'Scheduled Test Email',
            body: 'This is a scheduled test email',
            priority: 'medium',
            category: 'testing'
        });

        const scheduleTime = new Date();
        scheduleTime.setSeconds(scheduleTime.getSeconds() + 5); // Schedule for 5 seconds from now

        const scheduledEmail = await client.scheduleEmail({
            emailId: composedEmail.emailId,
            scheduleFor: scheduleTime.toISOString()
        });

        expect(scheduledEmail).toBeDefined();
        expect(scheduledEmail.emailId).toBe(composedEmail.emailId);
        expect(scheduledEmail.status).toBe('scheduled');
        expect(scheduledEmail.scheduleFor).toBe(scheduleTime.toISOString());

        // Wait for email to be sent
        await new Promise(resolve => setTimeout(resolve, 6000));

        // Check if email was sent
        const status = await client.getApprovalStatus({ emailId: composedEmail.emailId });
        expect(status.status).toBe('sent');
    });

    it('should handle batch email operations', async () => {
        const emails = [
            {
                recipients: 'batch1@example.com',
                subject: 'Batch Email 1',
                body: 'This is the first batch email',
                priority: 'low'
            },
            {
                recipients: 'batch2@example.com',
                subject: 'Batch Email 2',
                body: 'This is the second batch email',
                priority: 'high'
            },
            {
                recipients: 'batch3@example.com',
                subject: 'Batch Email 3',
                body: 'This is the third batch email',
                priority: 'medium'
            }
        ];

        // Send batch emails
        const results = await client.batchSendEmails(emails);

        expect(results).toBeDefined();
        expect(Array.isArray(results)).toBe(true);
        expect(results.length).toBe(3);

        results.forEach((result, index) => {
            expect(result.success).toBe(true);
            expect(result.result).toBeDefined();
            expect(result.result.emailId).toBeDefined();
            expect(result.result.status).toBe('sent');
            expect(result.result.metadata).toBeDefined();
            expect(result.result.metadata.category).toBe('testing');
        });
    });

    it('should generate email reports', async () => {
        // Create some test emails first
        const testEmails = [
            {
                recipients: 'report1@example.com',
                subject: 'Report Test 1',
                body: 'This is for report generation',
                priority: 'high',
                category: 'business'
            },
            {
                recipients: 'report2@example.com',
                subject: 'Report Test 2',
                body: 'This is for report generation',
                priority: 'low',
                category: 'technical'
            }
        ];

        // Send the test emails
        for (const emailData of testEmails) {
            const composed = await client.composeEmail(emailData);
            await client.sendEmail({ emailId: composed.emailId, approval: true });
        }

        // Generate report
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 1); // Last 24 hours
        const report = await client.generateEmailReport(
            startDate.getTime(),
            Date.now(),
            'sent'
        );

        expect(report).toBeDefined();
        expect(report.total).toBeGreaterThan(0);
        expect(report.byStatus).toBeDefined();
        expect(report.byCategory).toBeDefined();
        expect(report.byPriority).toBeDefined();

        // Should include our test emails
        expect(report.total).toBeGreaterThanOrEqual(2);
    });

    it('should handle recipient validation', async () => {
        const validation = await client.validateRecipients({
            recipients: 'valid@example.com,invalid-email,blocked@company.com,test@allowed.com'
        });

        expect(validation).toBeDefined();
        expect(validation.recipients).toBeDefined();
        expect(validation.validationResults).toBeDefined();
        expect(validation.validationResults.length).toBe(4);

        const results = validation.validationResults;
        const validResult = results.find(r => r.email === 'valid@example.com');
        const invalidResult = results.find(r => r.email === 'invalid-email');
        const blockedResult = results.find(r => r.email === 'blocked@company.com');
        const allowedResult = results.find(r => r.email === 'test@allowed.com');

        expect(validResult.valid).toBe(true);
        expect(validResult.allowed).toBe(true);
        expect(validResult.reason).toBe('Valid');

        expect(invalidResult.valid).toBe(false);
        expect(invalidResult.reason).toBe('Invalid email format');

        expect(blockedResult.valid).toBe(true);
        expect(blockedResult.allowed).toBe(false);
        expect(blockedResult.reason).toBe('Domain not allowed');

        expect(allowedResult.valid).toBe(true);
        expect(allowedResult.allowed).toBe(true);
        expect(allowedResult.reason).toBe('Valid');
    });

    it('should handle error conditions gracefully', async () => {
        // Test with invalid authentication (should fail)
        try {
            // Try to send email with invalid token
            // This would require modifying the client to use invalid token
            // For now, we'll test with a non-existent email ID
            await client.sendEmail({ emailId: 'nonexistent-id', approval: true });
            expect(false).toBe(true); // Should not reach here
        } catch (error) {
            expect(error.message).toBeDefined();
            expect(error.message).toContain('Email not found');
        }

        // Test with invalid email format
        try {
            await client.composeEmail({
                recipients: 'invalid-email',
                subject: 'Test Invalid',
                body: 'This should fail',
                priority: 'medium'
            });
            expect(false).toBe(true); // Should not reach here
        } catch (error) {
            expect(error.message).toBeDefined();
            expect(error.message).toContain('Missing required email parameters');
        }
    });

    it('should handle concurrent operations', async () => {
        const promises = [];
        for (let i = 0; i < 10; i++) {
            promises.push(client.composeEmail({
                recipients: `concurrent${i}@example.com`,
                subject: `Concurrent Test ${i}`,
                body: 'This is a concurrent test',
                priority: 'medium'
            }));
        }

        const results = await Promise.all(promises);
        expect(results).toBeDefined();
        expect(Array.isArray(results)).toBe(true);
        expect(results.length).toBe(10);

        results.forEach((result, index) => {
            expect(result.emailId).toBeDefined();
            expect(result.status).toBe('pending');
            expect(result.metadata).toBeDefined();
            expect(result.metadata.recipients).toBe(`concurrent${index}@example.com`);
        });
    });

    it('should maintain server stability under load', async () => {
        const loadTestPromises = [];
        for (let i = 0; i < 20; i++) {
            loadTestPromises.push(client.composeEmail({
                recipients: `load${i}@example.com`,
                subject: `Load Test ${i}`,
                body: 'This is a load test',
                priority: 'medium'
            }));
        }

        // Send all emails
        const composedResults = await Promise.all(loadTestPromises);
        expect(composedResults.length).toBe(20);

        const sendPromises = composedResults.map(result =>
            client.sendEmail({ emailId: result.emailId, approval: true })
        );

        const sendResults = await Promise.all(sendPromises);
        expect(sendResults.length).toBe(20);

        // Check server didn't crash
        expect(serverProcess.killed).toBe(false);
        expect(serverProcess.exitCode).toBe(null);
    });

    it('should clean up properly on shutdown', async () => {
        // Send a test email
        const composedEmail = await client.composeEmail({
            recipients: 'shutdown-test@example.com',
            subject: 'Shutdown Test',
            body: 'This is a shutdown test',
            priority: 'medium'
        });

        // Stop the server
        serverProcess.kill();

        // Wait for process to exit
        await new Promise(resolve => serverProcess.on('exit', resolve));

        // Try to send another email (should fail)
        try {
            await client.sendEmail({ emailId: composedEmail.emailId, approval: true });
            expect(false).toBe(true); // Should not reach here
        } catch (error) {
            expect(error.message).toBeDefined();
            expect(error.message).toContain('Request failed');
        }
    });
});

// Helper functions for integration tests
function waitForServerOutput(searchText, timeout = 5000) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();

        serverProcess.stdout.on('data', (data) => {
            const output = data.toString();
            if (output.includes(searchText)) {
                resolve();
            }
        });

        // Timeout after specified time
        setTimeout(() => {
            reject(new Error(`Timeout waiting for server output: ${searchText}`));
        }, timeout);
    });
}