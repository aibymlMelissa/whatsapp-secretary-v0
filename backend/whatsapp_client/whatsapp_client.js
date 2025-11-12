const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const qrcode = require('qrcode-terminal');

const SESSION_PATH = process.env.SESSION_PATH || './whatsapp-session';
const MEDIA_PATH = process.env.MEDIA_PATH || './downloads';
const CALLBACK_URL = process.env.PYTHON_CALLBACK_URL || 'http://localhost:8001/api/whatsapp/callback';

class WhatsAppClient {
    constructor() {
        this.isConnected = false;
        this.isConnecting = false;
        this.client = null;

        console.log('WhatsApp client initialized, ready for commands');
    }

    async initialize() {
        if (this.isConnecting || this.isConnected) {
            console.log('WhatsApp is already connecting or connected');
            return;
        }

        this.isConnecting = true;
        console.log('Initializing WhatsApp client...');

        try {
            this.client = new Client({
                authStrategy: new LocalAuth({
                    dataPath: SESSION_PATH
                }),
                puppeteer: {
                    headless: true,
                    timeout: 120000,
                    args: [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--single-process',
                        '--disable-gpu',
                        '--disable-extensions'
                    ]
                }
            });

            this.setupEventHandlers();
            await this.client.initialize();
        } catch (error) {
            console.error('Failed to initialize WhatsApp client:', error);
            this.isConnecting = false;
            throw error;
        }
    }

    setupEventHandlers() {
        if (!this.client) return;

        this.client.on('qr', (qr) => {
            console.log('QR Code received, scan with your phone:');
            qrcode.generate(qr, { small: true });

            // Write QR code to file for Python backend to read
            const qrFile = path.join(process.cwd(), 'qr_code.txt');
            fs.writeFileSync(qrFile, qr);
            console.log(`✅ QR code written to ${qrFile}`);

            this.sendCallback('qr_code', { qr });
        });

        this.client.on('ready', () => {
            console.log('WhatsApp Client is ready!');
            this.isConnected = true;
            this.isConnecting = false;
            this.sendCallback('ready', { status: 'connected' });
        });

        this.client.on('authenticated', () => {
            console.log('WhatsApp authenticated');
            this.sendCallback('authenticated', {});
        });

        this.client.on('loading_screen', (percent, message) => {
            console.log('Loading screen:', percent, message);
        });

        this.client.on('auth_failure', (msg) => {
            console.error('Authentication failed:', msg);
            this.isConnecting = false;
            this.sendCallback('auth_failure', { message: msg });
        });

        this.client.on('disconnected', (reason) => {
            console.log('WhatsApp disconnected:', reason);
            this.isConnected = false;
            this.isConnecting = false;
            this.sendCallback('disconnected', { reason });
        });

        this.client.on('message', async (message) => {
            await this.handleMessage(message);
        });

        this.client.on('message_create', (message) => {
            if (message.fromMe) {
                this.sendCallback('message_sent', {
                    chatId: message.to,
                    messageId: message.id.id,
                    body: message.body,
                    timestamp: message.timestamp
                });
            }
        });
    }

    async handleMessage(message) {
        try {
            const messageData = {
                id: message.id.id,
                chatId: message.from,
                body: message.body,
                timestamp: message.timestamp,
                fromMe: message.fromMe,
                hasMedia: message.hasMedia,
                type: message.type,
                author: message.author
            };

            // Download media if present
            if (message.hasMedia) {
                const media = await message.downloadMedia();
                if (media) {
                    const filename = `${Date.now()}_${message.from.replace('@', '_')}.${media.mimetype.split('/')[1]}`;
                    const filepath = path.join(MEDIA_PATH, filename);

                    // Ensure media directory exists
                    if (!fs.existsSync(MEDIA_PATH)) {
                        fs.mkdirSync(MEDIA_PATH, { recursive: true });
                    }

                    const buffer = Buffer.from(media.data, 'base64');
                    fs.writeFileSync(filepath, buffer);

                    messageData.mediaPath = filepath;
                    messageData.mediaFilename = filename;
                    messageData.mimeType = media.mimetype;
                }
            }

            // Send to Python backend
            this.sendCallback('new_message', messageData);

        } catch (error) {
            console.error('Error handling message:', error);
        }
    }

    async sendCallback(event, data) {
        try {
            console.log(`📞 Sending callback to ${CALLBACK_URL}:`, { event, data });
            const response = await axios.post(CALLBACK_URL, {
                event,
                data,
                timestamp: Date.now()
            }, { timeout: 5000 });
            console.log(`✅ Callback successful:`, response.status, response.data);
        } catch (error) {
            console.error(`❌ Callback failed (${CALLBACK_URL}):`, error.message);
            if (error.response) {
                console.error(`❌ Response status: ${error.response.status}`);
                console.error(`❌ Response data:`, error.response.data);
            }
        }
    }

    async processStdinCommands() {
        process.stdin.setEncoding('utf8');

        process.stdin.on('data', async (data) => {
            try {
                const commands = data.trim().split('\n');
                for (const commandStr of commands) {
                    if (commandStr.trim()) {
                        const command = JSON.parse(commandStr);
                        await this.executeCommand(command);
                    }
                }
            } catch (error) {
                console.error('Error processing command:', error);
                this.sendResponse({ success: false, error: error.message });
            }
        });
    }

    async executeCommand(command) {
        const { action, data, id } = command;

        try {
            let result;

            switch (action) {
                case 'send_message':
                    result = await this.sendMessage(data.chatId, data.message, data.mediaPath);
                    break;

                case 'get_chats':
                    result = await this.getChats();
                    break;

                case 'get_chat_messages':
                    result = await this.getChatMessages(data.chatId, data.limit);
                    break;

                case 'get_status':
                    result = {
                        connected: this.isConnected,
                        connecting: this.isConnecting,
                        ready: this.client?.info !== null,
                        hasClient: !!this.client
                    };
                    break;

                case 'initialize':
                    await this.initialize();
                    result = { initialized: true };
                    break;

                default:
                    throw new Error(`Unknown action: ${action}`);
            }

            this.sendResponse({ success: true, data: result, id });

        } catch (error) {
            console.error(`Error executing ${action}:`, error);
            this.sendResponse({ success: false, error: error.message, id });
        }
    }

    async sendMessage(chatId, message, mediaPath = null) {
        if (!this.client?.info) {
            throw new Error('WhatsApp client not ready');
        }

        if (mediaPath && fs.existsSync(mediaPath)) {
            const media = MessageMedia.fromFilePath(mediaPath);
            await this.client.sendMessage(chatId, media, { caption: message || undefined });
        } else {
            await this.client.sendMessage(chatId, message);
        }

        return { sent: true, timestamp: Date.now() };
    }

    async getChats() {
        if (!this.client?.info) {
            throw new Error('WhatsApp client not ready');
        }

        const chats = await this.client.getChats();
        return chats.map(chat => ({
            id: chat.id._serialized,
            name: chat.name,
            isGroup: chat.isGroup,
            unreadCount: chat.unreadCount,
            lastMessage: chat.lastMessage ? {
                body: chat.lastMessage.body,
                timestamp: chat.lastMessage.timestamp,
                fromMe: chat.lastMessage.fromMe
            } : null
        }));
    }

    async getChatMessages(chatId, limit = 50) {
        if (!this.client?.info) {
            throw new Error('WhatsApp client not ready');
        }

        const chat = await this.client.getChatById(chatId);
        const messages = await chat.fetchMessages({ limit });

        return messages.map(msg => ({
            id: msg.id.id,
            body: msg.body,
            timestamp: msg.timestamp,
            fromMe: msg.fromMe,
            hasMedia: msg.hasMedia,
            type: msg.type,
            author: msg.author
        }));
    }

    sendResponse(response) {
        console.log(`PYTHON_RESPONSE:${JSON.stringify(response)}`);
    }

    async disconnect() {
        if (this.client) {
            await this.client.destroy();
            this.client = null;
            this.isConnected = false;
            this.isConnecting = false;
        }
    }
}

// Create the client instance
const client = new WhatsAppClient();

// Start processing commands from stdin
client.processStdinCommands();

// Handle process termination
process.on('SIGINT', () => {
    console.log('Shutting down WhatsApp client...');
    if (client.client) {
        client.client.destroy();
    }
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('Shutting down WhatsApp client...');
    if (client.client) {
        client.client.destroy();
    }
    process.exit(0);
});