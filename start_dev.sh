#!/bin/bash

# WhatsApp Secretary AI - Development Startup Script
# This script starts the backend, frontend, and monitors the services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  WhatsApp Secretary AI - Dev Startup${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}Services stopped.${NC}"
}

trap cleanup EXIT INT TERM

# Check Python venv
if [ ! -d "backend/venv" ]; then
    echo -e "${RED}Error: Python virtual environment not found${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    cd backend
    python3 -m venv venv
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    venv/bin/pip install -r requirements.txt
    cd ..
fi

# Check Node modules for backend WhatsApp client
if [ ! -d "backend/whatsapp_client/node_modules" ]; then
    echo -e "${YELLOW}Installing WhatsApp client dependencies...${NC}"
    cd backend/whatsapp_client
    npm install
    cd ../..
fi

# Check Node modules for frontend
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Start Backend
echo -e "\n${GREEN}Starting Backend (FastAPI)...${NC}"
cd backend
venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo -e "  Backend API: ${YELLOW}http://localhost:8001${NC}"
echo -e "  API Docs: ${YELLOW}http://localhost:8001/docs${NC}"

# Wait for backend to start
echo -e "\n${YELLOW}Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: Backend failed to start${NC}"
        echo -e "${YELLOW}Check logs/backend.log for details${NC}"
        exit 1
    fi
    sleep 1
done

# Start Frontend
echo -e "\n${GREEN}Starting Frontend (Vite)...${NC}"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend to start
echo -e "\n${YELLOW}Waiting for frontend to be ready...${NC}"
sleep 3

# Find the actual port the frontend is running on
FRONTEND_PORT=$(lsof -p $FRONTEND_PID 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
if [ -z "$FRONTEND_PORT" ]; then
    FRONTEND_PORT="3004"
fi

echo -e "${GREEN}✓ Frontend is ready!${NC}"
echo -e "  Frontend URL: ${YELLOW}http://localhost:${FRONTEND_PORT}${NC}"

# Display status
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  All services are running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Backend:  ${YELLOW}http://localhost:8001${NC} (PID: $BACKEND_PID)"
echo -e "Frontend: ${YELLOW}http://localhost:${FRONTEND_PORT}${NC} (PID: $FRONTEND_PID)"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"
echo -e "\n${YELLOW}Logs:${NC}"
echo -e "  Backend:  tail -f logs/backend.log"
echo -e "  Frontend: tail -f logs/frontend.log"

# Keep the script running
wait
