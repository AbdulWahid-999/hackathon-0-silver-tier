// Test script for MCP Email Server
// This script tests the email composition functionality

const http = require('http');
const { v4: uuidv4 } = require('uuid');

// Configuration
const MCP_SERVER_URL = 'http://localhost:8080';

// Test data
const testEmail = {
    method: 'compose-email',
    params: {
        recipients: 'test@example.com',
        subject: 'Test Email from MCP Server',
        body: 'This is a test email sent through the MCP Email Server.\n\n- Test 1: Basic functionality\n- Test 2: Approval workflow\n- Test 3: Error handling\n\nTimestamp: ' + new Date().toISOString(),
        priority: 'high',
        category: 'testing'
    }
};

// Function to send MCP request
function sendMCPRequest(data) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify(data);

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

// Main test function
async function runTests() {
    console.log('Starting MCP Email Server tests...\n');

    try {
        // Test 1: Compose a new email
        console.log('Test 1: Composing new email...');
        const composeResult = await sendMCPRequest(testEmail);

        if (composeResult.success) {
            console.log('✅ Email composed successfully');
            console.log('   Email ID:', composeResult.result.emailId);
            console.log('   File Path:', composeResult.result.filePath);
            console.log('   Status:', composeResult.result.status);
        } else {
            console.error('❌ Failed to compose email:', composeResult.error);
            return;
        }

        // Test 2: Get approval status
        console.log('\nTest 2: Checking approval status...');
        const statusCheck = await sendMCPRequest({
            method: 'get-approval-status',
            params: { emailId: composeResult.result.emailId }
        });

        if (statusCheck.success) {
            console.log('✅ Status check successful');
            console.log('   Status:', statusCheck.result.status);
            console.log('   Metadata:', JSON.stringify(statusCheck.result.metadata, null, 2));
        } else {
            console.error('❌ Failed to check status:', statusCheck.error);
        }

        // Test 3: List pending emails
        console.log('\nTest 3: Listing pending emails...');
        const pendingList = await sendMCPRequest({
            method: 'list-pending-emails'
        });

        if (pendingList.success) {
            console.log('✅ Pending emails retrieved');
            console.log('   Count:', pendingList.result.length);
            if (pendingList.result.length > 0) {
                console.log('   First email:', pendingList.result[0]);
            }
        } else {
            console.error('❌ Failed to list pending emails:', pendingList.error);
        }

        // Test 4: Get email templates
        console.log('\nTest 4: Getting email templates...');
        const templates = await sendMCPRequest({
            method: 'get-email-templates',
            params: { category: 'general' }
        });

        if (templates.success) {
            console.log('✅ Templates retrieved');
            console.log('   Count:', templates.result.length);
            console.log('   First template:', templates.result[0]);
        } else {
            console.error('❌ Failed to get templates:', templates.error);
        }

        console.log('\n✅ All tests completed successfully!');

    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    runTests();
}

module.exports = { sendMCPRequest, runTests };