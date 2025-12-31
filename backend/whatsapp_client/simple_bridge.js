/**
 * WhatsApp Web.js Bridge - File-based Communication Architecture
 *
 * This bridge provides reliable communication between Node.js (WhatsApp Web.js)
 * and Python FastAPI backend using file-based IPC instead of stdin/stdout.
 *
 * Architecture:
 * - Node.js process runs WhatsApp Web.js client
 * - Status updates written to status.json file
 * - QR codes written to qr_code.txt file
 * - Python backend polls these files for real-time updates
 * - Eliminates hanging issues with process communication
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const express = require('express');

const QR_FILE = path.join(__dirname, 'qr_code.txt');
const STATUS_FILE = path.join(__dirname, 'status.json');
const LOCK_FILE = path.join(__dirname, 'bridge.lock');
const CALLBACK_URL = process.env.PYTHON_CALLBACK_URL || 'http://127.0.0.1:8001/api/whatsapp/callback';
const HTTP_PORT = parseInt(process.env.WHATSAPP_BRIDGE_PORT || process.env.BRIDGE_PORT || '8002'); // HTTP server for receiving send commands

// Prevent multiple instances with lock file
if (fs.existsSync(LOCK_FILE)) {
    const lockContent = fs.readFileSync(LOCK_FILE, 'utf8');
    const lockPid = parseInt(lockContent);

    // Check if process is still running
    try {
        process.kill(lockPid, 0); // Signal 0 checks if process exists
        console.error(`❌ Another bridge instance is already running (PID: ${lockPid}). Exiting.`);
        process.exit(1);
    } catch (e) {
        // Process doesn't exist, remove stale lock
        console.log('⚠️  Removing stale lock file');
        fs.unlinkSync(LOCK_FILE);
    }
}

// Create lock file with current PID
fs.writeFileSync(LOCK_FILE, process.pid.toString());
console.log(`✅ Lock acquired (PID: ${process.pid})`);

console.log('Starting WhatsApp client with file-based communication...');

class WhatsAppBridge {
    constructor() {
        this.client = null;
        this.status = {
            connected: false,
            connecting: false,
            qr_code: null,
            ready: false
        };
        this.qrTimeout = null;
        this.qrGenerationTime = null;
        this.isRestarting = false;
        this.restartTimeout = null;
        this.updateStatus();
    }

    updateStatus() {
        fs.writeFileSync(STATUS_FILE, JSON.stringify(this.status, null, 2));
    }

    async sendCallback(event, data) {
        try {
            await axios.post(CALLBACK_URL, {
                event: event,
                data: data
            }, {
                timeout: 5000
            });
            console.log(`✅ Callback sent: ${event}`);
        } catch (error) {
            console.error(`❌ Callback failed for ${event}:`, error.message);
        }
    }

    async initialize() {
        this.status.connecting = true;
        this.updateStatus();

        this.client = new Client({
            authStrategy: new LocalAuth({
                dataPath: './whatsapp-session'
            }),
            puppeteer: {
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            }
        });

        this.client.on('qr', (qr) => {
            console.log('✅ QR Code received!');
            this.status.qr_code = qr;
            this.updateStatus();

            // Write QR code to file for Python to read
            fs.writeFileSync(QR_FILE, qr);
            console.log('📄 QR code written to file');

            // Track QR generation time
            this.qrGenerationTime = Date.now();

            // Clear existing timeout
            if (this.qrTimeout) {
                clearTimeout(this.qrTimeout);
            }

            // REMOVED: Auto-restart on QR timeout - let QR stay valid indefinitely
            // QR code will remain valid until:
            // 1. User scans it successfully
            // 2. User manually resets the session
            // 3. WhatsApp Web expires it (usually 2 minutes, but we let WhatsApp handle it)
            console.log('⏰ QR code will remain valid - no auto-restart timeout');
            console.log('ℹ️  Scan anytime or manually reset if needed');
        });

        this.client.on('ready', async () => {
            console.log('✅ WhatsApp Client is ready!');
            this.status.connected = true;
            this.status.connecting = false;
            this.status.ready = true;
            this.updateStatus();
            this.sendCallback('ready', {});

            // Clear QR timeout since we're now connected
            if (this.qrTimeout) {
                clearTimeout(this.qrTimeout);
                this.qrTimeout = null;
            }

            // Fetch and send chats to backend (LIMITED to prevent overload)
            try {
                console.log('📥 Fetching chats from WhatsApp...');
                const chats = await this.client.getChats();
                console.log(`✅ Found ${chats.length} chats`);

                // Send only top 20 chats to backend (reduced from 50)
                const chatsData = chats.slice(0, 20).map(chat => ({
                    id: chat.id._serialized,
                    name: chat.name || chat.id.user || 'Unknown',
                    isGroup: chat.isGroup,
                    timestamp: chat.timestamp || Date.now(),
                    unreadCount: chat.unreadCount || 0
                }));

                await this.sendCallback('chats_loaded', { chats: chatsData });
                console.log(`📤 Sent ${chatsData.length} chats to backend`);

                // SKIP message history fetch on initial connect to prevent overload
                // Messages will be fetched on-demand when user opens a chat
                console.log('⚠️  Skipping message history fetch to prevent overload');
                console.log('ℹ️  Messages will load on-demand when chats are opened');
            } catch (error) {
                console.error('❌ Error fetching chats:', error);
            }
        });

        this.client.on('authenticated', () => {
            console.log('✅ WhatsApp authenticated');

            // Clear QR timeout since we're authenticated
            if (this.qrTimeout) {
                clearTimeout(this.qrTimeout);
                this.qrTimeout = null;
            }
        });

        this.client.on('auth_failure', (msg) => {
            console.error('❌ Authentication failed:', msg);
            this.status.connecting = false;
            this.status.error = msg;
            this.updateStatus();
        });

        this.client.on('disconnected', async (reason) => {
            console.log('❌ WhatsApp disconnected:', reason);
            this.status.connected = false;
            this.status.connecting = false;
            this.updateStatus();
            this.sendCallback('disconnected', { reason });

            // DISABLED: Auto-restart on LOGOUT
            // Let the connection stay disconnected for manual intervention
            // This prevents rapid QR regeneration loops that confuse the connection
            console.log('⚠️  Connection lost - waiting for manual reset');
            console.log('ℹ️  Call /api/whatsapp/reset-session to restart');

            // Track disconnect time
            this.lastDisconnectTime = Date.now();
        });

        // Handle incoming messages
        this.client.on('message', async (message) => {
            console.log(`📨 New message from ${message.from}: ${message.body}`);

            try {
                const messageData = {
                    id: message.id._serialized,
                    chatId: message.from,
                    body: message.body,
                    fromMe: message.fromMe,
                    timestamp: message.timestamp,
                    hasMedia: message.hasMedia,
                    type: message.type
                };

                await this.sendCallback('new_message', messageData);
            } catch (error) {
                console.error('❌ Error processing message:', error);
            }
        });

        try {
            await this.client.initialize();
        } catch (error) {
            console.error('❌ Failed to initialize:', error);
            this.status.connecting = false;
            this.status.error = error.message;
            this.updateStatus();
        }
    }

    async restart() {
        console.log('🔄 Restarting WhatsApp client...');

        // Prevent multiple simultaneous restarts
        if (this.isRestarting) {
            console.log('⚠️  Restart already in progress, skipping...');
            return;
        }
        this.isRestarting = true;

        try {
            // Clear timeouts
            if (this.qrTimeout) {
                clearTimeout(this.qrTimeout);
                this.qrTimeout = null;
            }
            if (this.restartTimeout) {
                clearTimeout(this.restartTimeout);
                this.restartTimeout = null;
            }

            // Destroy existing client
            if (this.client) {
                try {
                    // Remove all listeners to prevent multiple event handlers
                    this.client.removeAllListeners();
                    await this.client.destroy();
                    console.log('✅ Client destroyed');
                } catch (error) {
                    console.error('❌ Error destroying client:', error);
                }
                this.client = null;
            }

            // Clean up session files
            try {
                const sessionPath = path.join(__dirname, 'whatsapp-session');
                if (fs.existsSync(sessionPath)) {
                    fs.rmSync(sessionPath, { recursive: true, force: true });
                    console.log('✅ Session cleared');
                }
                if (fs.existsSync(QR_FILE)) {
                    fs.unlinkSync(QR_FILE);
                }
                if (fs.existsSync(STATUS_FILE)) {
                    fs.unlinkSync(STATUS_FILE);
                }
            } catch (error) {
                console.error('❌ Error cleaning files:', error);
            }

            // Wait longer to ensure Chrome process fully exits
            console.log('⏳ Waiting for Chrome to fully exit...');
            await new Promise(resolve => setTimeout(resolve, 5000));

            // Reinitialize
            console.log('🚀 Reinitializing...');
            await this.initialize();
        } finally {
            this.isRestarting = false;
        }
    }
}

// Singleton instance - ensure only ONE bridge exists
let bridgeInstance = null;

function getBridgeInstance() {
    if (!bridgeInstance) {
        bridgeInstance = new WhatsAppBridge();
    }
    return bridgeInstance;
}

const bridge = getBridgeInstance();
bridge.initialize();

// HTTP server for receiving send message commands
const app = express();
app.use(express.json());

app.post('/send', async (req, res) => {
    try {
        const { chatId, message } = req.body;

        if (!chatId || !message) {
            return res.status(400).json({ error: 'chatId and message are required' });
        }

        if (!bridge.client || !bridge.status.ready) {
            return res.status(503).json({ error: 'WhatsApp client not ready' });
        }

        console.log(`📤 Sending message to ${chatId}: ${message.substring(0, 50)}...`);
        await bridge.client.sendMessage(chatId, message);
        console.log(`✅ Message sent successfully`);

        res.json({ success: true, chatId, message });
    } catch (error) {
        console.error('❌ Error sending message:', error);
        res.status(500).json({ error: error.message });
    }
});

app.listen(HTTP_PORT, () => {
    console.log(`✅ HTTP server listening on port ${HTTP_PORT} for send commands`);
});

// Global error handlers to prevent crashes
process.on('unhandledRejection', (error) => {
    console.error('❌ Unhandled promise rejection:', error);
    // Don't exit the process, just log the error
});

process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught exception:', error);
    // Don't exit the process, just log the error
});

// Cleanup lock file on exit
function cleanup() {
    try {
        if (fs.existsSync(LOCK_FILE)) {
            fs.unlinkSync(LOCK_FILE);
            console.log('✅ Lock file removed');
        }
    } catch (e) {
        console.error('❌ Error removing lock file:', e);
    }
}

// Keep the process alive
process.on('SIGINT', () => {
    console.log('Shutting down WhatsApp bridge...');
    if (bridge.client) {
        bridge.client.destroy();
    }
    cleanup();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('Received SIGTERM, shutting down...');
    if (bridge.client) {
        bridge.client.destroy();
    }
    cleanup();
    process.exit(0);
});

process.on('exit', () => {
    cleanup();
});