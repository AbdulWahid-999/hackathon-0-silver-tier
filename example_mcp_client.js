// Example MCP Client for Email Server
// This demonstrates how to interact with the MCP Email Server

const http = require('http');

// Configuration
const MCP_SERVER_URL = 'http://localhost:8080';

// Function to send MCP request
function sendMCPRequest(method, params) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify({ method, params });

        const options = {
            hostname: 'localhost',
            port: 8080,
            path: '/',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };

        const req = http.request(options, (res) => {
            let responseData = '';

            res.on('data', (chunk) => {
                responseData += chunk;
            });

            res.on('end', () => {
                try {
                    const parsedData = JSON.parse(responseData);
                    resolve(parsedData);
                } catch (error) {
                    reject(new Error('Failed to parse response: ' + error.message));
                }
            });
        });

        req.on('error', (error) => {
            reject(new Error('Request failed: ' + error.message));
        });

        req.write(postData);
        req.end();
    });
}

// Example usage
async function exampleUsage() {
    console.log('MCP Email Server Example Usage\n');

    try {
        // Example 1: Compose and send an email
        console.log('Example 1: Compose and send email');

        // Compose email
        const composeResult = await sendMCPRequest('compose-email', {
            recipients: 'recipient@example.com',
            subject: 'Welcome to Our Service',
            body: 'Dear Customer,\n\nThank you for signing up! We\'re excited to have you.\n\nBest regards,\nYour Company',
            priority: 'medium',
            category: 'welcome'
        });

        if (composeResult.success) {
            console.log('Email composed successfully');
            console.log('Email ID:', composeResult.result.emailId);

            // Send the email
            const sendResult = await sendMCPRequest('send-email', {
                emailId: composeResult.result.emailId
            });

            if (sendResult.success) {
                console.log('Email sent successfully');
            } else {
                console.log('Failed to send email:', sendResult.error);
            }
        } else {
            console.log('Failed to compose email:', composeResult.error);
        }

        // Example 2: Use email templates
        console.log('\nExample 2: Using email templates');

        const templates = await sendMCPRequest('get-email-templates', {
            category: 'general'
        });

        if (templates.success) {
            console.log('Available templates:');
            templates.result.forEach((template, index) => {
                console.log(`${index + 1}. ${template.name}`);
                console.log(`   Subject: ${template.subject}`);
                console.log(`   Preview: ${template.body.substring(0, 50)}...`);
                console.log('');
            });
        } else {
            console.log('Failed to get templates:', templates.error);
        }

        // Example 3: Check approval status
        console.log('\nExample 3: Checking approval status');

        // Create a test email first
        const testEmail = await sendMCPRequest('compose-email', {
            recipients: 'test@example.com',
            subject: 'Approval Test',
            body: 'This email is for approval testing.'
        });

        if (testEmail.success) {
            const statusResult = await sendMCPRequest('get-approval-status', {
                emailId: testEmail.result.emailId
            });

            if (statusResult.success) {
                console.log('Email status:', statusResult.result.status);
            } else {
                console.log('Failed to get status:', statusResult.error);
            }
        }

        // Example 4: List pending emails
        console.log('\nExample 4: Listing pending emails');

        const pendingResult = await sendMCPRequest('list-pending-emails');

        if (pendingResult.success) {
            console.log(`Found ${pendingResult.result.length} pending email(s)`);
            pendingResult.result.forEach((email, index) => {
                console.log(`${index + 1}. ${email.subject} (${email.recipients})`);
            });
        } else {
            console.log('Failed to list pending emails:', pendingResult.error);
        }

    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Run example if this file is executed directly
if (require.main === module) {
    exampleUsage();
}

module.exports = { sendMCPRequest, exampleUsage };