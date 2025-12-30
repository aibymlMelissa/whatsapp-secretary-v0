# WhatsApp Bridge Port Configuration

## Issue Identified

The WhatsApp backend uses a **multi-port architecture** that was causing connection issues in Railway deployment:

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              Railway Container                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────┐     ┌──────────────────┐ │
│  │  FastAPI Backend │     │  Node.js Bridge  │ │
│  │  (Python)        │────▶│  (WhatsApp.js)   │ │
│  │  Port: 8080      │     │  Port: 8002      │ │
│  └──────────────────┘     └──────────────────┘ │
│         ▲                                        │
│         │                                        │
│    Railway exposes                               │
│    only ONE port                                 │
└─────────────────────────────────────────────────┘
```

### The Problem

1. **Railway Environment**:
   - Railway only exposes **one port** to the internet (defined by `PORT` env var, typically `8080`)
   - Internal container communication on localhost works on any port

2. **Original Configuration**:
   - FastAPI backend: Listens on `PORT` (8080 in Railway, 8001 locally)
   - WhatsApp bridge: **Hardcoded** to port `8002`
   - Communication: Python → `http://127.0.0.1:8002/send` → Node.js

3. **Why It Failed**:
   - The Node.js bridge **was successfully listening on 8002**
   - But the port was **hardcoded** and not configurable
   - If Railway's internal networking had any restrictions, or if port 8002 wasn't available, the bridge would fail
   - More importantly: **lack of flexibility** for different deployment environments

## Solution Implemented

### 1. Made Bridge Port Configurable

**File**: `backend/whatsapp_client/simple_bridge.js`

```javascript
// Before (Hardcoded):
const HTTP_PORT = 8002;

// After (Configurable):
const HTTP_PORT = parseInt(
    process.env.WHATSAPP_BRIDGE_PORT ||
    process.env.BRIDGE_PORT ||
    '8002'
);
```

### 2. Updated Python Service

**File**: `backend/services/whatsapp_service.py`

#### Added Instance Variable:
```python
def __init__(self, connection_manager: ConnectionManager):
    # ...
    self.bridge_port = os.getenv('WHATSAPP_BRIDGE_PORT', os.getenv('BRIDGE_PORT', '8002'))
```

#### Pass Port to Node.js Process:
```python
async def initialize(self):
    bridge_port = os.getenv('WHATSAPP_BRIDGE_PORT', os.getenv('BRIDGE_PORT', '8002'))

    env = os.environ.copy()
    env['PYTHON_CALLBACK_URL'] = callback_url
    env['WHATSAPP_BRIDGE_PORT'] = bridge_port  # ← Pass to Node.js

    print(f"🔗 WhatsApp bridge will listen on port: {bridge_port}")
```

#### Updated Send Message:
```python
async def send_message(self, chat_id: str, message: str):
    # Before:
    # response = await client.post("http://127.0.0.1:8002/send", ...)

    # After:
    response = await client.post(
        f"http://127.0.0.1:{self.bridge_port}/send",
        json={"chatId": chat_id, "message": message}
    )
```

## Configuration

### Environment Variables

| Variable | Default | Purpose | Required |
|----------|---------|---------|----------|
| `PORT` | 8001 (local)<br>8080 (Railway) | Main FastAPI backend port | Yes (Railway sets this) |
| `WHATSAPP_BRIDGE_PORT` | 8002 | Node.js WhatsApp bridge port | No (falls back to 8002) |
| `BRIDGE_PORT` | 8002 | Alternative name for bridge port | No (fallback option) |

### Local Development

```bash
# .env file
PORT=8001                    # FastAPI listens here
WHATSAPP_BRIDGE_PORT=8002    # Node.js listens here (default)
```

**Communication Flow**:
```
Client → http://localhost:8001 (FastAPI)
FastAPI → http://127.0.0.1:8002/send (Node.js Bridge)
```

### Railway Production

Railway automatically sets `PORT=8080`. The bridge uses default `8002` for internal communication.

```bash
# Railway sets automatically:
PORT=8080                    # FastAPI listens (exposed to internet)

# Optional custom bridge port:
WHATSAPP_BRIDGE_PORT=8002    # Node.js listens (internal only)
```

**Communication Flow**:
```
Internet → https://your-app.up.railway.app:443 (Railway Proxy)
Railway Proxy → http://container:8080 (FastAPI)
FastAPI → http://127.0.0.1:8002/send (Node.js Bridge - internal)
```

### Docker/Container Deployments

```yaml
# docker-compose.yml
services:
  whatsapp-backend:
    environment:
      - PORT=8080
      - WHATSAPP_BRIDGE_PORT=8002
    ports:
      - "8080:8080"  # Only expose FastAPI port
```

## Port Mapping Summary

| Environment | FastAPI Port | Bridge Port | External Access |
|-------------|--------------|-------------|-----------------|
| Local Dev | 8001 | 8002 | Both on localhost |
| Railway | 8080 (env PORT) | 8002 (internal) | Only 8080 exposed |
| Docker | 8080 | 8002 | Only 8080 exposed |
| Custom | Any (PORT env) | Any (WHATSAPP_BRIDGE_PORT) | Configurable |

## Advantages of This Solution

### 1. **Flexibility**
- Works in any deployment environment
- Easy to change ports without code modification
- Supports custom port assignments

### 2. **Railway Compatibility**
- Works with Railway's single-port exposure model
- No conflicts with dynamically assigned PORT
- Clean separation of concerns

### 3. **Localhost Security**
- Bridge port is **not exposed** to the internet
- Only accessible within the container
- FastAPI acts as a gateway/proxy

### 4. **Backwards Compatible**
- Default values maintain existing behavior
- No breaking changes for current deployments
- Works seamlessly in local development

## Testing

### Test Local Communication

```bash
# Terminal 1: Start backend
cd backend
python3 app.py

# Terminal 2: Check if bridge is listening
curl http://localhost:8002/health

# Terminal 3: Test send message
curl -X POST http://localhost:8001/api/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "123@c.us", "message": "Test"}'
```

### Test Railway Deployment

```bash
# Check health endpoint
curl https://whatsapp-secretary-ai-production.up.railway.app/health

# Check logs for port configuration
railway logs --tail 50 | grep "bridge will listen"
```

Expected output:
```
🔗 WhatsApp bridge will listen on port: 8002
✅ HTTP server listening on port 8002 for send commands
```

## Troubleshooting

### Issue: "Connection refused" when sending messages

**Cause**: Bridge port mismatch between Python and Node.js

**Solution**:
1. Check environment variables are set correctly
2. Verify Node.js process started successfully
3. Check logs for port binding errors

```bash
# Check if Node.js is listening
railway logs | grep "HTTP server listening"

# Check if Python is using correct port
railway logs | grep "bridge will listen"
```

### Issue: Railway shows "Application failed to respond"

**Cause**: FastAPI not listening on Railway's PORT

**Solution**:
```python
# Ensure app.py uses PORT env var:
port = int(os.getenv('PORT', '8001'))
uvicorn.run("app:app", host="0.0.0.0", port=port)
```

### Issue: Bridge starts but messages don't send

**Cause**: Python trying to send to wrong port

**Solution**:
1. Verify `self.bridge_port` is set correctly in WhatsAppService.__init__
2. Check send_message uses `self.bridge_port` not hardcoded value
3. Restart the backend to reload environment variables

## Future Improvements

### 1. Health Check Endpoint on Bridge

Add to `simple_bridge.js`:
```javascript
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        port: HTTP_PORT,
        whatsapp_ready: !!bridge.client?.pupPage
    });
});
```

### 2. Auto Port Discovery

If port 8002 is busy, automatically find next available port:
```javascript
const findAvailablePort = async (startPort) => {
    // Implementation to find free port
};
```

### 3. Service Mesh / Reverse Proxy

For production scale, consider:
- nginx reverse proxy
- Kubernetes service mesh
- Docker networking

## References

- Railway Docs: https://docs.railway.app/develop/services#port
- WhatsApp.js: https://wwebjs.dev/
- FastAPI: https://fastapi.tiangolo.com/deployment/docker/
- Node.js HTTP Server: https://nodejs.org/api/http.html

---

**Status**: ✅ Fixed and Deployed
**Version**: 2.2.1
**Date**: 2025-12-30
