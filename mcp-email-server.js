// MCP Email Server for Silver Tier Functional Assistant
// This server implements email composition, sending, and approval workflow integration

const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { v4: uuidv4 } = require('uuid');
const nodemailer = require('nodemailer');
const { createLogger, transports, format } = require('winston');
const { RalphWiggumLoop } = require('./ralph-wiggum-loop');

// Configuration
const config = require('./config.json');
const VAULT_PATH = process.env.VAULT_PATH || 'C:\\Users\\goku\\MyWebsiteProjects\\hackathon-0\\Silver-Tier\\AI_Silver_Employee_Vault';
const NEEDS_ACTION_PATH = path.join(VAULT_PATH, 'Needs_Action');
const DONE_PATH = path.join(VAULT_PATH, 'Done');
const LOG_PATH = 'mcp-email-server.log';

// Logger setup
const logger = createLogger({
    level: config.logging?.level || 'INFO',
    format: format.combine(
        format.timestamp(),
        format.errors({ stack: true }),
        format.json()
    ),
    defaultMeta: { service: 'mcp-email-server' },
    transports: [
        new transports.File({ filename: LOG_PATH, maxsize: 5242880, maxFiles: 5 }),
        new transports.Console({ format: format.simple() })
    ]
});

// Email Transport Configuration
let emailTransport = null;
let emailConfig = {
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
        user: config.email?.smtp?.user || process.env.EMAIL_USER,
        pass: config.email?.smtp?.pass || process.env.EMAIL_PASS
    }
};

// Initialize nodemailer transport
async function initializeEmailTransport() {
    try {
        emailTransport = nodemailer.createTransport(emailConfig);
        const test = await emailTransport.verify();
        logger.info('Email transport initialized successfully');
        return true;
    } catch (error) {
        logger.error('Failed to initialize email transport:', error);
        return false;
    }
}

// MCP Server Class
class MCPServer {
    constructor() {
        this.handlers = new Map();
        this.initializeHandlers();
        this.initializeEmailWorkflow();
    }

    initializeHandlers() {
        // MCP Tool Handlers
        this.handlers.set('compose-email', this.composeEmail.bind(this));
        this.handlers.set('send-email', this.sendEmail.bind(this));
        this.handlers.set('get-email-templates', this.getEmailTemplates.bind(this));
        this.handlers.set('get-approval-status', this.getApprovalStatus.bind(this));
        this.handlers.set('list-pending-emails', this.listPendingEmails.bind(this));
        this.handlers.set('resend-email', this.resendEmail.bind(this));
    }

    async startRalphWiggumLoop(taskId, taskConfig) {
        try {
            await this.ralphWiggum.startLoop(
                taskConfig.prompt,
                process.cwd()
            );
            logger.info(`Ralph Wiggum loop started for task: ${taskId}`);
            return true;
        } catch (error) {
            logger.error(`Failed to start Ralph Wiggum loop for task ${taskId}:`, error);
            return false;
        }
    }

    setupFileWatcher() {
        const chokidar = require('chokidar');

        const watcher = chokidar.watch(NEEDS_ACTION_PATH, {
            persistent: true,
            ignoreInitial: true
        });

        watcher.on('add', async (filePath) => {
            try {
                await this.processNewEmailFile(filePath);
            } catch (error) {
                logger.error('Error processing new email file:', error);
            }
        });

        watcher.on('change', async (filePath) => {
            try {
                await this.processUpdatedEmailFile(filePath);
            } catch (error) {
                logger.error('Error processing updated email file:', error);
            }
        });

        logger.info('File watcher set up for email approvals');
    }

    async processNewEmailFile(filePath) {
        const fileName = path.basename(filePath);

        if (!fileName.startsWith('EMAIL_') || !fileName.endsWith('.md')) {
            return;
        }

        try {
            const content = await fs.readFile(filePath, 'utf8');
            const metadata = this.extractMetadata(content);

            if (metadata && metadata.status === 'pending') {
                logger.info(`New email pending approval: ${fileName}`);
                // Add to pending queue or notify system
            }
        } catch (error) {
            logger.error(`Error reading new email file ${fileName}:`, error);
        }
    }

    async processUpdatedEmailFile(filePath) {
        const fileName = path.basename(filePath);

        if (!fileName.startsWith('EMAIL_') || !fileName.endsWith('.md')) {
            return;
        }

        try {
            const content = await fs.readFile(filePath, 'utf8');
            const metadata = this.extractMetadata(content);

            if (metadata && metadata.status === 'approved') {
                logger.info(`Email approved: ${fileName}`);
                await this.sendEmailFromFile(filePath);
            }
        } catch (error) {
            logger.error(`Error processing updated email file ${fileName}:`, error);
        }
    }

    extractMetadata(content) {
        const frontMatterRegex = /^---$(.*?)^---$/s;
        const match = content.match(frontMatterRegex);

        if (match) {
            try {
                return JSON.parse(match[1].trim());
            } catch (error) {
                logger.error('Error parsing metadata:', error);
            }
        }
        return null;
    }

    async sendEmailFromFile(filePath) {
        try {
            const content = await fs.readFile(filePath, 'utf8');
            const metadata = this.extractMetadata(content);

            if (!metadata || !metadata.recipients || !metadata.subject || !metadata.body) {
                logger.error('Email file missing required fields');
                return;
            }

            const emailData = {
                from: metadata.from || config.email?.smtp?.user,
                to: metadata.recipients,
                subject: metadata.subject,
                text: metadata.body,
                html: metadata.htmlBody || null
            };

            if (emailTransport) {
                const info = await emailTransport.sendMail(emailData);
                logger.info(`Email sent: ${info.messageId}`);

                // Move to done folder
                await this.moveToDone(filePath, metadata);
            } else {
                logger.error('Email transport not initialized');
            }
        } catch (error) {
            logger.error('Error sending email from file:', error);
            // Update file with error status
            await this.updateEmailStatus(filePath, 'failed', error.message);
        }
    }

    async moveToDone(filePath, metadata) {
        const fileName = path.basename(filePath);
        const newFilePath = path.join(DONE_PATH, fileName);

        try {
            await fs.rename(filePath, newFilePath);
            metadata.status = 'sent';
            metadata.sent_at = new Date().toISOString();

            // Update the file with sent status
            const content = await fs.readFile(newFilePath, 'utf8');
            const updatedContent = this.updateMetadataInContent(content, metadata);
            await fs.writeFile(newFilePath, updatedContent, 'utf8');

            logger.info(`Moved email to done: ${fileName}`);
        } catch (error) {
            logger.error('Error moving file to done:', error);
        }
    }

    updateMetadataInContent(content, metadata) {
        const frontMatterRegex = /^---$(.*?)^---$/s;
        return content.replace(frontMatterRegex, (_, frontMatter) => {
            const updatedFrontMatter = JSON.stringify(metadata, null, 2);
            return `---\n${updatedFrontMatter}\n---`;
        });
    }

    async updateEmailStatus(filePath, status, error = null) {
        try {
            const content = await fs.readFile(filePath, 'utf8');
            const metadata = this.extractMetadata(content) || {};

            metadata.status = status;
            if (error) {
                metadata.error = error;
            }

            const updatedContent = this.updateMetadataInContent(content, metadata);
            await fs.writeFile(filePath, updatedContent, 'utf8');

            logger.info(`Updated email status to ${status}: ${path.basename(filePath)}`);
        } catch (error) {
            logger.error('Error updating email status:', error);
        }
    }

    async handleRequest(method, params) {
        const handler = this.handlers.get(method);

        if (!handler) {
            throw new Error(`Unknown method: ${method}`);
        }

        try {
            const result = await handler(params);
            return { success: true, result };
        } catch (error) {
            logger.error(`Error handling ${method}:`, error);
            return { success: false, error: error.message };
        }
    }

    // MCP Tool Implementations
    async composeEmail(params) {
        const {
            recipients,
            subject,
            body,
            htmlBody,
            from,
            priority = 'medium',
            category = 'general'
        } = params;

        if (!recipients || !subject || !body) {
            throw new Error('Missing required email parameters: recipients, subject, and body are required');
        }

        const emailId = `EMAIL_${uuidv4()}`;
        const timestamp = new Date().toISOString();
        const fileName = `${emailId}.md`;
        const filePath = path.join(NEEDS_ACTION_PATH, fileName);

        const metadata = {
            id: emailId,
            type: 'email',
            status: 'pending',
            priority,
            category,
            created_at: timestamp,
            from: from || config.email?.smtp?.user,
            recipients,
            subject,
            body,
            htmlBody: htmlBody || null,
            attachments: params.attachments || []
        };

        const content = this.generateEmailFileContent(metadata);

        await fs.writeFile(filePath, content, 'utf8');
        logger.info(`Composed new email: ${fileName}`);

        // Start Ralph Wiggum loop for this task
        await this.startRalphWiggumLoop(emailId, {
            prompt: `Compose and send email with recipients: ${recipients}, subject: ${subject}`,
            targetFiles: [`${NEEDS_ACTION_PATH}\EMAIL_${emailId}*.md`],
            maxIterations: 10
        });

        return {
            emailId,
            filePath,
            status: 'pending',
            metadata
        };
    }

    generateEmailFileContent(metadata) {
        const frontMatter = JSON.stringify(metadata, null, 2);

        return `---
${frontMatter}
---

# Email Composition

## Email Details

**From:** ${metadata.from}
**To:** ${metadata.recipients}
**Subject:** ${metadata.subject}

## Email Body

${metadata.body}

## Processing Notes

- Email composed at: ${metadata.created_at}
- Priority: ${metadata.priority}
- Category: ${metadata.category}
- Status: ${metadata.status}
`;
    }

    async sendEmail(params) {
        const { emailId, approval = false } = params;

        if (!emailId) {
            throw new Error('Email ID is required to send email');
        }

        const emailFilePattern = `EMAIL_${emailId}.md`;
        const files = await fs.readdir(NEEDS_ACTION_PATH);
        const matchingFiles = files.filter(file => file.startsWith(`EMAIL_${emailId}`));

        if (matchingFiles.length === 0) {
            throw new Error(`Email not found: ${emailId}`);
        }

        const emailFilePath = path.join(NEEDS_ACTION_PATH, matchingFiles[0]);
        const content = await fs.readFile(emailFilePath, 'utf8');
        const metadata = this.extractMetadata(content);

        if (!metadata) {
            throw new Error('Invalid email file format');
        }

        if (!approval && metadata.status === 'pending') {
            // For non-approved sends, update status to 'approved' and send
            metadata.status = 'approved';
            const updatedContent = this.updateMetadataInContent(content, metadata);
            await fs.writeFile(emailFilePath, updatedContent, 'utf8');
            logger.info(`Email ${emailId} automatically approved for sending`);
        }

        // Send the email
        await this.sendEmailFromFile(emailFilePath);

        // Start Ralph Wiggum loop for task completion monitoring
        await this.startRalphWiggumLoop(emailId, {
            prompt: `Send email with ID: ${emailId} and monitor completion`,
            targetFiles: [`${DONE_PATH}\EMAIL_${emailId}*.md`],
            maxIterations: 10
        });

        return {
            emailId,
            status: 'sent',
            message: `Email ${emailId} sent successfully`
        };
    }

    async getEmailTemplates(params) {
        const { category = 'general' } = params;

        const templates = {
            general: [
                {
                    name: 'Welcome Email',
                    subject: 'Welcome to {company}!',
                    body: 'Dear {name},\n\nWelcome to {company}! We\'re excited to have you on board. Here\'s what you need to know to get started...'
                },
                {
                    name: 'Follow-up Email',
                    subject: 'Following up on our conversation',
                    body: 'Hi {name},\n\nJust wanted to follow up on our recent conversation about {topic}. I\'d love to hear your thoughts...'
                }
            ],
            business: [
                {
                    name: 'Sales Pitch',
                    subject: 'Transform your {industry} business with {product}',
                    body: 'Dear {name},\n\nAre you looking to improve your {industry} business? Our {product} can help you achieve {benefit}...'
                }
            ]
        };

        return templates[category] || templates.general;
    }

    async getApprovalStatus(params) {
        const { emailId } = params;

        if (!emailId) {
            throw new Error('Email ID is required to check approval status');
        }

        const emailFilePattern = `EMAIL_${emailId}.md`;
        const files = await fs.readdir(NEEDS_ACTION_PATH);
        const matchingFiles = files.filter(file => file.startsWith(`EMAIL_${emailId}`));

        if (matchingFiles.length === 0) {
            throw new Error(`Email not found: ${emailId}`);
        }

        const emailFilePath = path.join(NEEDS_ACTION_PATH, matchingFiles[0]);
        const content = await fs.readFile(emailFilePath, 'utf8');
        const metadata = this.extractMetadata(content);

        return {
            emailId,
            status: metadata?.status || 'unknown',
            filePath: emailFilePath,
            metadata
        };
    }

    async listPendingEmails() {
        const files = await fs.readdir(NEEDS_ACTION_PATH);
        const emailFiles = files.filter(file => file.startsWith('EMAIL_') && file.endsWith('.md'));

        const pendingEmails = [];

        for (const file of emailFiles) {
            const filePath = path.join(NEEDS_ACTION_PATH, file);
            const content = await fs.readFile(filePath, 'utf8');
            const metadata = this.extractMetadata(content);

            if (metadata && metadata.status === 'pending') {
                pendingEmails.push({
                    emailId: metadata.id,
                    subject: metadata.subject,
                    recipients: metadata.recipients,
                    priority: metadata.priority,
                    created_at: metadata.created_at,
                    category: metadata.category
                });
            }
        }

        return pendingEmails;
    }

    async resendEmail(params) {
        const { emailId, newRecipients } = params;

        if (!emailId) {
            throw new Error('Email ID is required to resend email');
        }

        const emailFilePattern = `EMAIL_${emailId}.md`;
        const files = await fs.readdir(NEEDS_ACTION_PATH);
        const matchingFiles = files.filter(file => file.startsWith(`EMAIL_${emailId}`));

        if (matchingFiles.length === 0) {
            throw new Error(`Email not found: ${emailId}`);
        }

        const emailFilePath = path.join(NEEDS_ACTION_PATH, matchingFiles[0]);
        const content = await fs.readFile(emailFilePath, 'utf8');
        const metadata = this.extractMetadata(content);

        if (!metadata) {
            throw new Error('Invalid email file format');
        }

        // Create new email with same content but new recipients
        const newEmailData = {
            ...metadata,
            recipients: newRecipients || metadata.recipients,
            status: 'pending',
            original_email_id: emailId,
            created_at: new Date().toISOString()
        };

        const newEmailId = `EMAIL_${uuidv4()}`;
        newEmailData.id = newEmailId;
        delete newEmailData.error;

        const newFileName = `${newEmailId}.md`;
        const newFilePath = path.join(NEEDS_ACTION_PATH, newFileName);
        const newContent = this.generateEmailFileContent(newEmailData);

        await fs.writeFile(newFilePath, newContent, 'utf8');
        logger.info(`Resent email: ${newEmailId} (original: ${emailId})`);

        return {
            originalEmailId: emailId,
            newEmailId,
            newFilePath,
            status: 'pending'
        };
    }
}

// MCP Server Setup
const server = new MCPServer();

// MCP Protocol Implementation
async function handleMCPRequest(request) {
    try {
        const { method, params } = JSON.parse(request);
        const response = await server.handleRequest(method, params);
        return JSON.stringify(response);
    } catch (error) {
        logger.error('Error handling MCP request:', error);
        return JSON.stringify({ success: false, error: error.message });
    }
}

// Start the MCP server
async function startServer() {
    try {
        // Initialize email transport
        const transportReady = await initializeEmailTransport();
        if (!transportReady) {
            logger.warn('Email transport not ready, server starting in read-only mode');
        }

        // Start MCP server
        const net = require('net');
        const PORT = process.env.MCP_PORT || 8080;

        const server = net.createServer((socket) => {
            logger.info('MCP client connected');

            socket.on('data', async (data) => {
                try {
                    const response = await handleMCPRequest(data.toString());
                    socket.write(response);
                } catch (error) {
                    logger.error('Error processing client request:', error);
                    socket.write(JSON.stringify({ success: false, error: error.message }));
                }
            });

            socket.on('end', () => {
                logger.info('MCP client disconnected');
            });

            socket.on('error', (error) => {
                logger.error('Socket error:', error);
            });
        });

        server.listen(PORT, () => {
            logger.info(`MCP Email Server running on port ${PORT}`);
            console.log(`MCP Email Server running on port ${PORT}`);
        });

        server.on('error', (error) => {
            logger.error('Server error:', error);
        });

    } catch (error) {
        logger.error('Failed to start MCP server:', error);
        process.exit(1);
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    logger.info('Shutting down MCP Email Server...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger.info('Shutting down MCP Email Server...');
    process.exit(0);
});

// Start the server if this file is run directly
if (require.main === module) {
    startServer();
}

// Export for testing
module.exports = { MCPServer, startServer };