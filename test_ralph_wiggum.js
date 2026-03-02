// Test script for Ralph Wiggum Loop
// This script tests the Ralph Wiggum loop functionality

const { RalphWiggumLoop } = require('./ralph-wiggum-loop');

// Test configuration
const TEST_WORKING_DIRECTORY = 'C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier';
const TEST_PROMPT = `Implement a comprehensive email workflow system with the following requirements:

1. Create an MCP (Model Context Protocol) server that handles email composition, sending, and approval workflows
2. Implement file-based email storage with metadata tracking
3. Add file watching capabilities to detect email approvals
4. Create a robust logging system with Winston
5. Implement error handling and recovery mechanisms
6. Add support for email templates and categories
7. Create comprehensive test coverage

The system should be production-ready with proper error handling, logging, and monitoring capabilities.`;

// Main test function
async function testRalphWiggumLoop() {
    console.log('🧪 Testing Ralph Wiggum Loop...\n');

    try {
        const loop = new RalphWiggumLoop();

        // Start the loop
        await loop.startLoop(TEST_PROMPT, TEST_WORKING_DIRECTORY);

        console.log('\n🎉 Ralph Wiggum Loop test completed successfully!');

    } catch (error) {
        console.error('❌ Test failed:', error);
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    testRalphWiggumLoop();
}

module.exports = { testRalphWiggumLoop };