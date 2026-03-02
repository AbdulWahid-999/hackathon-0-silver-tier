#!/bin/bash

# Integration Test Script for Ralph Wiggum Loop with MCP Email Server

echo "🚀 Starting Ralph Wiggum Loop Integration Test..."

# Navigate to the Silver Tier directory
cd "C:/Users/goku/MyWebsiteProjects/hackathon-0/Silver-Tier"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Run the integration test
echo "🧪 Running integration test..."
node integration_example.js

echo "✅ Integration test completed!"
