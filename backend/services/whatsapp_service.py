# backend/app/services/whatsapp_service.py
import asyncio
import json
import subprocess
import os
import signal
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile
from pathlib import Path

from core.config import settings
from database.models import Chat, Message, MessageType
from database.database import get_db
from services.llm_service import LLMService

class WhatsAppService:
    """
    WhatsApp service that manages a Node.js subprocess running whatsapp-web.js
    """

    def __init__(self, connection_manager=None):
        self.process: Optional[subprocess.Popen] = None
        self.is_connected = False
        self.is_connecting = False
        self.qr_code = None
        self.session_path = settings.WHATSAPP_SESSION_PATH
        self.node_script_path = settings.WHATSAPP_NODE_SCRIPT_PATH
        self.llm_service = None  # Will be injected
        self.connection_manager = connection_manager  # WebSocket manager

        # Ensure directories exist
        Path(self.session_path).mkdir(parents=True, exist_ok=True)
        Path(settings.MEDIA_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
    
    def set_llm_service(self, llm_service: LLMService):
        """Set LLM service reference"""
        self.llm_service = llm_service
    
    async def initialize(self) -> bool:
        """Initialize WhatsApp service"""
        if self.process and self.process.poll() is None:
            print("WhatsApp process already running")
            return True

        try:
            print("🚀 Starting WhatsApp Node.js process...")
            self.is_connecting = True

            # Broadcast connecting status
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"connecting": True, "connected": False}
                })
            
            # Create Node.js script if it doesn't exist
            await self.create_node_script()
            
            # Start Node.js process
            env = os.environ.copy()
            env.update({
                'SESSION_PATH': self.session_path,
                'MEDIA_PATH': settings.MEDIA_DOWNLOAD_PATH,
                'PYTHON_CALLBACK_URL': f"http://localhost:{settings.PORT}/api/whatsapp/callback"
            })
            
            self.process = subprocess.Popen(
                ['node', self.node_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            print(f"✅ WhatsApp process started with PID: {self.process.pid}")
            
            # Start monitoring the process
            asyncio.create_task(self.monitor_process())
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start WhatsApp process: {e}")
            self.is_connecting = False
            return False
    
    async def create_node_script(self):
        """Create the Node.js WhatsApp integration script"""
        script_content = '''
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
                const commands = data.trim().split('\\n');
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
                        reconnectAttempts: this.reconnectAttempts
                    };
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
'''
        
        # Write the script to file
        os.makedirs(os.path.dirname(self.node_script_path), exist_ok=True)
        with open(self.node_script_path, 'w') as f:
            f.write(script_content)
        
        # Create package.json if it doesn't exist
        package_json_path = os.path.join(os.path.dirname(self.node_script_path), 'package.json')
        if not os.path.exists(package_json_path):
            package_json = {
                "name": "whatsapp-secretary-node",
                "version": "1.0.0",
                "dependencies": {
                    "whatsapp-web.js": "^1.23.0",
                    "axios": "^1.6.0"
                }
            }
            with open(package_json_path, 'w') as f:
                json.dump(package_json, f, indent=2)
            
            print("📦 Installing Node.js dependencies...")
            subprocess.run(['npm', 'install'], cwd=os.path.dirname(self.node_script_path))
    
    async def monitor_process(self):
        """Monitor the Node.js process"""
        if not self.process:
            return
        
        try:
            while self.process.poll() is None:
                output = self.process.stdout.readline()
                if output:
                    line = output.strip()
                    print(f"WhatsApp: {line}")
                    
                    # Parse Python responses
                    if line.startswith('PYTHON_RESPONSE:'):
                        response_json = line[16:]  # Remove prefix
                        try:
                            response = json.loads(response_json)
                            # Handle response
                        except json.JSONDecodeError:
                            pass
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"Error monitoring WhatsApp process: {e}")
        
        print("WhatsApp process ended")
        self.is_connected = False
        self.is_connecting = False
    
    async def send_command(self, action: str, data: dict = None) -> dict:
        """Send command to Node.js process"""
        if not self.process or self.process.poll() is not None:
            raise Exception("WhatsApp process not running")
        
        command = {
            "action": action,
            "data": data or {},
            "id": f"{action}_{datetime.now().timestamp()}"
        }
        
        command_json = json.dumps(command) + "\\n"
        self.process.stdin.write(command_json)
        self.process.stdin.flush()
        
        # In a real implementation, you'd wait for the response
        # For now, we'll return a success indicator
        return {"success": True, "command_id": command["id"]}
    
    async def send_message(self, chat_id: str, message: str, media_path: str = None) -> dict:
        """Send message via WhatsApp"""
        return await self.send_command("send_message", {
            "chatId": chat_id,
            "message": message,
            "mediaPath": media_path
        })
    
    async def get_chats(self) -> List[dict]:
        """Get all chats"""
        result = await self.send_command("get_chats")
        # In real implementation, parse the response
        return []
    
    async def get_chat_messages(self, chat_id: str, limit: int = 50) -> List[dict]:
        """Get messages from a specific chat"""
        result = await self.send_command("get_chat_messages", {
            "chatId": chat_id,
            "limit": limit
        })
        return []
    
    async def handle_callback(self, event: str, data: dict):
        """Handle callbacks from Node.js process"""
        print(f"WhatsApp callback: {event}")

        if event == "qr_code":
            self.qr_code = data.get("qr")
            # Broadcast QR code to connected clients
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "qr_code",
                    "data": {"qr": self.qr_code}
                })

        elif event == "ready":
            self.is_connected = True
            self.is_connecting = False
            print("✅ WhatsApp connected and ready")
            # Broadcast status update
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"connected": True, "connecting": False}
                })

        elif event == "authenticated":
            print("✅ WhatsApp authenticated")
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"authenticated": True}
                })

        elif event == "auth_failure":
            self.is_connecting = False
            print(f"❌ WhatsApp authentication failed: {data.get('message')}")
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"connected": False, "connecting": False, "error": data.get('message')}
                })

        elif event == "disconnected":
            self.is_connected = False
            self.is_connecting = False
            print(f"📱 WhatsApp disconnected: {data.get('reason')}")
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "whatsapp_status",
                    "data": {"connected": False, "connecting": False, "disconnected_reason": data.get('reason')}
                })

        elif event == "new_message":
            await self.process_new_message(data)
            # Broadcast new message
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "new_message",
                    "data": data
                })

        elif event == "message_sent":
            print(f"✅ Message sent to {data.get('chatId')}")
            if self.connection_manager:
                await self.connection_manager.broadcast({
                    "type": "message_sent",
                    "data": data
                })
    
    async def process_new_message(self, message_data: dict):
        """Process new incoming message"""
        try:
            # Save to database
            db = next(get_db())
            
            # Ensure chat exists
            chat = db.query(Chat).filter(Chat.id == message_data["chatId"]).first()
            if not chat:
                chat = Chat(
                    id=message_data["chatId"],
                    name=f"Chat {message_data['chatId'][:10]}",
                    phone_number=message_data["chatId"].split("@")[0]
                )
                db.add(chat)
                db.commit()
            
            # Save message
            message = Message(
                id=message_data["id"],
                chat_id=message_data["chatId"],
                body=message_data.get("body", ""),
                message_type=MessageType(message_data.get("type", "text")),
                from_me=message_data.get("fromMe", False),
                timestamp=datetime.fromtimestamp(message_data["timestamp"]),
                has_media=message_data.get("hasMedia", False),
                media_path=message_data.get("mediaPath")
            )
            db.add(message)
            db.commit()
            
            # Process with LLM if not from me
            if not message_data.get("fromMe", False) and self.llm_service:
                await self.process_message_with_llm(message_data)
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    async def process_message_with_llm(self, message_data: dict):
        """Process message with LLM and potentially respond"""
        try:
            message_body = message_data.get("body", "").strip()
            chat_id = message_data["chatId"]
            
            if not message_body:
                return
            
            # Check if this looks like an appointment request
            appointment_keywords = [
                "appointment", "book", "schedule", "reserve", "meeting",
                "available", "time", "date", "calendar"
            ]
            
            if any(keyword in message_body.lower() for keyword in appointment_keywords):
                # Process as appointment request
                appointment_data = await self.llm_service.process_appointment_request(message_body, chat_id)
                
                if appointment_data and appointment_data.get("confidence", 0) > 0.7:
                    # High confidence appointment request
                    response = await self.llm_service.generate_appointment_confirmation(appointment_data)
                    await self.send_message(chat_id, response)
                    return
            
            # Generate general response
            llm_response = await self.llm_service.generate_response(message_body, chat_id)
            
            if llm_response and llm_response.get("response"):
                await self.send_message(chat_id, llm_response["response"])
                
        except Exception as e:
            print(f"Error processing message with LLM: {e}")
    
    async def get_status(self) -> dict:
        """Get WhatsApp service status"""
        return {
            "connected": self.is_connected,
            "connecting": self.is_connecting,
            "process_running": self.process is not None and self.process.poll() is None,
            "has_qr_code": self.qr_code is not None,
            "session_exists": os.path.exists(self.session_path)
        }
    
    async def disconnect(self):
        """Disconnect WhatsApp"""
        if self.process:
            try:
                self.process.send_signal(signal.SIGTERM)
                await asyncio.sleep(2)
                if self.process.poll() is None:
                    self.process.kill()
            except Exception as e:
                print(f"Error terminating WhatsApp process: {e}")
            
            self.process = None
        
        self.is_connected = False
        self.is_connecting = False
        self.qr_code = None
    
    async def cleanup(self):
        """Cleanup WhatsApp service"""
        await self.disconnect()
        print("📱 WhatsApp service cleaned up")