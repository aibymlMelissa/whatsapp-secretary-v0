#!/bin/bash

# WhatsApp Secretary - Backend Only Startup Script
# For testing or development of backend services only

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 Starting WhatsApp Secretary Backend Only${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping backend service...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "Backend stopped"
    fi
    echo -e "${GREEN}Cleanup completed${NC}"
}

trap cleanup EXIT

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed${NC}"
    exit 1
fi

# Clean WhatsApp session for fresh QR code
echo -e "${BLUE}🧹 Cleaning WhatsApp session...${NC}"
rm -rf backend/whatsapp_client/whatsapp-session 2>/dev/null || true
rm -f backend/whatsapp_client/qr_code.txt 2>/dev/null || true
rm -f backend/whatsapp_client/status.json 2>/dev/null || true
echo -e "${GREEN}✅ WhatsApp session cleaned${NC}"

# Navigate to backend directory
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt > /dev/null

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found in project root${NC}"
    echo "Creating basic .env file for backend-only mode..."
    cat > ../.env << 'EOF'
# Basic configuration for backend-only mode
DATABASE_URL=sqlite:///./whatsapp_secretary.db
WHATSAPP_SESSION_PATH=./whatsapp-session
MEDIA_DOWNLOAD_PATH=./downloads
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_LLM_PROVIDER=openai
API_HOST=0.0.0.0
API_PORT=8001
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
EOF
    echo -e "${GREEN}Created basic .env file${NC}"
    echo -e "${YELLOW}Please edit .env with your API keys if needed${NC}"
fi

# Create necessary directories
mkdir -p whatsapp-session downloads logs static

# Start backend
echo -e "${BLUE}Starting backend server...${NC}"
python app.py &
BACKEND_PID=$!

# Wait for backend to be ready
echo -e "${BLUE}Waiting for backend to be ready...${NC}"
sleep 5

# Check if backend is running
if curl -s http://localhost:8001/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is ready!${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    echo "Check the logs above for errors"
    exit 1
fi

# Display status
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   📡 BACKEND SERVER READY                 ║"
echo "║                                                            ║"
echo "║  🔗 API Server:   http://localhost:8001                   ║"
echo "║  📚 API Docs:     http://localhost:8001/docs              ║"
echo "║  🏥 Health Check: http://localhost:8001/health            ║"
echo "║  📊 OpenAPI:      http://localhost:8001/openapi.json      ║"
echo "║                                                            ║"
echo "║  💡 Available Endpoints:                                   ║"
echo "║     • /api/whatsapp/* - WhatsApp operations                ║"
echo "║     • /api/appointments/* - Appointment management        ║"
echo "║     • /api/llm/* - LLM operations                         ║"
echo "║     • /api/files/* - File management                      ║"
echo "║     • /ws - WebSocket connection                          ║"
echo "║                                                            ║"
echo "║  🧪 Test the API:                                          ║"
echo "║     curl http://localhost:8001/health                     ║"
echo "║                                                            ║"
echo "║  🛑 Press Ctrl+C to stop the backend                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Show some useful curl commands
echo -e "${BLUE}💡 Useful API test commands:${NC}"
echo -e "${YELLOW}curl http://localhost:8001/health${NC}                    # Health check"
echo -e "${YELLOW}curl http://localhost:8001/api/whatsapp/status${NC}        # WhatsApp status"
echo -e "${YELLOW}curl -X POST http://localhost:8001/api/whatsapp/connect${NC} # Connect WhatsApp"
echo ""

# Keep script running
echo -e "${BLUE}Backend is running... (Ctrl+C to stop)${NC}"
while true; do
    sleep 1
    # Check if process is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend process stopped unexpectedly${NC}"
        break
    fi
done