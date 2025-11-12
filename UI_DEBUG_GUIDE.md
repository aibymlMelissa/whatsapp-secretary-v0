# UI Not Updating - Debug Guide

## Problem: "Nothing happened in UI"

Based on your backend logs showing successful message processing, but no UI updates, here's the systematic debug guide.

---

## Current Situation

### ✅ Working (Backend)
```
📨 Processing message from 85290511427@c.us: ...
💾 Created new chat for 85290511427
💾 Message saved to database: ...
✅ Message processed and saved successfully
```

### ❌ Not Working (Frontend)
- Chat not appearing in ChatList
- Messages not showing in ChatWindow
- No real-time updates via WebSocket

---

## Debug Steps

### Step 1: Check Browser Console

Open browser DevTools (F12) and check for errors:

```javascript
// Expected WebSocket messages:
{
  "type": "new_message",
  "data": {
    "chatId": "85290511427@c.us",
    "messageId": "...",
    "body": "...",
    "fromMe": false,
    "timestamp": 1234567890
  }
}
```

**Look for:**
- ❌ WebSocket connection errors
- ❌ CORS errors
- ❌ API request failures
- ❌ JavaScript errors in console

### Step 2: Verify WebSocket Connection

**In Browser Console, run:**
```javascript
// Check WebSocket status
console.log('WebSocket:', window.ws?.readyState);
// 0 = CONNECTING, 1 = OPEN, 2 = CLOSING, 3 = CLOSED
```

**Expected:** `1` (OPEN)

**If not connected, check Network tab:**
- Filter by "WS" (WebSocket)
- Look for `ws://localhost:8001/ws` or `ws://localhost:3004/ws`
- Check connection status and errors

### Step 3: Manual API Test

**In Browser Console or Terminal:**

```bash
# 1. Check backend health
curl http://localhost:8001/health

# 2. Get chats (should show 85290511427)
curl http://localhost:8001/api/whatsapp/chats

# 3. Get messages for the chat
curl http://localhost:8001/api/whatsapp/chats/85290511427%40c.us/messages
```

**Expected Response:**
```json
{
  "success": true,
  "chats": [
    {
      "id": "85290511427@c.us",
      "phone_number": "85290511427",
      "name": "Contact 1427",
      "ai_enabled": false,
      "is_whitelisted": false,
      "unread_count": 1,
      "last_message": { ... }
    }
  ]
}
```

### Step 4: Check WebSocket Broadcast

**In Backend Logs, look for:**
```
WhatsApp: ✅ Callback sent: new_message
```

**This means:**
- ✅ Node.js sent callback to Python
- ❓ Python should broadcast via WebSocket

**Check if broadcast is happening:**

In `backend/whatsapp_service.py:343-358`, add debug log:
```python
if self.connection_manager:
    print(f"🔊 Broadcasting new_message to {len(self.connection_manager.active_connections)} clients")
    await self.connection_manager.broadcast({
        "type": "new_message",
        "data": { ... }
    })
```

### Step 5: Check Frontend State

**In Browser Console:**
```javascript
// Check Zustand store state
const store = useWhatsAppStore.getState();
console.log('Chats:', store.chats);
console.log('Messages:', store.messages);
console.log('Current Chat:', store.currentChat);
```

**Expected:**
- `chats` array should contain chat with ID `85290511427@c.us`
- `messages` should have entries for that chat

---

## Common Issues & Fixes

### Issue 1: WebSocket Not Connecting

**Symptoms:**
- No WebSocket connection in Network tab
- Console error: "WebSocket connection failed"

**Cause:** WebSocket URL mismatch

**Fix:**
Check `frontend/src/services/websocket.ts:10-27`

```typescript
// Current logic:
if (import.meta.env.VITE_WS_URL) {
  url = `${import.meta.env.VITE_WS_URL}/ws`;
} else if (window.location.hostname.includes('ngrok-free.app')) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  url = `${protocol}//${window.location.host}/ws`;
} else {
  url = `ws://${window.location.host}/ws`;  // ← This might be wrong!
}
```

**Problem:** `window.location.host` = `localhost:3004` (frontend port)
**Should be:** `localhost:8001` (backend port)

**Quick Fix:**
```bash
# In frontend/.env.local
echo "VITE_WS_URL=ws://localhost:8001" >> frontend/.env.local
```

**Restart frontend after adding env variable.**

---

### Issue 2: Backend Hanging on /api/whatsapp/chats

**Symptoms:**
- API requests timeout
- Backend logs show no response

**Possible Causes:**
1. **Database lock** - SQLite locked by another process
2. **Infinite loop** - Query stuck
3. **Missing await** - Async function not awaited

**Debug:**
```bash
# Check if database is locked
lsof | grep whatsapp_secretary.db

# Check backend process CPU
ps aux | grep python | grep app.py
```

**Fix if Database Locked:**
```bash
# Stop all Python processes
pkill -f "python.*app.py"

# Remove lock files
rm -f backend/data/whatsapp_secretary.db-shm
rm -f backend/data/whatsapp_secretary.db-wal

# Restart backend
cd backend
python app.py
```

---

### Issue 3: CORS Error

**Symptoms:**
- Console error: "CORS policy blocked"
- API requests fail with CORS error

**Check:**
`backend/app.py:66-81` - CORS configuration

**Current:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3004",
        "http://127.0.0.1:3004",
        # ...
    ],
)
```

**Fix if needed:**
```python
# Temporarily allow all (for debugging only!)
allow_origins=["*"],
```

---

### Issue 4: Frontend Not Fetching Chats

**Symptoms:**
- ChatList shows "No chats available"
- API works via curl but not in browser

**Check:**
1. **API Base URL** - `frontend/src/services/api.ts:24`
2. **Fetch on mount** - `frontend/src/components/WhatsApp/ChatList.tsx:13-15`

**Debug in Browser Console:**
```javascript
// Test API directly
fetch('http://localhost:8001/api/whatsapp/chats')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

**Fix if API base URL wrong:**

In `frontend/.env.local`:
```bash
VITE_API_URL=http://localhost:8001
VITE_BACKEND_URL=http://localhost:8001
```

Restart frontend.

---

### Issue 5: Chat Created But Not Visible

**Symptoms:**
- Backend shows "💾 Created new chat"
- Database has the chat
- UI still shows "No chats available"

**Cause:** Frontend not refreshing after WebSocket event

**Check:**
`frontend/src/store/whatsapp.ts:165-185` - WebSocket listener

```typescript
websocketService.on('new_message', (message: any) => {
  console.log('New message received:', message);  // ← Add this debug

  // ... existing code ...

  // This should refresh chat list:
  useWhatsAppStore.getState().fetchChats();  // ← Check if called
});
```

**Quick Fix:**

Manually refresh chat list in UI:
1. Click on another tab
2. Click back to "Conversations" tab
3. Or add a "Refresh" button

---

## Immediate Fix Steps

### Step 1: Add Debug Logs

**Backend - `whatsapp_service.py:346`:**
```python
if self.connection_manager:
    active_count = len(self.connection_manager.active_connections)
    print(f"🔊 Broadcasting to {active_count} WebSocket clients")

    await self.connection_manager.broadcast({
        "type": "new_message",
        "data": {
            "chatId": data.get("chatId"),
            "messageId": data.get("id"),
            "body": data.get("body"),
            "fromMe": data.get("fromMe", False),
            "timestamp": data.get("timestamp"),
        }
    })

    print(f"✅ Broadcast complete")
else:
    print(f"❌ No WebSocket connection manager!")
```

**Frontend - `whatsapp.ts:165`:**
```typescript
websocketService.on('new_message', (message: any) => {
  console.log('🔔 WebSocket: new_message event received:', message);

  const messageData = message.data || message;
  console.log('📥 Message data:', messageData);

  if (messageData.chatId) {
    useWhatsAppStore.getState().addMessage({
      id: messageData.messageId || messageData.id,
      chat_id: messageData.chatId,
      body: messageData.body,
      message_type: 'text',
      from_me: messageData.fromMe || false,
      timestamp: messageData.timestamp,
      has_media: messageData.hasMedia || false,
      llm_processed: false,
    });

    console.log('✅ Message added to store');
  }

  useWhatsAppStore.getState().fetchChats();
  console.log('✅ Chat list refresh triggered');
});
```

### Step 2: Fix WebSocket URL

**Create/Update `frontend/.env.local`:**
```bash
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
VITE_BACKEND_URL=http://localhost:8001
```

### Step 3: Restart Everything

```bash
# Terminal 1 - Stop and restart backend
pkill -f "python.*app.py"
cd backend
python app.py

# Terminal 2 - Stop and restart frontend
pkill -f "vite"
cd frontend
npm run dev
```

### Step 4: Test in Browser

1. Open http://localhost:3004
2. Open DevTools Console (F12)
3. Look for debug logs:
   - `🔔 WebSocket: new_message event received:`
   - `✅ Message added to store`
   - `✅ Chat list refresh triggered`

4. Send a WhatsApp message to trigger flow
5. Watch console for updates

---

## Verification Checklist

After applying fixes, verify:

- [ ] WebSocket connects successfully (check Network tab → WS)
- [ ] Backend shows: `🔊 Broadcasting to 1 WebSocket clients`
- [ ] Frontend console shows: `🔔 WebSocket: new_message event received`
- [ ] Chat appears in ChatList component
- [ ] Messages appear in ChatWindow component
- [ ] Unread badge shows correct count
- [ ] Last message preview updates
- [ ] Timestamp shows correctly

---

## Still Not Working?

### Nuclear Option: Complete Reset

```bash
# 1. Stop all processes
pkill -f "python.*app.py"
pkill -f "node.*whatsapp"
pkill -f "vite"

# 2. Clear all caches and sessions
rm -rf backend/whatsapp_client/whatsapp-session
rm -rf backend/whatsapp_client/.wwebjs_cache
rm -rf backend/data/*.db-shm
rm -rf backend/data/*.db-wal
rm -rf frontend/node_modules/.vite

# 3. Restart backend
cd backend
python app.py

# 4. In new terminal, restart frontend
cd frontend
npm run dev

# 5. Connect WhatsApp
# - Open http://localhost:3004
# - Click "Connect WhatsApp"
# - Scan QR code
# - Wait for "Connected" status

# 6. Send test message from external WhatsApp

# 7. Watch for updates in UI
```

---

## Get More Info

### Backend Logs Location
Check terminal running `python app.py` for:
- `📨 Processing message from...`
- `🔊 Broadcasting to X WebSocket clients`
- `✅ Callback sent: new_message`

### Frontend Logs Location
Check browser DevTools Console for:
- WebSocket connection status
- `new_message` events
- State updates
- API errors

### Database Direct Check
```bash
cd backend
sqlite3 data/whatsapp_secretary.db

-- Check chats
SELECT id, phone_number, name, ai_enabled, is_whitelisted FROM chat;

-- Check messages
SELECT id, chat_id, body, from_me, timestamp FROM message ORDER BY timestamp DESC LIMIT 10;

-- Exit
.quit
```

---

## Contact for Support

If issue persists after all fixes:

1. **Collect Debug Info:**
   - Browser console logs (all errors)
   - Backend terminal output (last 50 lines)
   - Network tab screenshot (WS connection status)
   - API test results (curl commands)

2. **Check GitHub Issues:**
   - Similar issues reported?
   - Known bugs with fixes?

3. **Create Debug Report:**
   - Include all logs
   - Steps to reproduce
   - Environment details (OS, browser, versions)

---

*Last Updated: 2025-10-04*
*Version: 2.0.0*
