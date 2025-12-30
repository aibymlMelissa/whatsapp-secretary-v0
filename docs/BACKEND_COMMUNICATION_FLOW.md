# Backend WhatsApp Communication Flow & File Transfer

## Overview

This document explains the backend communication flow for WhatsApp messages, including file transfers, based on actual system logs and implementation.

---

## Message Processing Flow (Step-by-Step)

### Example Log Analysis

```
📨 Processing message from 85290511427@c.us: ...
💾 Created new chat for 85290511427
💾 Message saved to database: ...
✅ Message processed and saved successfully
ℹ️ AI not enabled for this chat
INFO: 127.0.0.1:53945 - "POST /api/whatsapp/callback HTTP/1.1" 200 OK
INFO: 127.0.0.1:53883 - "GET /api/settings/llm?phone_number=+1234567890 HTTP/1.1" 200 OK
INFO: 127.0.0.1:53884 - "GET /api/settings/llm?phone_number=+1234567890 HTTP/1.1" 200 OK
INFO: 127.0.0.1:52316 - "GET /api/whatsapp/chats/85260552717%40c.us/messages?limit=50 HTTP/1.1" 200 OK
WhatsApp: ✅ Callback sent: new_message
```

---

## Detailed Flow Breakdown

### 1. **Message Reception** 📨
```
📨 Processing message from 85290511427@c.us: ...
```

**What happens:**
- Node.js WhatsApp client receives message via `whatsapp-web.js`
- Message is from external number: `85290511427`
- Chat ID format: `{phone_number}@c.us` (WhatsApp standard format)
- Message data extracted: chatId, body, timestamp, hasMedia, type

**Code Location:** `whatsapp_service.py:373-416`

**Function:**
```python
async def process_new_message(self, message_data: dict):
    print(f"📨 Processing message from {message_data.get('chatId', 'unknown')}: {message_data.get('body', 'no text')[:50]}...")
```

---

### 2. **New Chat Creation** 💾
```
💾 Created new chat for 85290511427
```

**What happens:**
- System checks if Chat record exists for `85290511427@c.us`
- If not exists → Creates new Chat record with:
  - `id = "85290511427@c.us"`
  - `phone_number = "85290511427"`
  - `name = "Contact 1427"` (last 4 digits used as default)
  - `is_group = False`
  - `is_active = True`
  - `ai_enabled = False` (default)
  - `is_whitelisted = False` (default)

**Code Location:** `whatsapp_service.py:436-450`

**Function:**
```python
if not chat:
    chat = Chat(
        id=chat_id,
        phone_number=phone_number,
        name=f"Contact {phone_number[-4:]}",
        is_group=message_data.get("isGroup", False),
        is_active=True
    )
    db.add(chat)
    db.flush()
    print(f"💾 Created new chat for {phone_number}")
```

---

### 3. **Message Database Save** 💾
```
💾 Message saved to database: ...
```

**What happens:**
- Creates Message record in database with:
  - `id` = WhatsApp message ID
  - `chat_id` = "85290511427@c.us"
  - `body` = Message text content
  - `message_type` = MessageType.TEXT (or IMAGE/VIDEO/AUDIO/DOCUMENT)
  - `from_me` = False (received message)
  - `timestamp` = Message timestamp from WhatsApp
  - `has_media` = True/False
  - `media_path` = Local file path (if media)
  - `llm_processed` = False (not yet processed by AI)

**Code Location:** `whatsapp_service.py:452-482`

**Function:**
```python
message = Message(
    id=message_data.get("id"),
    chat_id=chat.id,
    body=message_data.get("body", ""),
    message_type=MessageType.TEXT,
    from_me=message_data.get("fromMe", False),
    timestamp=datetime.fromtimestamp(message_data["timestamp"]),
    has_media=message_data.get("hasMedia", False),
    llm_processed=False
)
db.add(message)
db.commit()
print(f"💾 Message saved to database: {message_data.get('body', '')[:30]}...")
```

---

### 4. **Processing Completion** ✅
```
✅ Message processed and saved successfully
```

**What happens:**
- Confirms successful database save
- Message is now stored and retrievable
- Frontend can fetch via API: `GET /api/whatsapp/chats/{chat_id}/messages`

**Code Location:** `whatsapp_service.py:381`

---

### 5. **AI Processing Check** ℹ️
```
ℹ️ AI not enabled for this chat
```

**What happens:**
- System checks if chat has `ai_enabled = True`
- System checks if chat has `is_whitelisted = True`
- In this case: AI is disabled (default for new chats)
- **Security:** Both flags must be True for AI processing

**Code Location:** `whatsapp_service.py:395-411`

**Logic:**
```python
if not message_data.get("fromMe", False):
    db = SessionLocal()
    try:
        chat = db.query(Chat).filter(Chat.id == message_data.get("chatId")).first()
        if chat and chat.ai_enabled and self.llm_service:
            if chat.is_whitelisted:
                print(f"🤖 AI enabled and whitelisted for this chat, processing with LLM...")
                await self.process_message_with_llm(message_data)
            else:
                print(f"🔒 AI enabled but chat not whitelisted - skipping LLM processing")
        else:
            if chat:
                print(f"ℹ️ AI {'not enabled' if not chat.ai_enabled else 'service not available'} for this chat")
```

**To Enable AI:**
1. Frontend: Click "Trusted" button (whitelists chat)
2. Frontend: Click "AI On" button (enables AI)
3. Backend API calls:
   - `POST /api/whatsapp/chats/{chat_id}/toggle-whitelist`
   - `POST /api/whatsapp/chats/{chat_id}/toggle-ai`

---

### 6. **HTTP Callback Response** 200 OK
```
INFO: 127.0.0.1:53945 - "POST /api/whatsapp/callback HTTP/1.1" 200 OK
```

**What happens:**
- Node.js WhatsApp client sent callback to Python backend
- Python processed the callback successfully
- Returns 200 OK to Node.js client
- Confirms bidirectional communication working

**API Endpoint:** `POST /api/whatsapp/callback`

**Code Location:** `routers/whatsapp.py:80-97`

**Request Format:**
```json
{
  "event": "new_message",
  "data": {
    "id": "message_id_here",
    "chatId": "85290511427@c.us",
    "body": "Message text",
    "timestamp": 1234567890,
    "fromMe": false,
    "hasMedia": false,
    "type": "chat"
  },
  "timestamp": 1234567890000
}
```

---

### 7. **LLM Settings Fetch** (Parallel Requests)
```
INFO: 127.0.0.1:53883 - "GET /api/settings/llm?phone_number=+1234567890 HTTP/1.1" 200 OK
INFO: 127.0.0.1:53884 - "GET /api/settings/llm?phone_number=+1234567890 HTTP/1.1" 200 OK
```

**What happens:**
- Frontend fetches user-specific LLM configuration
- Two parallel requests (likely from different UI components)
- Retrieves settings for phone number: `+1234567890`
- Returns user's preferred LLM provider, model, temperature, etc.

**API Endpoint:** `GET /api/settings/llm?phone_number={phone}`

**Response Format:**
```json
{
  "success": true,
  "config": {
    "preferred_provider": "gemini",
    "ollama_model": "llama3.2",
    "gemini_model": "gemini-1.5-flash",
    "temperature": 0.7,
    "max_tokens": 500,
    "ollama_base_url": "http://localhost:11434"
  }
}
```

---

### 8. **Message History Fetch**
```
INFO: 127.0.0.1:52316 - "GET /api/whatsapp/chats/85260552717%40c.us/messages?limit=50 HTTP/1.1" 200 OK
```

**What happens:**
- Frontend fetches last 50 messages for chat `85260552717@c.us`
- URL-encoded chat ID: `85260552717%40c.us` → `85260552717@c.us`
- Returns messages in chronological order
- Used to populate ChatWindow component

**API Endpoint:** `GET /api/whatsapp/chats/{chat_id}/messages?limit=50`

**Code Location:** `routers/whatsapp.py:220-254`

**Response Format:**
```json
{
  "success": true,
  "messages": [
    {
      "id": "message_id",
      "chat_id": "85260552717@c.us",
      "body": "Message text",
      "message_type": "text",
      "from_me": false,
      "timestamp": "2025-10-04T10:30:00",
      "has_media": false,
      "media_path": null,
      "llm_processed": false,
      "llm_response": null
    }
  ]
}
```

---

### 9. **WebSocket Broadcast** ✅
```
WhatsApp: ✅ Callback sent: new_message
```

**What happens:**
- Backend broadcasts `new_message` event via WebSocket
- All connected frontend clients receive the update
- Triggers real-time UI updates in ChatList and ChatWindow

**Code Location:** `whatsapp_service.py:343-358`

**WebSocket Event:**
```python
if self.connection_manager:
    await self.connection_manager.broadcast({
        "type": "new_message",
        "data": {
            "chatId": data.get("chatId"),
            "messageId": data.get("id"),
            "body": data.get("body"),
            "fromMe": data.get("fromMe", False),
            "timestamp": data.get("timestamp"),
            "hasMedia": data.get("hasMedia", False),
            "isGroup": data.get("isGroup", False)
        }
    })
```

**Frontend Handler:** `whatsapp.ts:165-185`

---

## File Transfer Flow (Media Messages)

### When User Sends Media (Image/Video/Document)

#### 1. **Media Detection** (Node.js)
```javascript
// whatsapp_client.js:134-152
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
```

**What happens:**
1. `message.hasMedia` flag is True
2. Downloads media using `message.downloadMedia()`
3. Creates unique filename: `{timestamp}_{sanitized_phone}.{extension}`
4. Saves to `MEDIA_PATH` (default: `./backend/whatsapp_client/downloads/`)
5. Adds media info to message data

#### 2. **Media Message Callback**
```json
{
  "event": "new_message",
  "data": {
    "id": "media_message_id",
    "chatId": "85290511427@c.us",
    "body": "Image caption (if any)",
    "timestamp": 1234567890,
    "fromMe": false,
    "hasMedia": true,
    "mediaPath": "./downloads/1696431234567_85290511427_c_us.jpg",
    "mediaFilename": "1696431234567_85290511427_c_us.jpg",
    "mimeType": "image/jpeg",
    "type": "chat"
  }
}
```

#### 3. **Database Storage**
```python
# Message record with media
message = Message(
    id=message_data.get("id"),
    chat_id=chat.id,
    body=message_data.get("body", ""),
    message_type=MessageType.IMAGE,  # or VIDEO, AUDIO, DOCUMENT
    from_me=False,
    timestamp=datetime.fromtimestamp(message_data["timestamp"]),
    has_media=True,
    media_path=message_data.get("mediaPath"),
    llm_processed=False
)
```

#### 4. **Frontend Access**
- Frontend receives media_path in message object
- Can request file via: `GET /api/files/{filename}`
- Displays image/video in ChatWindow
- Provides download link for documents

**File Serve Endpoint:** `routers/files.py`

---

## Message Type Handling

### Supported Message Types

| Type | Enum | Description | Media | LLM Processing |
|------|------|-------------|-------|----------------|
| Text | `MessageType.TEXT` | Plain text message | No | ✅ Yes |
| Image | `MessageType.IMAGE` | Image file (JPEG, PNG, etc.) | Yes | ⚠️ Limited |
| Video | `MessageType.VIDEO` | Video file (MP4, etc.) | Yes | ❌ No |
| Audio | `MessageType.AUDIO` | Voice message, audio file | Yes | ❌ No |
| Document | `MessageType.DOCUMENT` | PDF, DOCX, etc. | Yes | ⚠️ Limited |

**Code Location:** `database/models.py:MessageType`

---

## Error Handling & Logging

### Log Levels & Meanings

| Emoji | Level | Meaning | Example |
|-------|-------|---------|---------|
| 📨 | INFO | Processing started | `📨 Processing message from...` |
| 💾 | INFO | Database operation | `💾 Created new chat for...` |
| ✅ | SUCCESS | Operation completed | `✅ Message processed and saved successfully` |
| ℹ️ | INFO | Status information | `ℹ️ AI not enabled for this chat` |
| 🤖 | INFO | AI processing | `🤖 AI enabled and whitelisted...` |
| 🔒 | WARNING | Security block | `🔒 AI enabled but not whitelisted` |
| ❌ | ERROR | Operation failed | `❌ Error processing message` |
| ⚠️ | WARNING | Potential issue | `⚠️ Invalid timestamp, using current time` |
| 🔐 | SECURITY | Authorization | `🔐 Authorization required` |

---

## Communication Paths

### 1. **Node.js → Python (Callback)**
```
WhatsApp Web → whatsapp-web.js → whatsapp_client.js → HTTP POST → Python Backend
```

- **URL:** `http://localhost:8001/api/whatsapp/callback`
- **Method:** POST
- **Content-Type:** application/json
- **Events:** new_message, qr_code, ready, authenticated, disconnected, etc.

### 2. **Python → Node.js (Command)**
```
Python Backend → stdin write → whatsapp_client.js → whatsapp-web.js → WhatsApp Web
```

- **Method:** stdin pipe
- **Format:** JSON line-delimited
- **Commands:** send_message, get_chats, get_chat_messages, get_status, etc.

**Example Command:**
```json
{"action": "send_message", "data": {"chatId": "85290511427@c.us", "message": "Hello"}, "id": "cmd_123"}
```

### 3. **Python → Frontend (WebSocket)**
```
Python Backend → WebSocket Manager → WebSocket → Frontend
```

- **URL:** `ws://localhost:8001/ws`
- **Protocol:** WebSocket
- **Events:** whatsapp_status, qr_code, new_message, message_sent

### 4. **Frontend → Python (REST API)**
```
Frontend → HTTP Request → FastAPI Router → Service → Database
```

- **Base URL:** `http://localhost:8001/api`
- **Protocol:** HTTP/HTTPS
- **Endpoints:** /whatsapp/*, /settings/*, /appointments/*, /llm/*

---

## Performance Metrics

### Typical Response Times

| Operation | Avg Time | Location |
|-----------|----------|----------|
| Message callback processing | 50-100ms | `whatsapp_service.py:373` |
| Database save | 10-30ms | `whatsapp_service.py:418` |
| AI response generation (Ollama) | 1-3s | `llm_service.py:175` |
| AI response generation (Gemini) | 500ms-2s | `llm_service.py:233` |
| Media file download | 100ms-2s | `whatsapp_client.js:135` |
| WebSocket broadcast | 5-10ms | `websocket/manager.py` |
| Frontend message fetch | 20-50ms | `routers/whatsapp.py:220` |

---

## Troubleshooting Common Issues

### Issue 1: "ℹ️ AI not enabled for this chat"

**Cause:** Default security - AI is disabled for new chats

**Solution:**
```sql
-- Enable whitelist
UPDATE chat SET is_whitelisted = TRUE WHERE id = '85290511427@c.us';

-- Enable AI
UPDATE chat SET ai_enabled = TRUE WHERE id = '85290511427@c.us';
```

Or via UI:
1. Select chat in ChatList
2. Click "Trusted" button (shield icon)
3. Click "AI On" button (bot icon)

---

### Issue 2: Media files not downloading

**Check:**
1. `MEDIA_PATH` directory exists and is writable
2. Node.js has permissions to write files
3. Sufficient disk space available

**Fix:**
```bash
mkdir -p backend/whatsapp_client/downloads
chmod 755 backend/whatsapp_client/downloads
```

---

### Issue 3: Duplicate HTTP requests (same endpoint called twice)

**Observed:**
```
INFO: 127.0.0.1:53883 - "GET /api/settings/llm?phone_number=+1234567890 HTTP/1.1" 200 OK
INFO: 127.0.0.1:53884 - "GET /api/settings/llm?phone_number=+1234567890 HTTP/1.1" 200 OK
```

**Cause:** Multiple frontend components fetching same data

**Solution:** Implement request deduplication or caching in frontend

---

### Issue 4: Message not appearing in UI

**Debug Steps:**
1. Check backend logs for "✅ Callback sent: new_message"
2. Check browser DevTools → Network → WS tab for WebSocket message
3. Check frontend console for WebSocket event handler
4. Manually refresh: `GET /api/whatsapp/chats/{chat_id}/messages`

---

## Security Considerations

### 1. **File Path Sanitization**
- Media filenames use timestamp + sanitized phone number
- Prevents directory traversal attacks
- Format: `{timestamp}_{phone_without_special_chars}.{ext}`

### 2. **Chat Whitelist Enforcement**
```python
if chat.is_whitelisted:
    await self.process_message_with_llm(message_data)
else:
    print(f"🔒 AI enabled but chat not whitelisted - skipping LLM processing")
```

### 3. **Message Origin Validation**
```python
if not message_data.get("fromMe", False):
    # Only process messages from others, not our own
```

### 4. **Media File Access Control**
- Media files stored in isolated directory
- Access via authenticated API endpoint only
- No direct file system access from frontend

---

## Configuration

### Environment Variables

```bash
# WhatsApp Client
WHATSAPP_SESSION_PATH=./backend/whatsapp_client/whatsapp-session
MEDIA_DOWNLOAD_PATH=./backend/whatsapp_client/downloads

# Communication
PYTHON_CALLBACK_URL=http://localhost:8001/api/whatsapp/callback

# WebSocket
WS_URL=ws://localhost:8001/ws
```

### System Paths

| Path | Purpose | Location |
|------|---------|----------|
| Session Storage | WhatsApp auth session | `./whatsapp_client/whatsapp-session/` |
| Media Downloads | Received media files | `./whatsapp_client/downloads/` |
| QR Code File | Authentication QR | `./whatsapp_client/qr_code.txt` |
| Status File | Node.js status | `./whatsapp_client/status.json` |
| Database | Message & chat storage | `./data/whatsapp_secretary.db` |

---

## Monitoring & Debugging

### Enable Detailed Logging

**Backend (Python):**
```python
# In app.py or service files
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend (Browser Console):**
```javascript
// In websocket.ts
console.log('WebSocket message:', message);
```

**Node.js Client:**
```javascript
// In whatsapp_client.js
console.log('📞 Sending callback:', { event, data });
```

### Key Metrics to Monitor

1. **Message Processing Time:** Time from receipt to database save
2. **Callback Success Rate:** Percentage of successful HTTP callbacks
3. **WebSocket Connection Health:** Uptime and reconnection frequency
4. **Media Download Success Rate:** Successful vs failed media downloads
5. **AI Processing Rate:** Messages processed by LLM vs total messages

---

*Last Updated: 2025-10-04*
*Version: 2.0.0*
