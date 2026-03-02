// Enhanced MCP Email Server for Silver Tier Functional Assistant
// This server implements comprehensive email functionality with robust security, error handling, and integration with the existing file-based approval workflow

const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { v4: uuidv4 } = require('uuid');
const nodemailer = require('nodemailer');
const { createLogger, transports, format } = require('winston');
const yaml = require('js-yaml');
const crypto = require('crypto');

// Configuration
const config = require('./config.json');
const VAULT_PATH = process.env.VAULT_PATH || 'C:\Users\goku\MyWebsiteProjects\hackathon-0\Bronze-Tier\AI_Employee_Vault';
const NEEDS_ACTION_PATH = path.join(VAULT_PATH, 'Needs_Action');
const DONE_PATH = path.join(VAULT_PATH, 'Done');
const LOG_PATH = 'mcp-email-server-enhanced.log';
const SECURITY_KEY = process.env.SECURITY_KEY || 'default-security-key-change-in-production';

// Logger setup
const logger = createLogger({
    level: config.logging?.level || 'INFO',
    format: format.combine(
        format.timestamp(),
        format.errors({ stack: true }),
        format.json()
    ),
    defaultMeta: { service: 'mcp-email-server-enhanced' },
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

// Security Configuration
const securityConfig = {
    maxAttempts: 5,
    lockoutDuration: 300000, // 5 minutes
    allowedDomains: ['example.com', 'company.com'],
    rateLimit: 10 // requests per minute
};

// Rate limiting
const requestTracker = new Map();
const attemptTracker = new Map();

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

// Encryption utilities
function encryptData(data) {
    const cipher = crypto.createCipher('aes-256-cbc', SECURITY_KEY);
    let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return encrypted;
}

function decryptData(encryptedData) {
    try {
        const decipher = crypto.createDecipher('aes-256-cbc', SECURITY_KEY);
        let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
        decrypted += decipher.final('utf8');
        return JSON.parse(decrypted);
    } catch (error) {
        logger.error('Decryption failed:', error);
        return null;
    }
}

// Rate limiting check
function checkRateLimit(ipAddress) {
    const now = Date.now();
    const requests = requestTracker.get(ipAddress) || [];

    // Remove old requests (older than 1 minute)
    const recentRequests = requests.filter(timestamp => now - timestamp < 60000);

    if (recentRequests.length >= securityConfig.rateLimit) {
        return false;
    }

    recentRequests.push(now);
    requestTracker.set(ipAddress, recentRequests);
    return true;
}

// Authentication middleware
function authenticateRequest(authToken, ipAddress) {
    const now = Date.now();

    // Check if IP is locked out
    const attemptData = attemptTracker.get(ipAddress) || { attempts: 0, lastAttempt: 0 };
    if (attemptData.attempts >= securityConfig.maxAttempts &&
        now - attemptData.lastAttempt < securityConfig.lockoutDuration) {
        return false;
    }

    // Validate token
    const expectedToken = process.env.MCP_AUTH_TOKEN;
    if (!expectedToken || authToken !== expectedToken) {
        // Increment failed attempts
        attemptData.attempts = (attemptData.attempts || 0) + 1;
        attemptData.lastAttempt = now;
        attemptTracker.set(ipAddress, attemptData);
        return false;
    }

    // Reset attempts on successful authentication
    attemptTracker.set(ipAddress, { attempts: 0, lastAttempt: 0 });
    return true;
}

// MCP Server Class
class MCPServer {
    constructor() {
        this.handlers = new Map();
        this.initializeHandlers();
        this.initializeEmailWorkflow();
        this.securityMonitor = null;
    }

    initializeHandlers() {
        // MCP Tool Handlers
        this.handlers.set('compose-email', this.composeEmail.bind(this));
        this.handlers.set('send-email', this.sendEmail.bind(this));
        this.handlers.set('get-email-templates', this.getEmailTemplates.bind(this));
        this.handlers.set('get-approval-status', this.getApprovalStatus.bind(this));
        this.handlers.set('list-pending-emails', this.listPendingEmails.bind(this));
        this.handlers.set('resend-email', this.resendEmail.bind(this));
        this.handlers.set('schedule-email', this.scheduleEmail.bind(this));
        this.handlers.set('cancel-scheduled-email', this.cancelScheduledEmail.bind(this));
        this.handlers.set('get-email-history', this.getEmailHistory.bind(this));
        this.handlers.set('validate-email-recipients', this.validateRecipients.bind(this));
        this.handlers.set('test-email-connection', this.testConnection.bind(this));
    }

    initializeEmailWorkflow() {
        // Ensure directories exist
        fs.mkdir(NEEDS_ACTION_PATH, { recursive: true })
            .catch(err => logger.error('Failed to create Needs_Action directory:', err));

        fs.mkdir(DONE_PATH, { recursive: true })
            .catch(err => logger.error('Failed to create Done directory:', err));

        // Set up file watcher for email approvals
        this.setupFileWatcher();

        // Start security monitoring
        this.startSecurityMonitoring();
    }

    setupFileWatcher() {
        const chokidar = require('chokidar');

        const watcher = chokidar.watch(NEEDS_ACTION_PATH, {
            persistent: true,
            ignoreInitial: true,
            awaitWriteFinish: {
                stabilityThreshold: 2000,
                pollInterval: 100
            }
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

        watcher.on('unlink', (filePath) => {
            logger.info(`Email file removed: ${path.basename(filePath)}`);
        });

        logger.info('File watcher set up for email approvals');
    }

    startSecurityMonitoring() {
        // Monitor for suspicious activity
        this.securityMonitor = setInterval(() => {
            const now = Date.now();

            // Clean up old rate limit data
            for (const [ip, requests] of requestTracker.entries()) {
                const recentRequests = requests.filter(timestamp => now - timestamp < 120000); // 2 minutes
                if (recentRequests.length === 0) {
                    requestTracker.delete(ip);
                } else {
                    requestTracker.set(ip, recentRequests);
                }
            }

            // Clean up old attempt data
            for (const [ip, data] of attemptTracker.entries()) {
                if (now - data.lastAttempt > securityConfig.lockoutDuration * 2) {
                    attemptTracker.delete(ip);
                }
            }
        }, 60000); // Run every minute
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

                // Validate email content
                const validationResult = this.validateEmailContent(metadata);
                if (!validationResult.valid) {
                    await this.updateEmailStatus(filePath, 'validation-failed', validationResult.errors.join(', '));
                    return;
                }

                // Notify system of pending approval
                this.notifyPendingApproval(metadata);
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
                const metadata = JSON.parse(match[1].trim());
                // Decrypt sensitive fields if needed
                if (metadata.encrypted_fields) {
                    for (const field of metadata.encrypted_fields) {
                        if (metadata[field]) {
                            metadata[field] = decryptData(metadata[field]);
                        }
                    }
                }
                return metadata;
            } catch (error) {
                logger.error('Error parsing metadata:', error);
            }
        }
        return null;
    }

    generateEmailFileContent(metadata) {
        // Encrypt sensitive fields
        const encryptedFields = [];
        const secureMetadata = { ...metadata };

        if (metadata.sensitive_data) {
            secureMetadata.sensitive_data = encryptData(metadata.sensitive_data);
            encryptedFields.push('sensitive_data');
        }

        if (metadata.api_keys) {
            secureMetadata.api_keys = encryptData(metadata.api_keys);
            encryptedFields.push('api_keys');
        }

        if (encryptedFields.length > 0) {
            secureMetadata.encrypted_fields = encryptedFields;
        }

        const frontMatter = JSON.stringify(secureMetadata, null, 2);

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

    async sendEmailFromFile(filePath) {
        try {
            const content = await fs.readFile(filePath, 'utf8');
            const metadata = this.extractMetadata(content);

            if (!metadata || !metadata.recipients || !metadata.subject || !metadata.body) {
                logger.error('Email file missing required fields');
                await this.updateEmailStatus(filePath, 'failed', 'Missing required email fields');
                return;
            }

            const emailData = {
                from: metadata.from || config.email?.smtp?.user,
                to: metadata.recipients,
                subject: metadata.subject,
                text: metadata.body,
                html: metadata.htmlBody || null,
                attachments: metadata.attachments || []
            };

            if (emailTransport) {
                const info = await emailTransport.sendMail(emailData);
                logger.info(`Email sent: ${info.messageId}`;

                // Move to done folder
                await this.moveToDone(filePath, metadata);
            } else {
                logger.error('Email transport not initialized');
                await this.updateEmailStatus(filePath, 'failed', 'Email transport not initialized');
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
            return `---
${updatedFrontMatter}
---`;
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

    validateEmailContent(metadata) {
        const errors = [];

        // Validate recipients
        if (!metadata.recipients || typeof metadata.recipients !== 'string') {
            errors.push('Invalid recipients format');
        } else {
            const recipients = metadata.recipients.split(',').map(r => r.trim());
            for (const recipient of recipients) {
                if (!this.validateEmailFormat(recipient)) {
                    errors.push(`Invalid email format: ${recipient}`);
                }
                if (securityConfig.allowedDomains.length > 0) {
                    const domain = recipient.split('@')[1];
                    if (!securityConfig.allowedDomains.includes(domain)) {
                        errors.push(`Email domain not allowed: ${domain}`);
                    }
                }
            }
        }

        // Validate subject length
        if (!metadata.subject || metadata.subject.length < 1 || metadata.subject.length > 998) {
            errors.push('Subject must be between 1 and 998 characters');
        }

        // Validate body length
        if (!metadata.body || metadata.body.length < 1 || metadata.body.length > 100000) {
            errors.push('Body must be between 1 and 100,000 characters');
        }

        // Validate priority
        const validPriorities = ['low', 'medium', 'high', 'urgent'];
        if (metadata.priority && !validPriorities.includes(metadata.priority)) {
            errors.push(`Invalid priority: ${metadata.priority}. Must be one of: ${validPriorities.join(', ')}`);
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    validateEmailFormat(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    notifyPendingApproval(metadata) {
        // This would integrate with your approval workflow system
        // For now, just log the pending approval
        logger.info(`Email pending approval: ${metadata.id} - ${metadata.subject}`);

        // You could also send a notification to an approval channel
        // This is where you'd integrate with your existing approval workflow
    }

    async handleRequest(method, params, authToken, ipAddress) {
        // Security checks
        if (!checkRateLimit(ipAddress)) {
            return { success: false, error: 'Rate limit exceeded. Please try again later.' };
        }

        if (!authenticateRequest(authToken, ipAddress)) {
            return { success: false, error: 'Authentication failed' };
        }

        const handler = this.handlers.get(method);

        if (!handler) {
            return { success: false, error: `Unknown method: ${method}` };
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
            category = 'general',
            attachments = [],
            schedule_for = null
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
            attachments,
            schedule_for
        };

        const content = this.generateEmailFileContent(metadata);

        await fs.writeFile(filePath, content, 'utf8');
        logger.info(`Composed new email: ${fileName}`);

        return {
            emailId,
            filePath,
            status: 'pending',
            metadata
        };
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
                },
                {
                    name: 'Meeting Confirmation',
                    subject: 'Meeting Confirmation: {topic}',
                    body: 'Dear {name},\n\nThis is to confirm our meeting on {date} at {time} to discuss {topic}.\n\nLocation: {location}\n\nLooking forward to our conversation!'
                }
            ],
            business: [
                {
                    name: 'Sales Pitch',
                    subject: 'Transform your {industry} business with {product}',
                    body: 'Dear {name},\n\nAre you looking to improve your {industry} business? Our {product} can help you achieve {benefit}...'
                },
                {
                    name: 'Customer Support',
                    subject: 'RE: {issue} - Support Ticket #{id}',
                    body: 'Dear {name},\n\nThank you for contacting our support team regarding {issue}. We\'ve received your ticket #{id} and will get back to you within 24 hours.\n\nBest regards,\nSupport Team'
                }
            ],
            technical: [
                {
                    name: 'System Alert',
                    subject: 'System Alert: {system} Issue',
                    body: 'Team,\n\nWe are experiencing issues with {system}. Our team is actively working on a resolution.\n\nStatus: {status}\nImpact: {impact}\nETA: {eta}\n\nWe will provide updates as they become available.'
                },
                {
                    name: 'Release Notes',
                    subject: 'Release Notes: Version {version}',
                    body: 'Hi Team,\n\nWe\'re excited to announce the release of version {version}!\n\n## New Features\n- {feature1}\n- {feature2}\n\n## Improvements\n- {improvement1}\n\n## Bug Fixes\n- {bugfix1}\n\n## Deployment\n- Date: {date}\n- Time: {time}\n- Environment: {environment}'
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
                    category: metadata.category,
                    filePath
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

    async scheduleEmail(params) {
        const { emailId, scheduleFor } = params;

        if (!emailId || !scheduleFor) {
            throw new Error('Email ID and scheduleFor timestamp are required to schedule email');
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

        // Update metadata with schedule time
        metadata.schedule_for = scheduleFor;
        metadata.status = 'scheduled';

        const updatedContent = this.updateMetadataInContent(content, metadata);
        await fs.writeFile(emailFilePath, updatedContent, 'utf8');
        logger.info(`Scheduled email ${emailId} for ${scheduleFor}`);

        // Set up scheduled send
        this.setupScheduledSend(emailId, scheduleFor);

        return {
            emailId,
            scheduleFor,
            status: 'scheduled'
        };
    }

    setupScheduledSend(emailId, scheduleFor) {
        const sendTime = new Date(scheduleFor).getTime();
        const now = Date.now();
        const delay = sendTime - now;

        if (delay <= 0) {
            logger.warn(`Schedule time for email ${emailId} is in the past. Sending immediately.`);
            this.sendEmail({ emailId, approval: true });
            return;
        }

        setTimeout(async () => {
            try {
                logger.info(`Sending scheduled email: ${emailId}`);
                await this.sendEmail({ emailId, approval: true });
            } catch (error) {
                logger.error(`Error sending scheduled email ${emailId}:`, error);
            }
        }, delay);

        logger.info(`Scheduled email ${emailId} to send in ${Math.floor(delay / 1000)} seconds`);
    }

    async cancelScheduledEmail(params) {
        const { emailId } = params;

        if (!emailId) {
            throw new Error('Email ID is required to cancel scheduled email');
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

        if (metadata.status !== 'scheduled') {
            throw new Error(`Email ${emailId} is not scheduled (current status: ${metadata.status})`);
        }

        // Update status to pending
        metadata.status = 'pending';
        delete metadata.schedule_for;

        const updatedContent = this.updateMetadataInContent(content, metadata);
        await fs.writeFile(emailFilePath, updatedContent, 'utf8');
        logger.info(`Cancelled scheduled email: ${emailId}`);

        return {
            emailId,
            status: 'pending',
            message: `Email ${emailId} scheduling cancelled`
        };
    }

    async getEmailHistory(params) {
        const { limit = 50, status = 'all' } = params;

        const doneFiles = await fs.readdir(DONE_PATH);
        const doneEmailFiles = doneFiles.filter(file => file.startsWith('EMAIL_') && file.endsWith('.md'));

        const history = [];

        for (const file of doneEmailFiles.slice(0, limit)) {
            const filePath = path.join(DONE_PATH, file);
            const content = await fs.readFile(filePath, 'utf8');
            const metadata = this.extractMetadata(content);

            if (metadata && (status === 'all' || metadata.status === status)) {
                history.push({
                    emailId: metadata.id,
                    subject: metadata.subject,
                    recipients: metadata.recipients,
                    priority: metadata.priority,
                    category: metadata.category,
                    status: metadata.status,
                    created_at: metadata.created_at,
                    sent_at: metadata.sent_at,
                    filePath
                });
            }
        }

        return history;
    }

    async validateRecipients(params) {
        const { recipients } = params;

        if (!recipients) {
            throw new Error('Recipients are required for validation');
        }

        const recipientList = recipients.split(',').map(r => r.trim());
        const validationResults = [];

        for (const recipient of recipientList) {
            const isValid = this.validateEmailFormat(recipient);
            const isAllowed = this.isDomainAllowed(recipient);

            validationResults.push({
                email: recipient,
                valid: isValid,
                allowed: isAllowed,
                reason: !isValid ? 'Invalid email format' : !isAllowed ? 'Domain not allowed' : 'Valid'
            });
        }

        return {
            recipients: recipientList,
            validationResults,
            allValid: validationResults.every(r => r.valid && r.allowed)
        };
    }

    isDomainAllowed(email) {
        if (securityConfig.allowedDomains.length === 0) {
            return true; // No domain restrictions
        }

        const domain = email.split('@')[1];
        return securityConfig.allowedDomains.includes(domain);
    }

    async testConnection() {
        try {
            if (!emailTransport) {
                await initializeEmailTransport();
            }

            const test = await emailTransport.verify();
            return {
                success: true,
                message: 'Email connection successful',
                details: test
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                details: error
            };
        }
    }
}

// MCP Server Setup
const server = new MCPServer();

// MCP Protocol Implementation
async function handleMCPRequest(request) {
    try {
        const { method, params, authToken, ipAddress } = JSON.parse(request);
        const response = await server.handleRequest(method, params, authToken, ipAddress);
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
        const PORT = process.env.MCP_PORT || 8081;

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
            logger.info(`Enhanced MCP Email Server running on port ${PORT}`);
            console.log(`Enhanced MCP Email Server running on port ${PORT}`);
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
    logger.info('Shutting down Enhanced MCP Email Server...');
    if (server.securityMonitor) {
        clearInterval(server.securityMonitor);
    }
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger.info('Shutting down Enhanced MCP Email Server...');
    if (server.securityMonitor) {
        clearInterval(server.securityMonitor);
    }
    process.exit(0);
});

// Start the server if this file is run directly
if (require.main === module) {
    startServer();
}

// Export for testing
module.exports = { MCPServer, startServer, initializeEmailTransport, checkRateLimit, authenticateRequest };