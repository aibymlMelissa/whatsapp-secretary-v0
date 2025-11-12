# WhatsApp Secretary AI

## Project Description

An AI-powered WhatsApp Secretary application built with FastAPI backend and React frontend, designed to intelligently manage WhatsApp conversations with automated responses, appointment booking, and secure authorization workflows.

The application serves as an intelligent business assistant that:
- Manages WhatsApp conversations with AI-powered responses
- Handles appointment scheduling and reminders
- Implements secure two-factor authorization for sensitive operations
- Provides real-time message synchronization via WebSocket
- Supports multiple LLM providers (Ollama, Google Gemini, OpenAI, Anthropic)

---

## Architecture Overview

### Technology Stack

**Backend:**
- FastAPI (Python) - High-performance async API framework
- SQLite/PostgreSQL - Database for chat and message storage
- whatsapp-web.js (Node.js) - WhatsApp Web integration
- Google Gemini & Ollama - LLM providers for AI responses
- WebSocket - Real-time bidirectional communication

**Frontend:**
- React + TypeScript - Modern UI framework
- Vite - Fast development and build tool
- Zustand - State management
- TailwindCSS - Utility-first styling
- Shadcn/UI - Component library

**Communication:**
- HTTP REST API - Request/response operations
- WebSocket - Real-time updates (QR codes, messages, status)
- File-based IPC - Node.js ↔ Python communication

---

## Message Flow: External WhatsApp Number → LLM Response

### Summary Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  EXTERNAL WHATSAPP MESSAGE (e.g., 85260552717)                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  1. NODE.JS LAYER - WhatsApp Client                                 │
│  📍 whatsapp_client.js:104-160                                      │
│  • Receives message via whatsapp-web.js                             │
│  • Extracts message data (chatId, body, timestamp, media)           │
│  • Downloads media if hasMedia=true                                 │
│  • Sends HTTP POST to Python backend callback                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  2. PYTHON BACKEND - Callback Handler                               │
│  📍 routers/whatsapp.py:80-97                                       │
│  • Receives callback with event="new_message"                       │
│  • Delegates to WhatsAppService.handle_callback()                   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  3. WHATSAPP SERVICE - Message Processing                           │
│  📍 whatsapp_service.py:343-416                                     │
│  • Saves message to database (Chat + Message tables)                │
│  • Checks if sender is BOSS (authorization response)                │
│  • Validates chat.ai_enabled && chat.is_whitelisted                 │
│  • If whitelisted → process_message_with_llm()                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  4. DATABASE SAVE                                                   │
│  📍 whatsapp_service.py:418-494                                     │
│  • Creates Chat record (if new contact)                             │
│  • Creates Message record with llm_processed=False                  │
│  • Stores: id, chat_id, body, timestamp, from_me, etc.              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  5. LLM PROCESSING DECISION                                         │
│  📍 whatsapp_service.py:594-626                                     │
│  • Detects appointment keywords → appointment flow                  │
│  • Otherwise → general conversational response                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  6. LLM SERVICE - Response Generation                               │
│  📍 llm_service.py:89-173                                           │
│  • Auto-selects provider (Ollama/Gemini) based on complexity        │
│  • Loads conversation context from cache                            │
│  • Builds system prompt (business assistant persona)                │
│  • Calls LLM API with conversation history                          │
│  • Saves conversation to database                                   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  7. LLM API CALL                                                    │
│  📍 llm_service.py:175-290                                          │
│  • Ollama: POST to /api/chat with messages array                    │
│  • Gemini: Uses google.generativeai with chat history              │
│  • Returns AI-generated text response                               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  8. SEND RESPONSE VIA WHATSAPP                                      │
│  📍 whatsapp_service.py:206-212                                     │
│  • Sends command to Node.js via stdin                               │
│  • Node.js uses whatsapp-web.js to send message                     │
│  • Message appears in external user's WhatsApp                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  9. REAL-TIME UI UPDATES (WebSocket)                                │
│  📍 websocket.ts:56-63 → whatsapp.ts:157-191                        │
│                                                                       │
│  WebSocket Events Broadcasted:                                      │
│  • "new_message" → Updates ChatWindow (new incoming message)        │
│  • "message_sent" → Updates ChatWindow (outgoing confirmation)      │
│  • "whatsapp_status" → Updates ConnectionStatus component           │
│  • "qr_code" → Displays QR for authentication                       │
│                                                                       │
│  Frontend Updates:                                                  │
│  ✓ ChatList.tsx:88-92 - Shows unread badge                          │
│  ✓ ChatList.tsx:94-98 - Updates last message timestamp              │
│  ✓ ChatList.tsx:107-114 - Displays last message preview             │
│  ✓ ChatWindow.tsx:171-197 - Appends new message to chat             │
│  ✓ whatsapp.ts:165-185 - Adds message to Zustand store              │
│  ✓ whatsapp.ts:184 - Refreshes chat list (unread count, timestamp)  │
└─────────────────────────────────────────────────────────────────────┘
```

### UI Update Details

When a message flows through the system, the following UI components are updated in real-time:

**1. Chat List (ChatList.tsx)**
- Line 88-92: Updates unread count badge
- Line 94-98: Shows relative timestamp (e.g., "2 minutes ago")
- Line 107-114: Updates last message preview text
- Line 85-87: Displays whitelist shield icon if trusted

**2. Chat Window (ChatWindow.tsx)**
- Line 171-197: Appends new message bubble to conversation
- Line 174: Aligns message left (received) or right (sent)
- Line 176-181: Applies styling (gray for received, blue for sent)
- Line 183-185: Shows message body text
- Line 186-194: Displays message timestamp
- Line 29: Auto-scrolls to bottom when new message arrives

**3. WhatsApp Store (whatsapp.ts)**
- Line 165-185: WebSocket listener for "new_message" event
- Line 171-180: Creates Message object and adds to store
- Line 184: Triggers fetchChats() to refresh chat list
- Line 133-142: addMessage() updates messages state

**4. Connection Status (Implied)**
- Updates when "whatsapp_status" event received
- Shows connected/disconnected/connecting states

---

## Authorization Flow (Special Case)

For sensitive operations requiring BOSS approval:

```
User requests sensitive data (DB query, file access, appointments)
                    ↓
LLM detects sensitive operation request
                    ↓
authorization_service.py:63 - Creates PendingAuthorization record
                    ↓
Sends WhatsApp to BOSS number: "Reply with 'AIbyML.com' to approve"
                    ↓
BOSS sends authorization code via WhatsApp
                    ↓
authorization_service.py:139 - Validates response from BOSS
                    ↓
Approves request & executes original action
                    ↓
Sends confirmation to both BOSS and requester
```

**Key Security Feature:** Only messages from configured BOSS phone number matching exact auth code are accepted.

---

## Key Security Features

### 1. **Whitelist-Only AI Processing**
- **Location:** `whatsapp_service.py:402`
- **Description:** AI responses only enabled for chats with `is_whitelisted=True`
- **UI Control:** Shield button in ChatWindow.tsx:124-141 (Trusted/Untrusted toggle)
- **Protection:** Prevents unauthorized users from consuming AI resources

### 2. **Two-Factor Authorization for Sensitive Operations**
- **Service:** `authorization_service.py`
- **Flow:**
  1. LLM detects sensitive request (database, files, appointments)
  2. System creates pending authorization with unique request_id
  3. WhatsApp message sent to BOSS with auth code requirement
  4. BOSS must reply with exact phrase (default: "AIbyML.com")
  5. System validates sender phone + auth code match
  6. Only then executes the original request
- **Timeout:** Configurable (default: 5 minutes)
- **Protection:** Prevents unauthorized data access even if AI is compromised

### 3. **Message Origin Validation**
- **Location:** `whatsapp_service.py:388-392`
- **Description:** Checks `fromMe=False` to prevent self-response loops
- **Protection:** Prevents infinite message loops and resource exhaustion

### 4. **Database Audit Trail**
- **Tables:**
  - `Chat` - Stores contact info, AI status, whitelist status
  - `Message` - Full message history with timestamps
  - `ConversationHistory` - LLM interactions with response times
  - `PendingAuthorization` - Authorization request audit log
- **Protection:** Complete audit trail for compliance and debugging

### 5. **Secure LLM Provider Configuration**
- **Location:** `llm_service.py:80-107`
- **Description:** User-specific LLM configs stored per phone number
- **Fields:** API keys, preferred provider, temperature, max_tokens
- **Protection:** Isolated configurations prevent cross-user data leakage

### 6. **Media File Isolation**
- **Location:** `whatsapp_client.js:134-152`
- **Description:** Media files saved with unique timestamp + sender ID
- **Path:** `MEDIA_PATH/{timestamp}_{sanitized_phone}.{extension}`
- **Protection:** Prevents file overwrite attacks

---

## Key Configuration Points

### 1. **AI Enable/Disable (Per Chat)**
- **Database:** `Chat.ai_enabled` (Boolean)
- **Default:** `False` (must be manually enabled)
- **UI Control:** ChatWindow.tsx:142-159 (AI On/Off button)
- **API:** `POST /api/whatsapp/chats/{chat_id}/toggle-ai`
- **Code:** `routers/whatsapp.py:168-192`

### 2. **Whitelist Status (Per Chat)**
- **Database:** `Chat.is_whitelisted` (Boolean)
- **Default:** `False` (untrusted by default)
- **UI Control:** ChatWindow.tsx:124-141 (Trusted/Untrusted button)
- **API:** `POST /api/whatsapp/chats/{chat_id}/toggle-whitelist`
- **Code:** `routers/whatsapp.py:194-218`
- **Security Impact:** MUST be `True` for AI processing to work

### 3. **BOSS Phone Number (System Config)**
- **Database:** `SystemConfig.key = "BOSS_PHONE_NUMBER"`
- **Format:** Phone number without @ (e.g., "85260552717")
- **Purpose:** Receives authorization requests
- **Code:** `authorization_service.py:27-36`

### 4. **Authorization Code Phrase**
- **Database:** `SystemConfig.key = "AUTH_CODE_PHRASE"`
- **Default:** `"AIbyML.com"`
- **Purpose:** Secret phrase BOSS must reply with
- **Code:** `authorization_service.py:38-47`

### 5. **Authorization Timeout**
- **Database:** `SystemConfig.key = "AUTH_TIMEOUT_MINUTES"`
- **Default:** `5` minutes
- **Purpose:** Expiration time for auth requests
- **Code:** `authorization_service.py:49-61`

### 6. **LLM Provider Selection**
- **Auto-Select Logic:** `llm_service.py:416-439`
  - **Gemini:** Complex queries, appointments, analysis (>10 words)
  - **Ollama:** Simple queries, greetings, quick responses (<10 words)
- **Manual Override:** Set `provider` parameter in API call
- **User Config:** Per-user preferred provider in database

### 7. **Business Hours & Services**
- **Location:** `llm_service.py:441-475` (system prompt)
- **Default Business Hours:** 9:00 AM - 5:00 PM
- **Default Services:** Consultation, Meeting, Service Call, Checkup
- **Customization:** Pass context dict to `generate_response()`

### 8. **Conversation Context Settings**
- **Max Context Length:** 20 messages (`llm_service.py:28`)
- **Context Timeout:** 30 minutes (`llm_service.py:29`)
- **Storage:** In-memory cache with database backup
- **Purpose:** Maintains conversation continuity

### 9. **WebSocket Configuration**
- **Backend Endpoint:** `ws://localhost:8001/ws` (app.py:120)
- **Frontend Auto-Detection:**
  - NGROK: Uses wss:// for HTTPS, ws:// for HTTP
  - Local: ws://localhost:3004/ws
- **Code:** `websocket.ts:10-27`

### 10. **Node.js ↔ Python Communication**
- **Method:** HTTP callbacks + file-based status
- **Callback URL:** `http://localhost:8001/api/whatsapp/callback`
- **Status File:** `whatsapp_client/status.json`
- **QR File:** `whatsapp_client/qr_code.txt`
- **Code:** `whatsapp_client.js:9-10`, `whatsapp_service.py:42-45`

---

## Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=sqlite:///./data/whatsapp_secretary.db

# WhatsApp
WHATSAPP_SESSION_PATH=./backend/whatsapp_client/whatsapp-session
MEDIA_DOWNLOAD_PATH=./backend/whatsapp_client/downloads

# LLM Providers
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash

# Node.js Bridge
PYTHON_CALLBACK_URL=http://localhost:8001/api/whatsapp/callback
```

### Frontend (.env.local)
```bash
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama (optional, for local LLM)
- Google Gemini API key (or other LLM provider)

### Installation

1. **Clone repository**
```bash
git clone <repository-url>
cd WhatsAppSecretary_v0
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure your settings
```

3. **Frontend Setup**
```bash
cd frontend
npm install
cp .env.example .env.local  # Configure your settings
```

4. **WhatsApp Client Setup**
```bash
cd backend/whatsapp_client
npm install
```

5. **Start Services**

**Option A: Development Mode (Separate Terminals)**
```bash
# Terminal 1 - Backend
cd backend
uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Terminal 3 - WhatsApp Client (auto-started by backend)
```

**Option B: Development Script**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

6. **Access Application**
- Frontend: http://localhost:3004
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

---

## Usage Guide

### 1. Initial WhatsApp Connection

1. Click "Connect WhatsApp" in the UI
2. Scan QR code with WhatsApp mobile app
3. Wait for "Connected" status (green indicator)

### 2. Configure a Chat for AI

1. Select a chat from the chat list
2. Click "Trusted" button (shield icon) to whitelist
3. Click "AI On" button (bot icon) to enable AI responses
4. Both must be enabled for AI to respond

### 3. Configure BOSS Authorization

1. Set BOSS phone number in database:
```sql
INSERT INTO system_config (key, value)
VALUES ('BOSS_PHONE_NUMBER', '85260552717');
```

2. Set authorization code (optional, default is "AIbyML.com"):
```sql
INSERT INTO system_config (key, value)
VALUES ('AUTH_CODE_PHRASE', 'YourSecretPhrase');
```

3. When sensitive request detected:
   - BOSS receives WhatsApp with authorization request
   - BOSS replies with exact auth code
   - System executes request and sends confirmation

### 4. Message Flow Example

**Scenario:** User 85260552717 sends "Hello, I need an appointment tomorrow at 3pm"

1. ✅ Message received via WhatsApp Web
2. ✅ Saved to database with Chat and Message records
3. ✅ Check: Is chat whitelisted? (Yes)
4. ✅ Check: Is AI enabled? (Yes)
5. ✅ Detect appointment keywords → appointment flow
6. ✅ LLM extracts: date=tomorrow, time=15:00
7. ✅ Generate confirmation message
8. ✅ Send response via WhatsApp
9. ✅ Update UI in real-time via WebSocket

**Frontend Updates:**
- ChatList shows new unread badge
- ChatList updates last message: "Hello, I need..."
- ChatWindow appends user message bubble (left, gray)
- ChatWindow appends AI response bubble (right, blue)
- Auto-scroll to bottom

---

## API Endpoints

### WhatsApp Management
- `POST /api/whatsapp/connect` - Initialize WhatsApp connection
- `POST /api/whatsapp/disconnect` - Disconnect WhatsApp
- `GET /api/whatsapp/status` - Get connection status
- `GET /api/whatsapp/qr` - Get QR code for authentication
- `POST /api/whatsapp/callback` - Node.js callback endpoint
- `POST /api/whatsapp/send-message` - Send message

### Chat Management
- `GET /api/whatsapp/chats` - Get all chats
- `GET /api/whatsapp/chats/{chat_id}/messages` - Get messages
- `POST /api/whatsapp/chats/{chat_id}/toggle-ai` - Toggle AI for chat
- `POST /api/whatsapp/chats/{chat_id}/toggle-whitelist` - Toggle whitelist

### LLM & Appointments
- `POST /api/llm/generate` - Generate LLM response
- `GET /api/llm/status` - LLM service status
- `GET /api/appointments` - List appointments
- `POST /api/appointments` - Create appointment

### WebSocket Events
- `whatsapp_status` - Connection status updates
- `qr_code` - QR code for authentication
- `new_message` - New incoming message
- `message_sent` - Outgoing message confirmation
- `pairing_code` - Pairing code (deprecated, QR only)

---

## Database Schema

### Core Tables

**Chat**
- `id` (PK) - WhatsApp chat ID (e.g., "85260552717@c.us")
- `phone_number` - Contact phone number
- `name` - Contact display name
- `is_group` - Group chat flag
- `ai_enabled` - AI response toggle
- `is_whitelisted` - Whitelist security flag
- `is_active` - Active status

**Message**
- `id` (PK) - WhatsApp message ID
- `chat_id` (FK) - Reference to Chat
- `body` - Message text
- `message_type` - TEXT/IMAGE/VIDEO/AUDIO/DOCUMENT
- `from_me` - Sent by user (True) or received (False)
- `timestamp` - Message datetime
- `has_media` - Media attachment flag
- `media_path` - Local media file path
- `llm_processed` - AI processing flag
- `llm_response` - AI generated response

**ConversationHistory**
- `id` (PK)
- `chat_id` - Reference to Chat
- `user_input` - User message
- `llm_response` - AI response
- `provider` - LLM provider used (OLLAMA/GEMINI/OPENAI/ANTHROPIC)
- `model_name` - Specific model name
- `response_time_ms` - Response latency

**PendingAuthorization**
- `id` (PK)
- `request_id` - Unique UUID
- `chat_id` - Requester chat ID
- `requester_phone` - Phone number of requester
- `action_type` - Type of sensitive action
- `action_description` - Human-readable description
- `requested_data` - JSON data payload
- `auth_code` - Expected authorization code
- `status` - pending/approved/rejected/expired
- `approved_by` - BOSS phone number
- `expires_at` - Expiration timestamp

**SystemConfig**
- `id` (PK)
- `key` - Config key (BOSS_PHONE_NUMBER, AUTH_CODE_PHRASE, etc.)
- `value` - Config value
- `description` - Human-readable description

---

## Troubleshooting

### WhatsApp Won't Connect
1. Check Node.js process is running: `ps aux | grep node`
2. Check backend logs for errors
3. Delete session folder: `rm -rf backend/whatsapp_client/whatsapp-session`
4. Restart backend and scan QR again

### AI Not Responding
1. Verify chat is **whitelisted** (shield icon shows "Trusted")
2. Verify AI is **enabled** (bot icon shows "AI On")
3. Check LLM service status: `GET /api/llm/status`
4. Check backend logs for LLM errors

### Messages Not Appearing in UI
1. Check WebSocket connection in browser DevTools (Network tab)
2. Verify WebSocket URL matches backend (ws://localhost:8001/ws)
3. Check frontend console for WebSocket errors
4. Refresh chat list manually

### Authorization Not Working
1. Verify BOSS phone number in database: `SELECT * FROM system_config WHERE key='BOSS_PHONE_NUMBER'`
2. Check exact auth code phrase matches
3. Verify authorization hasn't expired (default 5 minutes)
4. Check backend logs for authorization validation

---

## Development

### Project Structure
```
WhatsAppSecretary_v0/
├── backend/
│   ├── app.py                    # FastAPI application entry
│   ├── core/
│   │   └── config.py             # Configuration settings
│   ├── database/
│   │   ├── database.py           # Database setup
│   │   └── models.py             # SQLAlchemy models
│   ├── routers/
│   │   ├── whatsapp.py           # WhatsApp endpoints
│   │   ├── appointments.py       # Appointment endpoints
│   │   └── llm.py                # LLM endpoints
│   ├── services/
│   │   ├── whatsapp_service.py   # WhatsApp business logic
│   │   ├── llm_service.py        # LLM integration
│   │   ├── authorization_service.py  # 2FA authorization
│   │   └── user_service.py       # User management
│   ├── whatsapp_client/
│   │   ├── whatsapp_client.js    # Node.js WhatsApp client
│   │   ├── simple_bridge.js      # File-based IPC bridge
│   │   └── package.json          # Node.js dependencies
│   └── websocket/
│       └── manager.py            # WebSocket connection manager
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── WhatsApp/
│   │   │       ├── ChatList.tsx       # Chat list component
│   │   │       ├── ChatWindow.tsx     # Chat window component
│   │   │       └── ConnectionStatus.tsx  # Status indicator
│   │   ├── services/
│   │   │   ├── api.ts            # HTTP API client
│   │   │   └── websocket.ts      # WebSocket client
│   │   ├── store/
│   │   │   └── whatsapp.ts       # Zustand state management
│   │   └── types/
│   │       └── index.ts          # TypeScript types
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

### Adding New Features

**1. New LLM Provider**
- Add provider enum to `database/models.py:LLMProvider`
- Implement `generate_<provider>_response()` in `llm_service.py`
- Add provider selection logic in `select_best_provider()`
- Update UI to show provider status

**2. New Message Type**
- Add type to `database/models.py:MessageType`
- Update Node.js handler in `whatsapp_client.js:handleMessage()`
- Add media processing logic
- Update UI to render new type

**3. New Authorization Type**
- Add action type to database schema
- Implement detection logic in LLM service
- Create authorization request in `authorization_service.py`
- Handle execution in `execute_authorized_action()`

---

## Production Deployment

### Security Checklist
- [ ] Change default AUTH_CODE_PHRASE
- [ ] Configure BOSS phone number
- [ ] Enable HTTPS/WSS for all connections
- [ ] Set secure environment variables
- [ ] Enable database encryption
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerts
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Review and minimize API key permissions

### Docker Deployment
```bash
docker-compose up -d
```

### Environment Configuration
- Use `.env.production` for production settings
- Store secrets in secure vault (AWS Secrets Manager, etc.)
- Configure auto-scaling for backend
- Set up CDN for frontend assets
- Enable database backups

---

## License

[Specify your license here]

---

## Support

For issues and questions:
- GitHub Issues: [Repository Issues URL]
- Email: [Support Email]
- Documentation: [Docs URL]

---

*Last Updated: 2025-10-04*
*Version: 2.0.0*
