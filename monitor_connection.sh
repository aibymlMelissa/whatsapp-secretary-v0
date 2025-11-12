#!/bin/bash
# Connection Monitor - Ensures backend and frontend stay connected

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 WhatsApp Secretary - Connection Monitor${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to check backend
check_backend() {
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend: Running"
        return 0
    else
        echo -e "${RED}✗${NC} Backend: Down"
        return 1
    fi
}

# Function to check frontend
check_frontend() {
    if lsof -i :3004 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend: Running"
        return 0
    else
        echo -e "${RED}✗${NC} Frontend: Down"
        return 1
    fi
}

# Function to check API connectivity
check_api() {
    RESPONSE=$(curl -s http://localhost:8001/api/whatsapp/stats)
    if [[ $RESPONSE == *"success"* ]]; then
        echo -e "${GREEN}✓${NC} API: Connected"
        return 0
    else
        echo -e "${RED}✗${NC} API: Not responding"
        return 1
    fi
}

# Function to check WhatsApp connection
check_whatsapp() {
    HEALTH=$(curl -s http://localhost:8001/health)
    CONNECTED=$(echo $HEALTH | grep -o '"connected":[^,]*' | cut -d: -f2)

    if [[ $CONNECTED == "true" ]]; then
        echo -e "${GREEN}✓${NC} WhatsApp: Connected"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} WhatsApp: Disconnected"
        return 1
    fi
}

# Continuous monitoring mode
if [[ "$1" == "--watch" ]]; then
    echo "Continuous monitoring mode (Ctrl+C to stop)"
    echo ""

    while true; do
        clear
        echo -e "${BLUE}🔍 WhatsApp Secretary - Connection Monitor${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "$(date '+%Y-%m-%d %H:%M:%S')"
        echo ""

        check_backend
        BACKEND_STATUS=$?

        check_frontend
        FRONTEND_STATUS=$?

        if [[ $BACKEND_STATUS -eq 0 ]]; then
            check_api
            check_whatsapp
        fi

        echo ""
        echo -e "${BLUE}📊 Quick Stats:${NC}"
        if [[ $BACKEND_STATUS -eq 0 ]]; then
            STATS=$(curl -s http://localhost:8001/api/whatsapp/stats | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        stats = data['stats']
        print(f\"   Active Chats: {stats.get('active_chats', 0)}\")
        print(f\"   Messages Today: {stats.get('messages_today', 0)}\")
        print(f\"   AI Enabled: {stats.get('ai_enabled_chats', 0)}\")
        print(f\"   Appointments: {stats.get('upcoming_appointments', 0)}\")
except:
    pass
" 2>/dev/null)
            echo "$STATS"
        else
            echo -e "   ${RED}Backend down - stats unavailable${NC}"
        fi

        echo ""
        echo -e "${YELLOW}💡 Press Ctrl+C to stop monitoring${NC}"

        sleep 5
    done
else
    # Single check mode
    check_backend
    BACKEND_STATUS=$?

    check_frontend
    FRONTEND_STATUS=$?

    if [[ $BACKEND_STATUS -eq 0 ]]; then
        check_api
        check_whatsapp
    fi

    echo ""

    if [[ $BACKEND_STATUS -eq 0 ]] && [[ $FRONTEND_STATUS -eq 0 ]]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✨ All systems operational!${NC}"
        echo ""
        echo -e "${BLUE}📋 Service URLs:${NC}"
        echo "   Frontend: http://localhost:3004"
        echo "   Backend:  http://localhost:8001"
        echo "   API Docs: http://localhost:8001/docs"
        echo ""
        echo -e "${YELLOW}💡 Run with --watch for continuous monitoring${NC}"
    else
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}⚠️  System issues detected!${NC}"
        echo ""
        echo -e "${YELLOW}Run ./restart_all.sh to fix${NC}"
    fi
fi
echo ""
