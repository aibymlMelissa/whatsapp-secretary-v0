# 🚀 Quick Start Guide

## Choose Your Startup Method

### 1. 🎯 **Recommended: Simple Development Start**
```bash
./start-dev.sh
```
or on Windows:
```cmd
start.bat dev
```

### 2. 🐳 **Docker (Full Stack)**
```bash
./start-docker.sh
```
or on Windows:
```cmd
start.bat docker
```

### 3. 📡 **Backend Only (For API Testing)**
```bash
./start-backend-only.sh
```

### 4. ⚙️ **Full Control Start**
```bash
./start.sh dev     # Development mode
./start.sh docker  # Docker mode
```

---

## 📋 Prerequisites

### For Development Mode:
- **Python 3.11+** - [Download](https://python.org)
- **Node.js 18+** - [Download](https://nodejs.org)
- **npm** (comes with Node.js)

### For Docker Mode:
- **Docker** - [Download](https://docker.com)
- **docker-compose** - [Download](https://docs.docker.com/compose/install/)

---

## ⚡ Fastest Start (Development)

1. **Run the startup script:**
   ```bash
   ./start-dev.sh
   ```

2. **Open your browser:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Documentation: http://localhost:8001/docs

3. **Connect WhatsApp:**
   - Click "Connect" in the WhatsApp status panel
   - Scan the QR code with your WhatsApp mobile app
   - Start managing conversations!

---

## 🔧 Configuration

The `.env` file will be created automatically with default values. Update these if needed:

```env
# Required: Add your API keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Customize settings
DEFAULT_LLM_PROVIDER=openai
API_PORT=8001
```

---

## 🎛️ Available Services

Once started, you'll have access to:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend Dashboard** | http://localhost:3000 | Main user interface |
| **Backend API** | http://localhost:8001 | REST API endpoints |
| **API Documentation** | http://localhost:8001/docs | Interactive API docs |
| **Health Check** | http://localhost:8001/health | System status |
| **WebSocket** | ws://localhost:8001/ws | Real-time communication |

---

## 🛑 Stopping the System

### Development Mode:
- Press `Ctrl+C` in the terminal running the startup script

### Docker Mode:
- Press `Ctrl+C` in the terminal, or run:
  ```bash
  docker-compose down
  ```

### Individual Services:
- Close the terminal windows where services are running

---

## 🐛 Troubleshooting

### Port Already in Use:
```bash
# Check what's using the port
lsof -i :8001  # Backend port
lsof -i :3000  # Frontend port

# Kill the process
kill -9 <PID>
```

### Python Virtual Environment Issues:
```bash
# Remove and recreate
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Node.js Module Issues:
```bash
# Clean and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Docker Issues:
```bash
# Clean Docker containers and images
docker-compose down
docker system prune -f
docker-compose up --build
```

---

## 📚 Next Steps

1. **Connect WhatsApp** - Follow the QR code setup
2. **Configure AI APIs** - Add your OpenAI/Anthropic keys to `.env`
3. **Test Features** - Try sending messages and booking appointments
4. **Customize Settings** - Modify business hours and appointment settings
5. **Explore API** - Check out the interactive docs at `/docs`

---

## 🆘 Need Help?

- Check the full [README.md](README.md) for detailed documentation
- Review the [API Documentation](http://localhost:8001/docs) when running
- Create an issue on GitHub for bugs or feature requests

---

**🎉 You're ready to go! Start with `./start-dev.sh` and you'll be up and running in under a minute!**