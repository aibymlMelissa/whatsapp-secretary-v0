
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const SESSION_PATH = process.env.SESSION_PATH || './whatsapp-session';
const MEDIA_PATH = process.env.MEDIA_PATH || './downloads';
const CALLBACK_URL = process.env.PYTHON_CALLBACK_URL || 'http://localhost:8000/api/whatsapp/callback';

class WhatsAppClient {
    constructor() {
        this.isConnected = false;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.pairingCode = null;
        this.pairingPhoneNumber = null;

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
                    '--disable-extensions',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            }
        });

        this.setupEventHandlers();
        this.commandQueue = [];
        this.isProcessing = false;

        // Start processing commands from stdin
        this.processStdinCommands();
    }
    
    setupEventHandlers() {
        this.client.on('qr', (qr) => {
            console.log('QR Code received');
            // Remove terminal QR display and only send to backend
            this.sendCallback('qr_code', { qr });
        });

        this.client.on('code', async (code) => {
            console.log('Pairing code received:', code);
            this.pairingCode = code;
            this.sendCallback('pairing_code', { code, phoneNumber: this.pairingPhoneNumber });
        });
        
        this.client.on('ready', () => {
            console.log('WhatsApp Client is ready!');
            this.isConnected = true;
            this.isConnecting = false;
            this.reconnectAttempts = 0;
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
            this.sendCallback('auth_failure', { message: msg });
        });
        
        this.client.on('disconnected', (reason) => {
            console.log('WhatsApp disconnected:', reason);
            this.isConnected = false;
            this.isConnecting = false;
            this.sendCallback('disconnected', { reason });
            this.attemptReconnect(reason);
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
            await axios.post(CALLBACK_URL, {
                event,
                data,
                timestamp: Date.now()
            }, { timeout: 5000 });
        } catch (error) {
            console.error('Callback failed:', error.message);
        }
    }
    
    async processStdinCommands() {
        process.stdin.setEncoding('utf8');
        
        process.stdin.on('data', async (data) => {
            try {
                const commands = data.trim().split('
');
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
                        ready: this.client.info !== null,
                        hasClient: !!this.client,
                        reconnectAttempts: this.reconnectAttempts,
                        pairingCode: this.pairingCode
                    };
                    break;

                case 'request_pairing_code':
                    this.pairingPhoneNumber = data.phoneNumber;
                    await this.client.requestPairingCode(data.phoneNumber);
                    result = { requested: true, phoneNumber: data.phoneNumber };
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
        if (!this.client.info) {
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
        if (!this.client.info) {
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
        if (!this.client.info) {
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
    
    async attemptReconnect(reason) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log(`Max reconnection attempts (${this.maxReconnectAttempts}) reached.`);
            return;
        }

        this.reconnectAttempts++;
        const delay = 5000 * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

        setTimeout(async () => {
            try {
                if (this.client) {
                    await this.client.destroy();
                }
                await this.initialize();
            } catch (error) {
                console.error(`Reconnection attempt ${this.reconnectAttempts} failed:`, error);
                this.attemptReconnect(`Reconnection failed: ${error.message}`);
            }
        }, delay);
    }

    async initialize() {
        if (this.isConnecting || this.isConnected) {
            console.log('WhatsApp is already connecting or connected');
            return;
        }

        this.isConnecting = true;
        console.log('Initializing WhatsApp client...');

        try {
            await this.client.initialize();
        } catch (error) {
            console.error('Failed to initialize WhatsApp client:', error);
            this.isConnecting = false;
            throw error;
        }
    }
}

// Start the client
const client = new WhatsAppClient();
client.initialize().catch(console.error);

// Handle process termination
process.on('SIGINT', () => {
    console.log('Shutting down WhatsApp client...');
    if (client.client) {
        client.client.destroy();
    }
    process.exit(0);
});
