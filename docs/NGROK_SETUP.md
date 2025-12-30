# Running WhatsApp Secretary with ngrok

This guide explains how to make your WhatsApp Secretary accessible via ngrok (public internet).

## Quick Start

### Option 1: Using the automated script (Recommended)

1. **Start ngrok tunnel:**
   ```bash
   # In terminal 1: Start ngrok for backend
   ngrok http 8001
   ```
   Note the https URL (e.g., `https://abc123.ngrok-free.app`)

2. **Use the automated script:**
   ```bash
   # In terminal 2: Use our automated script
   ./start-ngrok.sh
   ```

### Option 2: Manual setup

1. **Start ngrok:**
   ```bash
   ngrok http 8001
   ```

2. **Update backend CORS (if needed):**
   Edit `backend/app.py` and add your ngrok URL to the CORS origins list:
   ```python
   allow_origins=[
       # ... existing origins ...
       "https://your-ngrok-url.ngrok-free.app",
       "http://your-ngrok-url.ngrok-free.app"
   ],
   ```

3. **Create frontend environment file:**
   Create `frontend/.env.local`:
   ```bash
   VITE_BACKEND_URL=https://your-ngrok-url.ngrok-free.app
   VITE_WS_URL=wss://your-ngrok-url.ngrok-free.app
   ```

4. **Start services:**
   ```bash
   # Terminal 1: Backend
   cd backend && python app.py

   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

5. **Access via ngrok:**
   Open `https://your-ngrok-url.ngrok-free.app:3004` in your browser

## How It Works

The solution includes several improvements to make ngrok work seamlessly:

### 1. Dynamic API Detection
- The frontend automatically detects if it's running on a ngrok domain
- API calls are automatically routed to the correct backend URL
- No manual configuration needed in most cases

### 2. WebSocket Support
- WebSocket connections automatically use `wss://` for https ngrok URLs
- Automatic fallback for different environments

### 3. CORS Configuration
- Backend is pre-configured with common ngrok patterns
- Easy to add new ngrok URLs as needed

### 4. Environment Variables
- Support for custom backend URLs via `VITE_BACKEND_URL`
- Support for custom WebSocket URLs via `VITE_WS_URL`

## Troubleshooting

### QR Code Not Loading
If the QR code shows "timeout of 10000ms exceeded":

1. **Check ngrok is running:** Verify ngrok is active with `curl https://your-url.ngrok-free.app/health`
2. **Verify CORS:** Ensure your ngrok URL is in the backend CORS list
3. **Check network:** ngrok requires internet connection
4. **Try refresh:** Click the refresh button in the QR code section

### WebSocket Connection Issues
1. **Check URL:** Ensure WebSocket uses `wss://` for https ngrok URLs
2. **Browser console:** Check for WebSocket errors in browser dev tools
3. **Firewall:** Ensure ngrok tunnel allows WebSocket connections

### Performance Issues
- ngrok free tier has limitations on bandwidth and connections
- Consider ngrok paid plans for production use
- Local development is always faster than ngrok tunnels

## Production Considerations

For production deployment:
- Use a proper reverse proxy (nginx, Apache)
- Set up SSL certificates
- Use environment variables for configuration
- Consider using a VPS or cloud hosting instead of ngrok

## Security Notes

- ngrok exposes your local server to the internet
- Use ngrok's authentication features for additional security
- Never commit ngrok URLs to version control
- Monitor ngrok access logs for suspicious activity