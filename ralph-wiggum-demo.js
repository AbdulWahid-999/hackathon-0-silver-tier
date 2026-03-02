// Ralph Wiggum Loop Demonstration
// This script demonstrates how the Ralph Wiggum loop works

const { RalphWiggumLoop } = require('./ralph-wiggum-loop');

// Example usage of Ralph Wiggum loop
async function demonstrateRalphWiggumLoop() {
    console.log('🎭 Ralph Wiggum Loop Demonstration 🎭');
    console.log('=====================================');

    // Create Ralph Wiggum loop instance
    const ralphWiggum = new RalphWiggumLoop();

    // Install exit hook
    ralphWiggum.installExitHook();
    console.log('✅ Exit hook installed');

    // Register example hooks
    ralphWiggum.registerHook('fileMonitor', require('./ralph-wiggum-loop').exampleHooks.fileMonitorHook);
    ralphWiggum.registerHook('processMonitor', require('./ralph-wiggum-loop').exampleHooks.processMonitorHook);
    ralphWiggum.registerHook('resourceMonitor', require('./ralph-wiggum-loop').exampleHooks.resourceMonitorHook);
    console.log('✅ Example hooks registered');

    // Define a sample task
    const taskId = 'demo-task-001';
    const samplePrompt = 'Create a simple text file in the current directory';
    const targetFiles = ['*.txt', 'task_completion_marker.json'];

    console.log(`
📝 Starting task: ${taskId}`);
    console.log(`📝 Prompt: ${samplePrompt}`);
    console.log(`📁 Target files: ${targetFiles.join(', ')}`);

    try {
        // Start the Ralph Wiggum loop
        const result = await ralphWiggum.startLoop(samplePrompt, process.cwd());

        console.log(`
✅ Ralph Wiggum loop completed: ${result}`);

        // Show statistics
        const stats = ralphWiggum.getStatistics();
        console.log('\n📊 Ralph Wiggum Statistics:');
        console.log(`   Total Tasks: ${stats.totalTasks}`);
        console.log(`   Pending Tasks: ${stats.pendingTasks}`);
        console.log(`   In Progress Tasks: ${stats.inProgressTasks}`);
        console.log(`   Completed Tasks: ${stats.completedTasks}`);
        console.log(`   Iterations: ${stats.iterations}/${stats.maxIterations}`);

        // Check for task completion
        const isCompleted = ralphWiggum.isTaskCompleted(taskId);
        console.log(`\n🔍 Task Completion Status: ${isCompleted ? 'Complete' : 'Incomplete'}`);

        if (isCompleted) {
            console.log('🎉 Task completed successfully!');
        } else {
            console.log('⚠️  Task did not complete within iteration limit');
        }

    } catch (error) {
        console.error('❌ Error in Ralph Wiggum loop:', error);
    }
}

// Alternative demonstration: Manual control
async function demonstrateManualControl() {
    console.log('\n🚀 Manual Control Demonstration');
    console.log('================================');

    const ralphWiggum = new RalphWiggumLoop();
    ralphWiggum.installExitHook();

    // Create a pending task
    const taskId = 'manual-task-001';
    const prompt = 'Generate a completion marker file';
    const targetFiles = ['completion_marker.txt'];

    ralphWiggum.addPendingTask(taskId, prompt, targetFiles);
    console.log(`✅ Added pending task: ${taskId}`);

    // Simulate task completion by creating the target file
    setTimeout(async () => {
        try {
            const fs = require('fs').promises;
            await fs.writeFile('completion_marker.txt', 'Task completed successfully');
            console.log('🎉 Created completion marker file');

            // Resolve the task completion
            ralphWiggum.resolveTaskCompletion(taskId, {
                success: true,
                message: 'Manual task completed via file creation'
            });
            console.log('✅ Task completion resolved');

            // Check status
            const status = ralphWiggum.getTaskStatus(taskId);
            console.log(`📋 Task status: ${status}`);

        } catch (error) {
            console.error('❌ Error in manual demonstration:', error);
        }
    }, 3000);

    // Wait and show status
    setTimeout(() => {
        const status = ralphWiggum.getTaskStatus(taskId);
        console.log(`📋 After 3 seconds, task status: ${status}`);
    }, 5000);
}

// Error handling demonstration
async function demonstrateErrorHandling() {
    console.log('\n🔧 Error Handling Demonstration');
    console.log('==================================');

    const ralphWiggum = new RalphWiggumLoop();
    ralphWiggum.installExitHook();

    const taskId = 'error-task-001';
    const prompt = 'Perform a task that will fail';
    const targetFiles = ['non_existent_file.txt'];

    console.log(`📝 Starting error-prone task: ${taskId}`);

    try {
        await ralphWiggum.startLoop(prompt, process.cwd());
    } catch (error) {
        console.log('✅ Error was caught as expected');
        console.log(`📋 Error message: ${error.message}`);
    }
}

// Run demonstrations
async function runAllDemonstrations() {
    console.log('🎭 Ralph Wiggum Loop - Complete Demonstration Suite 🎭\n');

    await demonstrateRalphWiggumLoop();
    console.log('\n' + '='.repeat(50) + '\n');

    await demonstrateManualControl();
    console.log('\n' + '='.repeat(50) + '\n');

    await demonstrateErrorHandling();
    console.log('\n' + '='.repeat(50) + '\n');

    console.log('🎉 All demonstrations completed!');
}

// Run if this file is executed directly
if (require.main === module) {
    runAllDemonstrations().catch(console.error);
}

module.exports = { demonstrateRalphWiggumLoop, demonstrateManualControl, demonstrateErrorHandling };