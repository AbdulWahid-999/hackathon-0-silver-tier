// Ralph Wiggum Loop Integration Example
// Demonstrates how to integrate the Ralph Wiggum loop with existing workflows

const { RalphWiggumLoop } = require('./ralph-wiggum-loop');

// Example task function
async function exampleTask(prompt) {
    console.log('🚀 Executing example task...');
    console.log('📝 Prompt:', prompt);

    // Simulate some work
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Create a completion marker file
    const fs = require('fs').promises;
    const path = require('path');
    const markerPath = path.join(process.cwd(), 'task_complete_marker.txt');

    await fs.writeFile(markerPath, 'complete', 'utf8');
    console.log('✅ Created completion marker:', markerPath);

    return { success: true, message: 'Task completed' };
}

// Example completion check function
async function exampleCompletionCheck() {
    const fs = require('fs').promises;
    const path = require('path');
    const markerPath = path.join(process.cwd(), 'task_complete_marker.txt');

    try {
        await fs.access(markerPath);
        const content = await fs.readFile(markerPath, 'utf8');
        return content.trim().toLowerCase() === 'complete';
    } catch {
        return false;
    }
}

// Example task configuration
const taskConfig = {
    description: 'Test Ralph Wiggum Loop Integration',
    execute: () => exampleTask('This is a test task for Ralph Wiggum loop'),
    completionCheck: exampleCompletionCheck
};

// Main integration function
async function integrateRalphWiggumLoop() {
    console.log('🔧 Starting Ralph Wiggum Loop Integration...');

    try {
        const loop = new RalphWiggumLoop();

        // Track files for completion detection
        loop.trackFiles([
            'task_complete_marker.txt',
            'mcp-email-server.log',
            'EMAIL_*.md',
            'task_status.json'
        ]);

        // Start the loop with task configuration
        await loop.startLoop({
            description: taskConfig.description,
            execute: taskConfig.execute,
            completionCheck: taskConfig.completionCheck
        });

        console.log('✅ Integration complete!');
        return true;

    } catch (error) {
        console.error('❌ Integration failed:', error.message);
        return false;
    }
}

// Test the integration
async function testIntegration() {
    console.log('🧪 Testing Ralph Wiggum Loop Integration...');

    try {
        // Clean up any existing markers
        await cleanupMarkers();

        // Run integration test
        const success = await integrateRalphWiggumLoop();

        if (success) {
            console.log('🎉 Test passed!');
        } else {
            console.log('❌ Test failed.');
        }

        return success;

    } catch (error) {
        console.error('❌ Test error:', error.message);
        return false;
    }
}

// Cleanup function
async function cleanupMarkers() {
    const fs = require('fs').promises;
    const path = require('path');

    const markerFiles = [
        'task_complete_marker.txt',
        'task_marker_*.json',
        'task_completion_marker.json'
    ];

    for (const pattern of markerFiles) {
        const files = await fs.readdir(process.cwd());
        for (const file of files) {
            if (file.match(pattern.replace('*', '.*'))) {
                try {
                    await fs.unlink(path.join(process.cwd(), file));
                    console.log('🗑️  Cleaned up:', file);
                } catch (error) {
                    console.error('❌ Failed to clean up:', file, error.message);
                }
            }
        }
    }
}

// Run test if this file is executed directly
if (require.main === module) {
    testIntegration().then(success => {
        process.exit(success ? 0 : 1);
    });
}

module.exports = {
    RalphWiggumLoop,
    integrateRalphWiggumLoop,
    testIntegration,
    cleanupMarkers
};