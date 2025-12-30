// whatsapp/whatsappManager.ts
import { Client, LocalAuth, Message, MessageMedia } from 'whatsapp-web.js';
import { Server } from 'socket.io';
import qrcode from 'qrcode-terminal';
import { EventEmitter } from 'events';
import fs from 'fs/promises';
import path from 'path';

export class WhatsAppManager extends EventEmitter {
  private client: Client | null = null;
  private io: Server;
  private isConnected = false;
  private isConnecting = false;

  constructor(io: Server) {
    super();
    this.io = io;
  }

  async initialize(): Promise<void> {
    if (this.isConnecting || this.isConnected) {
      throw new Error('WhatsApp is already connected or connecting');
    }

    this.isConnecting = true;

    try {
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

      this.setupEventHandlers();
      await this.client.initialize();
    } catch (error) {
      this.isConnecting = false;
      throw error;
    }
  }

  private setupEventHandlers(): void {
    if (!this.client) return;

    this.client.on('qr', (qr: string) => {
      console.log('QR Code received, scan with your phone:');
      qrcode.generate(qr, { small: true });

      this.io.emit('qrCode', { qr });
    });

    this.client.on('ready', () => {
      console.log('WhatsApp Client is ready!');
      this.isConnected = true;
      this.isConnecting = false;

      this.io.emit('whatsappStatus', { status: 'connected' });
    });

    this.client.on('authenticated', () => {
      console.log('WhatsApp Client authenticated');
      this.io.emit('whatsappStatus', { status: 'authenticated' });
    });

    this.client.on('auth_failure', (msg: string) => {
      console.error('Authentication failed:', msg);
      this.isConnecting = false;
      this.io.emit('whatsappStatus', { status: 'auth_failed', message: msg });
    });

    this.client.on('disconnected', (reason: string) => {
      console.log('WhatsApp Client disconnected:', reason);
      this.isConnected = false;
      this.isConnecting = false;
      this.io.emit('whatsappStatus', { status: 'disconnected', reason });
    });

    this.client.on('message', (message: Message) => {
      this.emit('message', message);
    });

    this.client.on('message_create', (message: Message) => {
      // Handle sent messages
      if (message.fromMe) {
        this.io.emit('messageSent', {
          chatId: message.to,
          message: message.body,
          timestamp: new Date().toISOString()
        });
      }
    });
  }

  async sendMessage(chatId: string, text: string, mediaPath?: string): Promise<void> {
    if (!this.client || !this.isConnected) {
      throw new Error('WhatsApp client is not connected');
    }

    try {
      if (mediaPath) {
        // Send media message
        const media = MessageMedia.fromFilePath(mediaPath);
        await this.client.sendMessage(chatId, media, { caption: text || undefined });
      } else {
        // Send text message
        await this.client.sendMessage(chatId, text);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  async getChats(): Promise<any[]> {
    if (!this.client || !this.isConnected) {
      throw new Error('WhatsApp client is not connected');
    }

    try {
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
    } catch (error) {
      console.error('Error getting chats:', error);
      throw error;
    }
  }

  async getChatMessages(chatId: string, limit: number = 50): Promise<any[]> {
    if (!this.client || !this.isConnected) {
      throw new Error('WhatsApp client is not connected');
    }

    try {
      const chat = await this.client.getChatById(chatId);
      const messages = await chat.fetchMessages({ limit });

      return messages.map(msg => ({
        id: msg.id._serialized,
        body: msg.body,
        timestamp: msg.timestamp,
        fromMe: msg.fromMe,
        hasMedia: msg.hasMedia,
        type: msg.type,
        author: msg.author
      }));
    } catch (error) {
      console.error('Error getting chat messages:', error);
      throw error;
    }
  }

  async downloadMedia(message: Message): Promise<string | null> {
    try {
      if (!message.hasMedia) return null;

      const media = await message.downloadMedia();
      const fileName = `${Date.now()}_${message.from.replace('@', '_')}.${media.mimetype.split('/')[1]}`;
      const filePath = path.join(__dirname, '../downloads', fileName);

      // Ensure downloads directory exists
      await fs.mkdir(path.dirname(filePath), { recursive: true });

      // Convert base64 to buffer and save
      const buffer = Buffer.from(media.data, 'base64');
      await fs.writeFile(filePath, buffer);

      return fileName;
    } catch (error) {
      console.error('Error downloading media:', error);
      return null;
    }
  }

  async searchMessages(query: string, chatId?: string): Promise<any[]> {
    if (!this.client || !this.isConnected) {
      throw new Error('WhatsApp client is not connected');
    }

    try {
      // This is a basic implementation - WhatsApp Web.js doesn't have built-in search
      // You might need to implement your own search logic by fetching messages and filtering
      const chats = chatId ? [await this.client.getChatById(chatId)] : await this.client.getChats();
      const results: any[] = [];

      for (const chat of chats) {
        const messages = await chat.fetchMessages({ limit: 100 });
        const filtered = messages.filter(msg =>
          msg.body.toLowerCase().includes(query.toLowerCase())
        );

        results.push(...filtered.map(msg => ({
          id: msg.id._serialized,
          chatId: chat.id._serialized,
          chatName: chat.name,
          body: msg.body,
          timestamp: msg.timestamp,
          fromMe: msg.fromMe
        })));
      }

      return results.slice(0, 50); // Limit results
    } catch (error) {
      console.error('Error searching messages:', error);
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (this.client) {
      await this.client.destroy();
      this.client = null;
      this.isConnected = false;
      this.isConnecting = false;
    }
  }

  getStatus(): any {
    return {
      connected: this.isConnected,
      connecting: this.isConnecting,
      hasClient: !!this.client
    };
  }
}

export default WhatsAppManager;