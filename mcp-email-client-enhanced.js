// Enhanced MCP Email Client for Silver Tier Functional Assistant
// This client provides secure, robust interaction with the Enhanced MCP Email Server

const http = require('http');
const crypto = require('crypto');

// Configuration
const MCP_SERVER_URL = 'http://localhost:8081';
const AUTH_TOKEN = process.env.MCP_AUTH_TOKEN || 'change-this-token-in-production';
const CLIENT_IP = process.env.CLIENT_IP || '127.0.0.1';

// Helper functions
function generateRequestSignature(method, params) {
    const hmac = crypto.createHmac('sha256', AUTH_TOKEN);
    const payload = JSON.stringify({ method, params });
    return hmac.update(payload).digest('hex');
}

// Enhanced MCP Client Class
class EnhancedMCPClient {
    constructor() {
        this.requestId = 0;
        this.activeRequests = new Map();
        this.rateLimitReset = new Map();
    }

    async sendRequest(method, params = {}) {
        this.requestId++;
        const requestId = this.requestId;

        // Rate limiting check
        if (!this.checkRateLimit()) {
            throw new Error('Rate limit exceeded. Please try again later.');
        }

        const requestData = {
            method,
            params,
            authToken: AUTH_TOKEN,
            ipAddress: CLIENT_IP,
            requestId,
            timestamp: Date.now()
        };

        const postData = JSON.stringify(requestData);

        const options = {
            hostname: 'localhost',
            port: 8081,
            path: '/',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData),
                'X-Request-ID': requestId,
                'X-Client-IP': CLIENT_IP
            }
        };

        return new Promise((resolve, reject) => {
            const req = http.request(options, (res) => {
                let responseData = '';

                res.on('data', (chunk) => {
                    responseData += chunk;
                });

                res.on('end', () => {
                    try {
                        const parsedData = JSON.parse(responseData);
                        this.activeRequests.delete(requestId);

                        if (parsedData.success) {
                            resolve(parsedData.result);
                        } else {
                            reject(new Error(parsedData.error || 'Request failed'));
                        }
                    } catch (error) {
                        this.activeRequests.delete(requestId);
                        reject(new Error('Failed to parse response: ' + error.message));
                    }
                });
            });

            req.on('error', (error) => {
                this.activeRequests.delete(requestId);
                reject(new Error('Request failed: ' + error.message));
            });

            req.setTimeout(30000, () => {
                req.destroy();
                this.activeRequests.delete(requestId);
                reject(new Error('Request timeout'));
            });

            req.write(postData);
            req.end();

            // Track active request
            this.activeRequests.set(requestId, { method, startTime: Date.now() });
        });
    }

    checkRateLimit() {
        const now = Date.now();
        const requests = this.activeRequests.values();
        const recentRequests = Array.from(requests).filter(req => now - req.startTime < 60000);

        return recentRequests.length < 10; // 10 requests per minute
    }

    async composeEmail(params) {
        return await this.sendRequest('compose-email', params);
    }

    async sendEmail(params) {
        return await this.sendRequest('send-email', params);
    }

    async getEmailTemplates(params) {
        return await this.sendRequest('get-email-templates', params);
    }

    async getApprovalStatus(params) {
        return await this.sendRequest('get-approval-status', params);
    }

    async listPendingEmails() {
        return await this.sendRequest('list-pending-emails');
    }

    async resendEmail(params) {
        return await this.sendRequest('resend-email', params);
    }

    async scheduleEmail(params) {
        return await this.sendRequest('schedule-email', params);
    }

    async cancelScheduledEmail(params) {
        return await this.sendRequest('cancel-scheduled-email', params);
    }

    async getEmailHistory(params) {
        return await this.sendRequest('get-email-history', params);
    }

    async validateRecipients(params) {
        return await this.sendRequest('validate-email-recipients', params);
    }

    async testConnection() {
        return await this.sendRequest('test-email-connection');
    }

    async batchSendEmails(emails) {
        const results = [];

        for (const emailData of emails) {
            try {
                const result = await this.sendEmail(emailData);
                results.push({ success: true, result });
            } catch (error) {
                results.push({ success: false, error: error.message });
            }
        }

        return results;
    }

    async getServerStatus() {
        // This would be implemented as a custom method on the server
        try {
            // Try to get metrics or health info
            // This is a placeholder for a real implementation
            return {
                connected: true,
                timestamp: Date.now(),
                activeRequests: this.activeRequests.size,
                rateLimit: this.checkRateLimit()
            };
        } catch (error) {
            return {
                connected: false,
                error: error.message
            };
        }
    }

    async retryFailedEmails(failedEmails, maxRetries = 3) {
        const results = [];

        for (const email of failedEmails) {
            for (let attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    const result = await this.sendEmail({
                        emailId: email.emailId,
                        approval: true
                    });
                    results.push({ emailId: email.emailId, success: true, attempt });
                    break;
                } catch (error) {
                    if (attempt === maxRetries) {
                        results.push({ emailId: email.emailId, success: false, error: error.message, attempts: attempt });
                    }
                    // Exponential backoff
                    await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt)));
                }
            }
        }

        return results;
    }

    async generateEmailReport(startDate, endDate, status = 'all') {
        const history = await this.getEmailHistory({ limit: 1000 });

        const filtered = history.filter(email => {
            const emailDate = new Date(email.sent_at || email.created_at).getTime();
            return emailDate >= startDate && emailDate <= endDate &&
                   (status === 'all' || email.status === status);
        });

        const report = {
            total: filtered.length,
            byStatus: {},
            byCategory: {},
            byPriority: {},
            averageProcessingTime: 0
        };

        for (const email of filtered) {
            report.byStatus[email.status] = (report.byStatus[email.status] || 0) + 1;
            report.byCategory[email.category] = (report.byCategory[email.category] || 0) + 1;
            report.byPriority[email.priority] = (report.byPriority[email.priority] || 0) + 1;
        }

        return report;
    }
}

// Enhanced example usage
async function enhancedExampleUsage() {
    console.log('🚀 Enhanced MCP Email Client Example Usage\n');

    const client = new EnhancedMCPClient();

    try {
        // Example 1: Test connection
        console.log('🔍 Example 1: Testing email server connection');
        const connectionTest = await client.testConnection();
        if (connectionTest.success) {
            console.log('✅ Connection successful:', connectionTest.message);
        } else {
            console.log('❌ Connection failed:', connectionTest.error);
        }

        // Example 2: Validate recipients
        console.log('\n🔗 Example 2: Validating email recipients');
        const validationResult = await client.validateRecipients({
            recipients: 'valid@example.com,invalid-email,blocked@company.com'
        });

        console.log('✅ Validation results:');
        validationResult.validationResults.forEach(result => {
            console.log(`   ${result.email}: ${result.valid ? '✅ Valid' : '❌ Invalid'} (${result.reason})`);
        });

        // Example 3: Get email templates
        console.log('\n📝 Example 3: Getting email templates');
        const templates = await client.getEmailTemplates({ category: 'general' });

        console.log('✅ Available templates:');
        templates.forEach((template, index) => {
            console.log(`   ${index + 1}. ${template.name}`);
            console.log(`      Subject: ${template.subject}`);
            console.log(`      Preview: ${template.body.substring(0, 60)}...`);
            console.log('');
        });

        // Example 4: Compose and send email with approval
        console.log('\n📧 Example 4: Composing and sending email with approval');

        const composedEmail = await client.composeEmail({
            recipients: 'test@example.com',
            subject: 'Enhanced Email Test',
            body: 'This is a test email using the enhanced MCP Email Client.\n\nFeatures tested:\n- Secure authentication\n- Rate limiting\n- Template usage\n- Error handling\n\nTimestamp: ' + new Date().toISOString(),
            priority: 'high',
            category: 'testing',
            attachments: []
        });

        if (composedEmail) {
            console.log('✅ Email composed successfully');
            console.log('   Email ID:', composedEmail.emailId);
            console.log('   File Path:', composedEmail.filePath);

            // Get approval status
            const status = await client.getApprovalStatus({ emailId: composedEmail.emailId });
            console.log('   Initial status:', status.status);

            // Send the email
            const sendResult = await client.sendEmail({
                emailId: composedEmail.emailId,
                approval: true
            });

            if (sendResult) {
                console.log('✅ Email sent successfully');
                console.log('   Status:', sendResult.status);
            } else {
                console.log('❌ Failed to send email');
            }
        }

        // Example 5: Schedule an email
        console.log('\n🕐 Example 5: Scheduling an email');

        const scheduleTime = new Date();
        scheduleTime.setMinutes(scheduleTime.getMinutes() + 2); // Schedule for 2 minutes from now

        const scheduledEmail = await client.scheduleEmail({
            emailId: composedEmail.emailId,
            scheduleFor: scheduleTime.toISOString()
        });

        if (scheduledEmail) {
            console.log('✅ Email scheduled successfully');
            console.log('   Scheduled for:', scheduledEmail.scheduleFor);
        }

        // Example 6: List pending emails
        console.log('\n📋 Example 6: Listing pending emails');

        const pendingEmails = await client.listPendingEmails();
        console.log(`✅ Found ${pendingEmails.length} pending email(s)`);
        pendingEmails.forEach((email, index) => {
            console.log(`   ${index + 1}. ${email.subject} (${email.recipients}) - Priority: ${email.priority}`);
        });

        // Example 7: Generate email report
        console.log('\n📊 Example 7: Generating email report');

        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 7); // Last 7 days
        const endDate = new Date();

        const report = await client.generateEmailReport(startDate.getTime(), endDate.getTime());
        console.log('✅ Email report generated:');
        console.log(`   Total emails: ${report.total}`);
        console.log('   By status:', JSON.stringify(report.byStatus, null, 2));
        console.log('   By category:', JSON.stringify(report.byCategory, null, 2));
        console.log('   By priority:', JSON.stringify(report.byPriority, null, 2));

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

// Run enhanced example if this file is executed directly
if (require.main === module) {
    enhancedExampleUsage();
}

module.exports = {
    EnhancedMCPClient,
    enhancedExampleUsage,
    generateRequestSignature
};