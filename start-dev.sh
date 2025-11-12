#!/bin/bash

# WhatsApp Secretary - Development Startup Script
# Simplified script for development environment

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting WhatsApp Secretary in Development Mode${NC}"

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"

    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "Backend stopped"
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "Frontend stopped"
    fi

    echo -e "${GREEN}Cleanup completed${NC}"
}

trap cleanup EXIT

# Check prerequisites
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is required but not installed${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm is required but not installed${NC}"
    exit 1
fi

# Clean WhatsApp session for fresh QR code
echo -e "${BLUE}🧹 Cleaning WhatsApp session...${NC}"
rm -rf backend/whatsapp_client/whatsapp-session 2>/dev/null || true
rm -f backend/whatsapp_client/qr_code.txt 2>/dev/null || true
rm -f backend/whatsapp_client/status.json 2>/dev/null || true
echo -e "${GREEN}✅ WhatsApp session cleaned${NC}"

# Start Backend
echo -e "${BLUE}📡 Starting Backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

# Start backend in background
python app.py &
BACKEND_PID=$!

cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start Frontend
echo -e "${BLUE}🌐 Starting Frontend...${NC}"
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install > /dev/null 2>&1
fi

# Start frontend in background
npm run dev &
FRONTEND_PID=$!

cd ..

# Display status
sleep 3
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ DEVELOPMENT SERVER READY             ║"
echo "║                                                            ║"
echo "║  🌐 Frontend:   http://localhost:3004                     ║"
echo "║  📡 Backend:    http://localhost:8001                     ║"
echo "║  📚 API Docs:   http://localhost:8001/docs                ║"
echo "║                                                            ║"
echo "║  💡 To connect WhatsApp:                                   ║"
echo "║     1. Open http://localhost:3004                         ║"
echo "║     2. Click 'Connect' in WhatsApp status panel           ║"
echo "║     3. Scan QR code with your WhatsApp app                ║"
echo "║                                                            ║"
echo "║  🛑 Press Ctrl+C to stop all services                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Keep script running
echo -e "${BLUE}Monitoring services... (Ctrl+C to stop)${NC}"
while true; do
    sleep 1
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend process stopped unexpectedly${NC}"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}Frontend process stopped unexpectedly${NC}"
        break
    fi
done