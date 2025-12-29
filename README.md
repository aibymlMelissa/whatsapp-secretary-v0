# WhatsApp Secretary AI

> An intelligent AI-powered WhatsApp assistant that manages conversations, schedules appointments, and provides secure two-factor authorization for sensitive operations.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/react-18+-61DAFB.svg)](https://reactjs.org/)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Security Features](#security-features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

WhatsApp Secretary AI is a comprehensive business assistant that automates WhatsApp communication through AI-powered responses. Built with FastAPI (Python), React (TypeScript), and WhatsApp Web.js (Node.js), it provides intelligent conversation management, appointment scheduling, and secure authorization workflows.

### What It Does

- **Intelligent Responses**: AI-powered conversation handling with context awareness
- **Appointment Management**: Automatic appointment booking, reminders, and scheduling
- **Secure Authorization**: Two-factor authentication for sensitive operations (password + phone number)
- **Real-time Sync**: WebSocket-based instant message updates across all clients
- **Multi-LLM Support**: Works with OpenAI GPT-4, Google Gemini, Anthropic Claude, and Ollama

---

## Key Features

### 1. Smart Message Processing

- **Bidirectional Communication**: Full send and receive capability via HTTP bridge
- **Context-Aware Responses**: Maintains conversation history for relevant replies
- **Media Support**: Handles images, videos, documents, and audio messages
- **Auto-Response**: Configurable AI responses based on whitelist and settings

### 2. Advanced Security

- **Password-Based Authorization**: Requires specific password in message for privileged access
- **Phone Number Verification**: Only authorized phone numbers can access protected features
- **Whitelist Control**: Per-chat AI enable/disable with whitelist protection
- **Audit Trail**: Complete message and authorization history in database

### 3. Appointment System

- **Natural Language Booking**: "I need an appointment tomorrow at 3pm" → Automatic scheduling
- **Smart Date/Time Extraction**: AI parses dates, times, and durations from messages
- **Conflict Detection**: Prevents double-booking with intelligent scheduling
- **Reminders**: Automated appointment reminders (configurable timing)

### 4. Developer-Friendly

- **REST API**: Comprehensive FastAPI backend with auto-generated docs
- **WebSocket Support**: Real-time bidirectional communication
- **Type-Safe Frontend**: Full TypeScript with strict type checking
- **Modular Architecture**: Easily extensible service-based design

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL WHATSAPP USER                      │
│                    (Sends message via WhatsApp)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  NODE.JS LAYER - WhatsApp Bridge (Port 8002)                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • whatsapp-web.js: Receives messages from WhatsApp Web         │
│  • Express HTTP Server: Listens for send requests               │
│  • File-based Status: Updates status.json & qr_code.txt         │
│  • Callback System: POSTs messages to Python backend            │
└─────────────────────────────────────────────────────────────────┘
                ↓ HTTP POST                    ↑ HTTP POST
                (new messages)                 (send responses)
┌─────────────────────────────────────────────────────────────────┐
│  PYTHON BACKEND - FastAPI (Port 8001)                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • WhatsApp Service: Message processing & authorization check   │
│  • LLM Service: AI response generation (OpenAI/Gemini/Claude)   │
│  • Database: SQLite/PostgreSQL for persistence                  │
│  • WebSocket Manager: Real-time updates to frontend             │
└─────────────────────────────────────────────────────────────────┘
                              ↓ WebSocket
┌─────────────────────────────────────────────────────────────────┐
│  REACT FRONTEND (Port 3005)                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • Chat Interface: Message display & input                      │
│  • Real-time Updates: WebSocket-based sync                      │
│  • Control Panel: AI toggle, whitelist management               │
│  • QR Code Display: WhatsApp connection authentication          │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript | Modern, type-safe UI |
| **State Management** | Zustand | Lightweight state management |
| **Styling** | TailwindCSS + Shadcn/UI | Beautiful, responsive components |
| **Build Tool** | Vite | Fast development and builds |
| **Backend API** | FastAPI (Python 3.10+) | High-performance async framework |
| **Database** | SQLite / PostgreSQL | Persistent data storage |
| **ORM** | SQLAlchemy | Database abstraction |
| **WhatsApp Client** | whatsapp-web.js (Node.js) | WhatsApp Web integration |
| **Bridge Server** | Express.js | HTTP server for message sending |
| **LLM Providers** | OpenAI, Gemini, Claude, Ollama | AI response generation |
| **Real-time** | WebSocket (uvicorn) | Bidirectional communication |

---

## Security Features

### 1. Password-Based Authorization System

**Configuration:**
- Authorized Phone Number: `+852 90511427` (AIbyML.com HK)
- Required Password: `AI((99mlMeta` (configurable in `.env`)

**How It Works:**
```python
# In message: "AI((99mlMeta - What appointments do we have today?"
# ✓ Phone number matches: +852 90511427
# ✓ Password found in message: AI((99mlMeta
# → FULL ACCESS GRANTED

# Without password or wrong phone:
# → Returns generic response: "Sorry, Mr Hung is not available..."
```

**Implementation:**
- `services/llm_service.py:466-528` - System prompt with authorization rules
- `services/whatsapp_service.py:595-725` - Phone number extraction and context building
- `.env` - `BOSS_PHONE_NUMBER`, `AUTHORIZATION_PASSWORD` configuration

### 2. Whitelist-Based AI Processing

- **Default:** AI disabled for all new chats
- **Control:** Manual whitelist toggle in UI (shield icon)
- **Protection:** Prevents unauthorized AI resource consumption
- **Granular:** Per-chat enable/disable for fine-grained control

### 3. Message Sending Security

**Two-Way Communication Architecture:**
```
┌──────────────────────────────────────────────────────────────┐
│  RECEIVING MESSAGES (WhatsApp → Python)                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  1. WhatsApp Web.js receives message                         │
│  2. Node.js POST to http://localhost:8001/api/whatsapp/callback│
│  3. Python saves to DB & processes with LLM                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  SENDING MESSAGES (Python → WhatsApp)                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  1. Python generates LLM response                            │
│  2. Python POST to http://localhost:8002/send                │
│  3. Express server receives {chatId, message}                │
│  4. Node.js sends via whatsapp-web.js                        │
└──────────────────────────────────────────────────────────────┘
```

**Key Files:**
- `backend/whatsapp_client/simple_bridge.js:226-255` - Express HTTP server on port 8002
- `backend/services/whatsapp_service.py:206-224` - HTTP POST message sending

### 4. Audit Trail

All interactions logged in database:
- **Message Table**: Full message history with timestamps
- **ConversationHistory**: LLM interactions with response times
- **Chat Table**: Contact info, AI status, whitelist status

---

## Quick Start

### Prerequisites

- **Python 3.10+** - Backend runtime
- **Node.js 18+** - WhatsApp client runtime
- **LLM Provider** - OpenAI API key or Google Gemini API key (or run Ollama locally)

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/aibymlMelissa/WhatsApp-Secretary-First-Trial.git
cd WhatsApp-Secretary-First-Trial
```

2. **Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
# Copy example and edit with your settings
cp .env.example .env

# Required settings in .env:
OPENAI_API_KEY=sk-...                    # Your OpenAI API key
GEMINI_API_KEY=your_gemini_key          # Or Google Gemini key
BOSS_PHONE_NUMBER=+85290511427          # Authorized phone number
AUTHORIZATION_PASSWORD=AI((99mlMeta     # Access password
```

4. **WhatsApp Client Setup**
```bash
cd backend/whatsapp_client
npm install
```

5. **Frontend Setup**
```bash
cd ../../frontend
npm install
cp .env.example .env.local

# Edit .env.local:
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
```

6. **Start the Application**

**Option A: Manual Start (3 terminals)**
```bash
# Terminal 1 - Backend API
cd backend
venv/bin/uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - WhatsApp Bridge
cd backend/whatsapp_client
node simple_bridge.js

# Terminal 3 - Frontend
cd frontend
npm run dev
```

**Option B: Using Start Script**
```bash
chmod +x start_dev.sh
./start_dev.sh
```

7. **Access the Application**
- Frontend UI: http://localhost:3005
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- WhatsApp Bridge: http://localhost:8002 (internal)

---

## Configuration

### Environment Variables

**Backend (.env)**
```bash
# Database
DATABASE_URL=sqlite:///./whatsapp_secretary.db

# Authorization System
BOSS_PHONE_NUMBER=+85290511427           # Authorized phone number
BOSS_CONTACT_NAME=AIbyML.com HK          # Display name for authorized user
AUTHORIZATION_PASSWORD=AI((99mlMeta      # Required password for full access
UNAUTHORIZED_MESSAGE=Sorry, Mr Hung is not available at this moment...

# LLM Providers (choose one or more)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# WhatsApp Client
PYTHON_CALLBACK_URL=http://localhost:8001/api/whatsapp/callback
WHATSAPP_BRIDGE_URL=http://localhost:8002
```

**Frontend (.env.local)**
```bash
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
```

### Authorization System Configuration

The authorization system uses **both** phone number and password verification:

1. **Authorized Phone Number**: Only this number gets full access
   - Configure: `BOSS_PHONE_NUMBER=+85290511427` in `.env`
   - Format: International format with + (e.g., +852 90511427)

2. **Required Password**: Must be included in message text
   - Configure: `AUTHORIZATION_PASSWORD=AI((99mlMeta` in `.env`
   - Usage: User types "AI((99mlMeta - [their question]"
   - Security: Without this password, even authorized number gets generic response

3. **Unauthorized Message**: Response for non-authorized requests
   - Configure: `UNAUTHORIZED_MESSAGE=...` in `.env`
   - Default: "Sorry, Mr Hung is not available at this moment..."

**Example Messages:**

```
❌ UNAUTHORIZED (wrong phone number):
   From: +85212345678
   Message: "What's your schedule?"
   Response: "Sorry, Mr Hung is not available..."

❌ UNAUTHORIZED (authorized phone, no password):
   From: +85290511427
   Message: "What appointments do we have?"
   Response: "Sorry, Mr Hung is not available..."

✅ AUTHORIZED (phone + password):
   From: +85290511427
   Message: "AI((99mlMeta - What appointments do we have today?"
   Response: [Full detailed response with appointment information]
```

---

## Usage Guide

### 1. Connect WhatsApp

1. Start all services (backend, frontend, WhatsApp bridge)
2. Open http://localhost:3005 in your browser
3. Scan the QR code with your WhatsApp mobile app:
   - Open WhatsApp → Settings → Linked Devices → Link a Device
4. Wait for "Connected" status (green indicator)

### 2. Configure Chat for AI

1. Select a chat from the chat list
2. Click the **"Trusted"** button (shield icon) to whitelist the contact
3. Click the **"AI On"** button (bot icon) to enable AI responses
4. Both must be enabled for AI to process messages

### 3. Test Authorization System

**Test 1: Unauthorized Phone Number**
```
Send from: Any phone except +85290511427
Message: "What's your schedule for tomorrow?"
Expected: "Sorry, Mr Hung is not available at this moment..."
```

**Test 2: Authorized Phone Without Password**
```
Send from: +85290511427
Message: "Show me today's appointments"
Expected: "Sorry, Mr Hung is not available..." (no password provided)
```

**Test 3: Authorized Phone With Password**
```
Send from: +85290511427
Message: "AI((99mlMeta - What appointments do we have today?"
Expected: Detailed AI response with appointment information
```

### 4. Appointment Booking Example

**User Message:**
```
"Hi, I'd like to book an appointment for tomorrow at 3pm"
```

**AI Processing:**
1. Detects appointment keywords: "book", "appointment"
2. Extracts date: Tomorrow (2025-12-30)
3. Extracts time: 3:00 PM
4. Creates appointment in database
5. Generates confirmation message

**AI Response:**
```
"I've scheduled your appointment for tomorrow, December 30th at 3:00 PM.
You'll receive a reminder 1 hour before. Is there anything else I can help you with?"
```

---

## API Reference

### WhatsApp Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/whatsapp/connect` | Start WhatsApp connection |
| `POST` | `/api/whatsapp/disconnect` | Stop WhatsApp connection |
| `GET` | `/api/whatsapp/status` | Get connection status |
| `GET` | `/api/whatsapp/qr` | Get QR code for authentication |
| `POST` | `/api/whatsapp/callback` | Receive messages from Node.js bridge |
| `POST` | `/api/whatsapp/send-message` | Send message (via HTTP bridge) |

### Chat Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/whatsapp/chats` | List all chats |
| `GET` | `/api/whatsapp/chats/{chat_id}/messages` | Get chat messages |
| `POST` | `/api/whatsapp/chats/{chat_id}/toggle-ai` | Enable/disable AI |
| `POST` | `/api/whatsapp/chats/{chat_id}/toggle-whitelist` | Whitelist toggle |

### WebSocket Events

| Event | Direction | Data | Description |
|-------|-----------|------|-------------|
| `whatsapp_status` | Server → Client | `{connected, ready, qr_code}` | Connection status |
| `qr_code` | Server → Client | `{qr_code}` | QR code for scanning |
| `new_message` | Server → Client | `{chat_id, message, ...}` | New message received |
| `message_sent` | Server → Client | `{chat_id, success}` | Message sent confirmation |

Full API documentation available at: http://localhost:8001/docs (when backend is running)

---

## Troubleshooting

### WhatsApp Not Connecting

**Symptoms:** QR code not appearing or connection fails

**Solutions:**
1. Check Node.js process is running:
   ```bash
   ps aux | grep node
   ```
2. Check backend logs for errors:
   ```bash
   tail -f backend/logs/backend.log
   ```
3. Delete session and reconnect:
   ```bash
   rm -rf backend/whatsapp_client/whatsapp-session
   rm backend/whatsapp_client/qr_code.txt
   # Restart backend and scan QR again
   ```

### AI Not Responding to Messages

**Symptoms:** Messages received but no AI response

**Checklist:**
- [ ] Is the chat **whitelisted**? (Shield icon shows "Trusted")
- [ ] Is AI **enabled** for the chat? (Bot icon shows "AI On")
- [ ] Is the WhatsApp bridge running? (Check port 8002)
- [ ] Check backend logs for LLM errors

**Test Message Sending:**
```bash
# Test if bridge is running
curl http://localhost:8002/send \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"chatId":"YOUR_CHAT_ID@c.us","message":"Test"}'
```

### Authorization Not Working

**Symptoms:** Authorized phone number getting generic responses

**Checklist:**
1. Verify phone number format in `.env`:
   ```bash
   # Correct
   BOSS_PHONE_NUMBER=+85290511427

   # Wrong
   BOSS_PHONE_NUMBER=85290511427  # Missing +
   BOSS_PHONE_NUMBER=+852 905 114 27  # Has spaces
   ```

2. Verify password is in message:
   ```
   ✓ "AI((99mlMeta - What's my schedule?"
   ✗ "What's my schedule?"  # No password
   ```

3. Check LLM service logs:
   ```bash
   # Look for authorization status in logs
   grep "Authorization Status" backend/logs/backend.log
   ```

### Port Already in Use

**Symptoms:** Error: `EADDRINUSE: address already in use :::8001`

**Solutions:**
```bash
# Kill process on port 8001
lsof -t -i:8001 | xargs kill -9

# Kill process on port 8002
lsof -t -i:8002 | xargs kill -9

# Kill process on port 3005
lsof -t -i:3005 | xargs kill -9
```

### Database Locked

**Symptoms:** `database is locked` error

**Solutions:**
```bash
# Close all connections and restart
pkill -9 python
rm backend/whatsapp_secretary.db-wal
rm backend/whatsapp_secretary.db-shm
# Restart backend
```

---

## Project Structure

```
whatsapp-secretary-ai/
├── backend/
│   ├── app.py                          # FastAPI application entry point
│   ├── core/
│   │   └── config.py                   # Configuration and environment variables
│   ├── database/
│   │   ├── database.py                 # Database connection setup
│   │   └── models.py                   # SQLAlchemy data models
│   ├── routers/
│   │   ├── whatsapp.py                 # WhatsApp API endpoints
│   │   ├── appointments.py             # Appointment management
│   │   └── llm.py                      # LLM endpoints
│   ├── services/
│   │   ├── whatsapp_service.py         # WhatsApp business logic
│   │   ├── llm_service.py              # LLM integration & authorization
│   │   ├── authorization_service.py    # Legacy 2FA (not used in current version)
│   │   └── user_service.py             # User management
│   ├── whatsapp_client/
│   │   ├── simple_bridge.js            # Node.js WhatsApp bridge with HTTP server
│   │   ├── package.json                # Node.js dependencies
│   │   └── whatsapp-session/           # WhatsApp session data (auto-created)
│   └── websocket/
│       └── manager.py                  # WebSocket connection manager
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── WhatsApp/
│   │   │       ├── ChatList.tsx        # Chat list component
│   │   │       ├── ChatWindow.tsx      # Chat window with messages
│   │   │       └── ConnectionStatus.tsx # WhatsApp status indicator
│   │   ├── services/
│   │   │   ├── api.ts                  # HTTP API client
│   │   │   └── websocket.ts            # WebSocket client
│   │   ├── store/
│   │   │   └── whatsapp.ts             # Zustand state management
│   │   └── types/
│   │       └── index.ts                # TypeScript type definitions
│   ├── package.json                    # Frontend dependencies
│   └── vite.config.ts                  # Vite build configuration
├── .env                                # Backend environment variables
├── .env.example                        # Example backend configuration
├── frontend/.env.local                 # Frontend environment variables
├── frontend/.env.example               # Example frontend configuration
├── README.md                           # This file
├── AUTHORIZATION_SYSTEM_REPORT.md      # Detailed authorization test report
└── package.json                        # Root package.json for scripts
```

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines

- **Code Style**: Follow PEP 8 for Python, ESLint config for TypeScript
- **Type Safety**: Use type hints in Python, strict TypeScript
- **Testing**: Add tests for new features
- **Documentation**: Update README and inline comments
- **Security**: Never commit API keys or sensitive data

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/aibymlMelissa/WhatsApp-Secretary-First-Trial/issues)
- **Documentation**: See `AUTHORIZATION_SYSTEM_REPORT.md` for detailed test results
- **Email**: [Your support email]

---

## Acknowledgments

- **whatsapp-web.js** - WhatsApp Web API integration
- **FastAPI** - Modern Python web framework
- **React** - UI library
- **OpenAI** - GPT-4 API
- **Google** - Gemini API
- **Anthropic** - Claude API

---

## Changelog

### Version 2.0.0 (2025-12-29)

**Major Changes:**
- ✨ **Added HTTP-based message sending** - Fixed AI response delivery
  - Express HTTP server on port 8002 in Node.js bridge
  - Python sends messages via HTTP POST instead of stdin
  - Bidirectional communication now fully functional

- 🔒 **Implemented password-based authorization system**
  - Requires both phone number (+852 90511427) and password (AI((99mlMeta)
  - LLM-based authorization check in system prompt
  - Generic response for unauthorized requests

- 🐛 **Bug Fixes:**
  - Fixed message sending functionality (messages now actually send!)
  - Fixed WhatsApp bridge initialization issues
  - Cleaned up session management and process handling

**Files Modified:**
- `backend/whatsapp_client/simple_bridge.js` - Added Express server (lines 226-255)
- `backend/services/whatsapp_service.py` - Updated send_message() (lines 206-224)
- `backend/services/llm_service.py` - Added authorization prompt (lines 466-528)
- `backend/core/config.py` - Fixed .env path loading

### Version 1.0.0 (2024-10-04)

- Initial release with basic WhatsApp integration
- AI-powered responses with multiple LLM providers
- Appointment scheduling system
- Real-time WebSocket updates
- React frontend with TypeScript

---

**Last Updated:** December 29, 2025
**Repository:** [WhatsApp-Secretary-First-Trial](https://github.com/aibymlMelissa/WhatsApp-Secretary-First-Trial)
**Maintained by:** AIbyML.com
