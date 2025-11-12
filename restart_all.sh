#!/bin/bash

echo "🔄 WhatsApp Secretary - Complete System Restart"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Kill all backend processes
echo -e "${YELLOW}1. Stopping backend processes...${NC}"
pkill -9 -f "python.*app.py" 2>/dev/null
pkill -9 -f "uvicorn" 2>/dev/null
pkill -9 -f "start-backend" 2>/dev/null
sleep 2
echo -e "${GREEN}   ✓ Backend processes stopped${NC}"

# Step 2: Clean database
echo -e "${YELLOW}2. Cleaning database...${NC}"
rm -f backend/whatsapp_secretary.db
echo -e "${GREEN}   ✓ Database cleaned${NC}"

# Step 3: Start backend
echo -e "${YELLOW}3. Starting backend...${NC}"
cd backend

# Activate venv and start
source venv/bin/activate
python app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

cd ..

# Wait for backend to be ready
echo -e "${BLUE}   Waiting for backend to initialize...${NC}"
sleep 5

for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Backend is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}   ✗ Backend failed to start${NC}"
        echo -e "${RED}   Check logs/backend.log for errors${NC}"
        exit 1
    fi
done

# Step 4: Check frontend
echo -e "${YELLOW}4. Checking frontend...${NC}"
if lsof -i :3004 > /dev/null 2>&1; then
    echo -e "${GREEN}   ✓ Frontend is running on http://localhost:3004${NC}"
else
    echo -e "${YELLOW}   Frontend not running. Starting it...${NC}"
    cd frontend
    npm run dev > ../logs/frontend.log 2>&1 &
    cd ..
    sleep 3
    echo -e "${GREEN}   ✓ Frontend started${NC}"
fi

# Step 5: Apply whitelist
echo -e "${YELLOW}5. Applying whitelist configuration...${NC}"
sleep 2

# Whitelist contacts
./whitelist_contact.sh

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ System restart complete!${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo -e "   Backend:  http://localhost:8001"
echo -e "   Frontend: http://localhost:3004"
echo -e "   API Docs: http://localhost:8001/docs"
echo ""
echo -e "${BLUE}📋 Whitelisted Contacts:${NC}"
echo -e "   • 85256878772 (Trusted + AI Enabled)"
echo -e "   • 85260552717 (Trusted + AI Enabled)"
echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo -e "   1. Open http://localhost:3004 in your browser"
echo -e "   2. Click on a chat to view messages"
echo -e "   3. Send a message with 'appointment' to test AI"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "   Backend:  tail -f logs/backend.log"
echo -e "   Frontend: tail -f logs/frontend.log"
echo ""
