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
const CALLBACK_URL = process.env.PYTHON_CALLBACK_URL || 'http://127.0.0.1:8001/api/whatsapp/callback';
const HTTP_PORT = 8002; // HTTP server for receiving send commands

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

            // Set 60-second timeout to restart if not scanned
            this.qrTimeout = setTimeout(() => {
                console.log('⏰ QR code not scanned within 60 seconds, restarting...');
                this.restart();
            }, 60000);
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

            // Fetch and send chats to backend
            try {
                console.log('📥 Fetching chats from WhatsApp...');
                const chats = await this.client.getChats();
                console.log(`✅ Found ${chats.length} chats`);

                // Send chats info to backend
                const chatsData = chats.slice(0, 50).map(chat => ({
                    id: chat.id._serialized,
                    name: chat.name || chat.id.user || 'Unknown',
                    isGroup: chat.isGroup,
                    timestamp: chat.timestamp || Date.now(),
                    unreadCount: chat.unreadCount || 0
                }));

                await this.sendCallback('chats_loaded', { chats: chatsData });
                console.log(`📤 Sent ${chatsData.length} chats to backend`);

                // Fetch recent message history for each chat
                console.log('📥 Fetching message history for chats...');
                for (const chat of chats.slice(0, 10)) {  // Limit to first 10 chats to avoid overload
                    try {
                        const messages = await chat.fetchMessages({ limit: 50 });
                        console.log(`📥 Fetched ${messages.length} messages for chat ${chat.name}`);

                        // Send each message to backend
                        for (const msg of messages) {
                            const messageData = {
                                id: msg.id._serialized,
                                chatId: msg.from || chat.id._serialized,
                                body: msg.body || '',
                                fromMe: msg.fromMe,
                                timestamp: msg.timestamp,
                                hasMedia: msg.hasMedia,
                                type: msg.type
                            };

                            await this.sendCallback('new_message', messageData);
                        }
                    } catch (msgError) {
                        console.error(`❌ Error fetching messages for chat ${chat.name}:`, msgError);
                    }
                }
                console.log('✅ Message history fetch completed');
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

        this.client.on('disconnected', (reason) => {
            console.log('❌ WhatsApp disconnected:', reason);
            this.status.connected = false;
            this.status.connecting = false;
            this.updateStatus();
            this.sendCallback('disconnected', { reason });
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

        // Clear timeout
        if (this.qrTimeout) {
            clearTimeout(this.qrTimeout);
            this.qrTimeout = null;
        }

        // Destroy existing client
        if (this.client) {
            try {
                await this.client.destroy();
                console.log('✅ Client destroyed');
            } catch (error) {
                console.error('❌ Error destroying client:', error);
            }
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

        // Wait a bit before reinitializing
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Reinitialize
        console.log('🚀 Reinitializing...');
        await this.initialize();
    }
}

const bridge = new WhatsAppBridge();
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

// Keep the process alive
process.on('SIGINT', () => {
    console.log('Shutting down WhatsApp bridge...');
    if (bridge.client) {
        bridge.client.destroy();
    }
    process.exit(0);
});