# Backend-Frontend Connection Health Guide

## 🔍 Ensuring Seamless Connection

This guide explains how the WhatsApp Secretary ensures continuous, reliable connection between backend and frontend.

---

## 🏗️ Architecture Overview

```
┌─────────────────┐      WebSocket      ┌──────────────────┐
│                 │◄───────────────────►│                  │
│  Frontend       │      (Real-time)    │   Backend API    │
│  (Port 3004)    │                     │   (Port 8001)    │
│                 │◄───────────────────►│                  │
└─────────────────┘    REST API         └──────────────────┘
                       (HTTP)
```

### Connection Types

1. **REST API** (HTTP)
   - Used for: Data fetching, mutations, file uploads
   - Endpoints: `/api/whatsapp/*`, `/api/appointments/*`, `/api/files/*`
   - Protocol: HTTP/HTTPS

2. **WebSocket** (WS/WSS)
   - Used for: Real-time updates, QR code, message notifications
   - Endpoint: `/ws`
   - Protocol: WebSocket (WS/WSS)

---

## ✅ Connection Health Features

### 1. **Automatic Reconnection**

The frontend WebSocket has built-in reconnection logic:

```typescript
// frontend/src/services/websocket.ts
- Max reconnection attempts: 10
- Reconnection delay: Exponential backoff (1s → 10s max)
- Auto-reconnect on connection drop
```

**How it works:**
- Connection lost? → Automatically retry
- Backend restart? → Frontend reconnects automatically
- Network issue? → Keeps trying with exponential backoff

### 2. **Heartbeat Mechanism**

Keeps WebSocket connection alive:

```typescript
// Sends ping every 30 seconds
this.heartbeatInterval = setInterval(() => {
  if (this.ws && this.ws.readyState === WebSocket.OPEN) {
    this.send('ping');
  }
}, 30000);
```

**Benefits:**
- Prevents idle connection timeout
- Early detection of connection issues
- Network infrastructure compatibility

### 3. **Health Monitoring**

Backend provides health endpoint:

```bash
curl http://localhost:8001/health

# Returns:
{
  "status": "healthy",
  "whatsapp": {
    "connected": true,
    "ready": true
  },
  "services": {
    "whatsapp_service": true,
    "llm_service": true
  }
}
```

---

## 🛠️ Monitoring Tools

### **Quick Check**

```bash
./monitor_connection.sh
```

Output:
```
✓ Backend: Running
✓ Frontend: Running
✓ API: Connected
⚠ WhatsApp: Disconnected

📊 Quick Stats:
   Active Chats: 3
   Messages Today: 2
   AI Enabled: 1
   Appointments: 0
```

### **Continuous Monitoring**

```bash
./monitor_connection.sh --watch
```

Updates every 5 seconds with:
- Backend status
- Frontend status
- API connectivity
- WhatsApp connection
- Real-time statistics

---

## 🔧 Connection Issues & Solutions

### Issue 1: Backend Not Responding

**Symptoms:**
- API calls timeout (2 minutes)
- Frontend shows loading forever
- Browser console: `Failed to fetch`

**Solution:**
```bash
# Restart backend
./restart_all.sh
```

### Issue 2: WebSocket Disconnected

**Symptoms:**
- No real-time updates
- QR code doesn't appear
- Messages don't update automatically

**Solution:**
1. Check browser console for WebSocket errors
2. Verify backend is running: `./monitor_connection.sh`
3. Refresh frontend page (Ctrl+R / Cmd+R)

### Issue 3: Port Conflicts

**Symptoms:**
- Backend error: `Address already in use`
- Multiple processes on same port

**Solution:**
```bash
# Kill all backend processes
pkill -9 -f "python.*app.py"
pkill -9 -f "uvicorn"

# Restart cleanly
./restart_all.sh
```

### Issue 4: Database Locked

**Symptoms:**
- API returns 500 errors
- Backend logs: `database is locked`

**Solution:**
```bash
# Clean restart (will reset database)
./restart_all.sh

# Or manually:
pkill -9 -f "python.*app.py"
rm -f backend/whatsapp_secretary.db
cd backend && source venv/bin/activate && python app.py &
```

---

## 📊 Connection States

### Frontend WebSocket States

1. **CONNECTING (0)** - Establishing connection
2. **OPEN (1)** - Connected and ready
3. **CLOSING (2)** - Connection closing
4. **CLOSED (3)** - Disconnected

Check in browser console:
```javascript
// WebSocket state
websocketService.isConnected()  // true/false
```

### Backend States

- **Running** - Server accepting connections
- **Starting** - Initializing services
- **Error** - Crashed or unresponsive
- **Stopped** - Not running

---

## 🔄 Best Practices

### 1. **Development Workflow**

```bash
# Start everything
./start-dev.sh

# Monitor in separate terminal
./monitor_connection.sh --watch

# Make code changes
# Backend auto-reloads (via uvicorn --reload)
# Frontend hot-reloads (via Vite HMR)
```

### 2. **After Code Changes**

Backend changes that affect DB schema:
```bash
# Full restart recommended
./restart_all.sh
```

Frontend changes:
- No restart needed (Vite HMR handles it)

### 3. **Production Deployment**

```bash
# 1. Build frontend
cd frontend && npm run build

# 2. Start backend with production settings
cd backend
export ENVIRONMENT=production
uvicorn app:app --host 0.0.0.0 --port 8001

# 3. Serve frontend via nginx/reverse proxy
```

---

## 📡 WebSocket Connection Details

### Frontend Connection Logic

```typescript
// Auto-detect environment
if (import.meta.env.VITE_WS_URL) {
  url = `${import.meta.env.VITE_WS_URL}/ws`;
} else if (window.location.hostname.includes('ngrok-free.app')) {
  // Use wss for ngrok https URLs
  url = `wss://${window.location.host}/ws`;
} else {
  // Default for local development
  url = `ws://${window.location.host}/ws`;
}
```

### Backend WebSocket Handler

```python
# backend/app.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Handle messages
    except WebSocketDisconnect:
        # Client disconnected
```

---

## 🚨 Emergency Recovery

If everything is broken:

```bash
# 1. Kill ALL processes
pkill -9 -f "python"
pkill -9 -f "node"

# 2. Clean everything
rm -f backend/whatsapp_secretary.db
rm -rf backend/whatsapp_client/.wwebjs_cache/
rm -rf backend/whatsapp_client/whatsapp/

# 3. Fresh start
./restart_all.sh

# 4. Verify
./monitor_connection.sh
```

---

## 📈 Performance Optimization

### 1. **WebSocket Reconnection**

Optimized settings in `frontend/src/services/websocket.ts`:
```typescript
maxReconnectAttempts: 10  // Increased from 5
Backoff delay: exponential (1s → 10s max)
```

### 2. **API Request Timeouts**

```typescript
// frontend/src/services/api.ts
axios.defaults.timeout = 30000;  // 30 seconds
```

### 3. **Database Connection Pool**

```python
# backend/database/database.py
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
```

---

## 🔐 Security Considerations

### 1. **CORS Configuration**

```python
# backend/app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3004", "https://*.ngrok-free.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. **WebSocket Origin Validation**

Backend validates WebSocket connections from trusted origins only.

---

## 📝 Logs & Debugging

### View Real-Time Logs

```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs (in browser)
Press F12 → Console tab
```

### Important Log Patterns

**Successful connection:**
```
✅ WebSocket connected
INFO: WebSocket connection accepted
```

**Connection issues:**
```
❌ WebSocket disconnected: 1006
Attempting to reconnect in 2000ms (attempt 2/10)
```

**Backend errors:**
```
ERROR: Exception in WebSocket connection
INFO: 127.0.0.1:xxx - "GET /api/..." 500 Internal Server Error
```

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Check connection | `./monitor_connection.sh` |
| Continuous monitor | `./monitor_connection.sh --watch` |
| Full restart | `./restart_all.sh` |
| Start dev mode | `./start-dev.sh` |
| Backend only | `./start-backend-only.sh` |
| View backend logs | `tail -f logs/backend.log` |
| Kill backend | `pkill -9 -f "python.*app.py"` |
| Check ports | `lsof -i :8001 -i :3004` |

---

## 🌐 Network Troubleshooting

### Check If Ports Are Open

```bash
# Backend port
lsof -i :8001

# Frontend port
lsof -i :3004

# Should show:
# python3  12345 user   5u  IPv4  TCP localhost:8001 (LISTEN)
# node     12346 user   6u  IPv4  TCP localhost:3004 (LISTEN)
```

### Test Connectivity

```bash
# Test backend HTTP
curl http://localhost:8001/health

# Test backend WebSocket (requires wscat)
npm install -g wscat
wscat -c ws://localhost:8001/ws

# Test frontend
curl http://localhost:3004
```

---

**Generated**: October 5, 2025
**Version**: 2.1.0
**Maintainer**: WhatsApp Secretary Team
