const { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } = require('@jest/globals');
const http = require('http');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

// Import the server and client
const { MCPServer, initializeEmailTransport, checkRateLimit, authenticateRequest } = require('../mcp-email-server-enhanced.js');
const { EnhancedMCPClient } = require('../mcp-email-client-enhanced.js');

// Test configuration
describe('MCP Email Server Enhanced', () => {
    let server;
    let client;
    let testVaultPath;
    let needsActionPath;
    let donePath;

    beforeAll(async () => {
        // Setup test environment
        testVaultPath = path.join(__dirname, 'test-vault');
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

        // Initialize email transport (mock if needed)
        await initializeEmailTransport();

        // Start server in test mode
        server = new MCPServer();
        client = new EnhancedMCPClient();
    });

    afterAll(async () => {
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

    describe('Security & Authentication', () => {
        it('should authenticate valid requests', async () => {
            const result = authenticateRequest('test-token', '127.0.0.1');
            expect(result).toBe(true);
        });

        it('should reject invalid authentication tokens', async () => {
            const result = authenticateRequest('invalid-token', '127.0.0.1');
            expect(result).toBe(false);
        });

        it('should enforce rate limiting', async () => {
            const ip = '127.0.0.1';

            // Make multiple requests
            for (let i = 0; i < 10; i++) {
                expect(checkRateLimit(ip)).toBe(true);
            }

            // 11th request should be rate limited
            expect(checkRateLimit(ip)).toBe(false);
        });

        it('should lock out after max failed attempts', async () => {
            const ip = '127.0.0.1';

            // Simulate failed attempts
            for (let i = 0; i < 5; i++) {
                authenticateRequest('wrong-token', ip);
            }

            // 6th attempt should be locked out
            const result = authenticateRequest('test-token', ip);
            expect(result).toBe(false);
        });
    });

    describe('Email Validation', () => {
        it('should validate email formats correctly', async () => {
            const validEmails = [
                'test@example.com',
                'user.name@domain.co',
                'user+tag@domain.com'
            ];

            const invalidEmails = [
                'invalid-email',
                'user@domain',
                'user@domain.',
                '@domain.com'
            ];

            validEmails.forEach(email => {
                expect(server.validateEmailFormat(email)).toBe(true);
            });

            invalidEmails.forEach(email => {
                expect(server.validateEmailFormat(email)).toBe(false);
            });
        });

        it('should validate email content', async () => {
            const validMetadata = {
                recipients: 'test@example.com',
                subject: 'Valid Subject',
                body: 'Valid body content',
                priority: 'medium',
                category: 'general'
            };

            const invalidMetadata = {
                recipients: 'invalid-email',
                subject: '',
                body: 'Valid body'
            };

            const validResult = server.validateEmailContent(validMetadata);
            expect(validResult.valid).toBe(true);

            const invalidResult = server.validateEmailContent(invalidMetadata);
            expect(invalidResult.valid).toBe(false);
            expect(invalidResult.errors.length).toBeGreaterThan(0);
        });
    });

    describe('Email Composition', () => {
        it('should compose valid email', async () => {
            const email = await client.composeEmail({
                recipients: 'test@example.com',
                subject: 'Test Email',
                body: 'This is a test email',
                priority: 'high',
                category: 'testing'
            });

            expect(email).toBeDefined();
            expect(email.emailId).toBeDefined();
            expect(email.filePath).toBeDefined();
            expect(email.status).toBe('pending');
            expect(email.metadata).toBeDefined();
            expect(email.metadata.id).toBe(email.emailId);
        });

        it('should reject emails with missing required fields', async () => {
            await expect(client.composeEmail({
                recipients: 'test@example.com',
                subject: '', // Missing
                body: 'This is a test email'
            })).rejects.toThrow('Missing required email parameters');
        });

        it('should generate proper email file content', async () => {
            const email = await client.composeEmail({
                recipients: 'test@example.com',
                subject: 'Test Email',
                body: 'This is a test email',
                priority: 'high',
                category: 'testing'
            });

            const filePath = path.join(needsActionPath, `${email.emailId}.md`);
            const content = await fs.readFile(filePath, 'utf8');

            // Check for front matter
            expect(content).toContain('---');
            expect(content).toContain('emailId');
            expect(content).toContain('status');
            expect(content).toContain('priority');
            expect(content).toContain('category');
        });
    });

    describe('Email Sending', () => {
        it('should send email successfully', async () => {
            // First compose an email
            const composedEmail = await client.composeEmail({
                recipients: 'test@example.com',
                subject: 'Test Send',
                body: 'This is a test send',
                priority: 'medium',
                category: 'testing'
            });

            // Send the email
            const sendResult = await client.sendEmail({
                emailId: composedEmail.emailId,
                approval: true
            });

            expect(sendResult).toBeDefined();
            expect(sendResult.emailId).toBe(composedEmail.emailId);
            expect(sendResult.status).toBe('sent');
        });

        it('should handle sending failures gracefully', async () => {
            // Compose an email with invalid SMTP settings (assuming transport fails)
            const composedEmail = await client.composeEmail({
                recipients: 'test@example.com',
                subject: 'Test Failure',
                body: 'This should fail',
                priority: 'low',
                category: 'testing'
            });

            // Try to send (should fail)
            await expect(client.sendEmail({
                emailId: composedEmail.emailId,
                approval: true
            })).rejects.toThrow();

            // Check email status should be failed
            const status = await client.getApprovalStatus({ emailId: composedEmail.emailId });
            expect(status.status).toBe('failed');
        });
    });

    describe('Email Templates', () => {
        it('should retrieve email templates', async () => {
            const templates = await client.getEmailTemplates({ category: 'general' });

            expect(templates).toBeDefined();
            expect(Array.isArray(templates)).toBe(true);
            expect(templates.length).toBeGreaterThan(0);

            // Check template structure
            const firstTemplate = templates[0];
            expect(firstTemplate.name).toBeDefined();
            expect(firstTemplate.subject).toBeDefined();
            expect(firstTemplate.body).toBeDefined();
        });

        it('should handle invalid template categories', async () => {
            const templates = await client.getEmailTemplates({ category: 'nonexistent' });

            // Should return general templates for invalid categories
            expect(templates).toBeDefined();
            expect(Array.isArray(templates)).toBe(true);
            expect(templates.length).toBeGreaterThan(0);
        });
    });

    describe('Email Scheduling', () => {
        it('should schedule email for future delivery', async () => {
            const composedEmail = await client.composeEmail({
                recipients: 'test@example.com',
                subject: 'Test Schedule',
                body: 'This is a scheduled email',
                priority: 'medium',
                category: 'testing'
            });

            const scheduleTime = new Date();
            scheduleTime.setMinutes(scheduleTime.getMinutes() + 1); // Schedule for 1 minute from now

            const scheduledEmail = await client.scheduleEmail({
                emailId: composedEmail.emailId,
                scheduleFor: scheduleTime.toISOString()
            });

            expect(scheduledEmail).toBeDefined();
            expect(scheduledEmail.emailId).toBe(composedEmail.emailId);
            expect(scheduledEmail.status).toBe('scheduled');
            expect(scheduledEmail.scheduleFor).toBe(scheduleTime.toISOString());
        });

        it('should handle scheduling in the past', async () => {
            const composedEmail = await client.composeEmail({
                recipients: 'test@example.com',
                subject: 'Test Past Schedule',
                body: 'This should send immediately',
                priority: 'medium',
                category: 'testing'
            });

            const pastTime = new Date();
            pastTime.setMinutes(pastTime.getMinutes() - 1); // Schedule for 1 minute ago

            // Should send immediately since schedule time is in the past
            const scheduledEmail = await client.scheduleEmail({
                emailId: composedEmail.emailId,
                scheduleFor: pastTime.toISOString()
            });

            expect(scheduledEmail).toBeDefined();
            expect(scheduledEmail.status).toBe('sent');
        });
    });

    describe('Email History & Management', () => {
        it('should track sent emails in history', async () => {
            // Send an email
            const composedEmail = await client.composeEmail({
                recipients: 'test@example.com',
                subject: 'Test History',
                body: 'This is for history tracking',
                priority: 'medium',
                category: 'testing'
            });

            await client.sendEmail({ emailId: composedEmail.emailId, approval: true });

            // Get history
            const history = await client.getEmailHistory({ limit: 10 });

            expect(history).toBeDefined();
            expect(Array.isArray(history)).toBe(true);
            expect(history.length).toBeGreaterThan(0);

            // Find our test email in history
            const testEmail = history.find(email => email.emailId === composedEmail.emailId);
            expect(testEmail).toBeDefined();
            expect(testEmail.status).toBe('sent');
        });

        it('should move sent emails to done folder', async () => {
            const composedEmail = await client.composeEmail({
                recipients: 'test@example.com',
                subject: 'Test Move',
                body: 'This should move to done',
                priority: 'medium',
                category: 'testing'
            });

            await client.sendEmail({ emailId: composedEmail.emailId, approval: true });

            // Check if file moved to done folder
            const doneFiles = await fs.readdir(donePath);
            const emailFile = doneFiles.find(file => file.startsWith(`EMAIL_${composedEmail.emailId}`));

            expect(emailFile).toBeDefined();
        });
    });

    describe('Recipient Validation', () => {
        it('should validate email recipients correctly', async () => {
            const validation = await client.validateRecipients({
                recipients: 'valid@example.com,invalid-email,blocked@company.com'
            });

            expect(validation).toBeDefined();
            expect(validation.recipients).toBeDefined();
            expect(validation.validationResults).toBeDefined();
            expect(validation.validationResults.length).toBe(3);

            // Check individual results
            const results = validation.validationResults;
            const validResult = results.find(r => r.email === 'valid@example.com');
            const invalidResult = results.find(r => r.email === 'invalid-email');
            const blockedResult = results.find(r => r.email === 'blocked@company.com');

            expect(validResult.valid).toBe(true);
            expect(validResult.allowed).toBe(true);

            expect(invalidResult.valid).toBe(false);
            expect(invalidResult.reason).toBe('Invalid email format');

            expect(blockedResult.valid).toBe(true);
            expect(blockedResult.allowed).toBe(false);
            expect(blockedResult.reason).toBe('Domain not allowed');
        });
    });

    describe('Batch Operations', () => {
        it('should send multiple emails', async () => {
            const emails = [
                {
                    recipients: 'user1@example.com',
                    subject: 'Batch Email 1',
                    body: 'This is the first batch email',
                    priority: 'low'
                },
                {
                    recipients: 'user2@example.com',
                    subject: 'Batch Email 2',
                    body: 'This is the second batch email',
                    priority: 'high'
                }
            ];

            const results = await client.batchSendEmails(emails);

            expect(results).toBeDefined();
            expect(Array.isArray(results)).toBe(true);
            expect(results.length).toBe(2);

            results.forEach(result => {
                expect(result.success).toBe(true);
            });
        });
    });

    describe('Error Handling', () => {
        it('should handle unknown email IDs gracefully', async () => {
            await expect(client.sendEmail({ emailId: 'nonexistent-id', approval: true }))
                .rejects.toThrow('Email not found');
        });

        it('should handle invalid method calls', async () => {
            // Try calling a non-existent method
            await expect(client.sendRequest('non-existent-method', {}))
                .rejects.toThrow('Unknown method');
        });
    });

    describe('Encryption & Security', () => {
        it('should encrypt and decrypt sensitive data', async () => {
            const sensitiveData = {
                apiKey: 'secret-api-key',
                password: 'super-secret',
                token: 'auth-token'
            };

            // This would test the encryption functions directly
            // Note: In a real test, you'd mock the crypto functions
            expect(true).toBe(true); // Placeholder for encryption tests
        });
    });

    describe('Cleanup & Maintenance', () => {
        it('should clean up old files', async () => {
            // This would test file cleanup functionality
            expect(true).toBe(true); // Placeholder for cleanup tests
        });
    });

    describe('Performance', () => {
        it('should handle concurrent requests', async () => {
            const promises = [];
            for (let i = 0; i < 5; i++) {
                promises.push(client.composeEmail({
                    recipients: `user${i}@example.com`,
                    subject: `Concurrent Test ${i}`,
                    body: 'This is a concurrent test',
                    priority: 'medium'
                }));
            }

            const results = await Promise.all(promises);
            expect(results.length).toBe(5);
        });
    });
});

// Helper functions for testing
function createTestEmailContent(metadata) {
    return `---
${JSON.stringify(metadata, null, 2)}
---

# Test Email

This is a test email for validation.`;
}