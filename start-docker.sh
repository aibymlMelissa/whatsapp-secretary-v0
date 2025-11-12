#!/bin/bash

# WhatsApp Secretary - Docker Startup Script
# Script to start the system using Docker containers

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🐳 Starting WhatsApp Secretary with Docker${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is required but not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}docker-compose is required but not installed${NC}"
    echo "Please install docker-compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping Docker containers...${NC}"
    docker-compose down
    echo -e "${GREEN}Cleanup completed${NC}"
}

trap cleanup EXIT

# Stop any existing containers
echo -e "${BLUE}Stopping existing containers...${NC}"
docker-compose down 2>/dev/null || true

# Build and start containers
echo -e "${BLUE}Building and starting Docker containers...${NC}"
docker-compose up --build -d

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 10

# Check backend health
echo "Checking backend health..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8001/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi

    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}❌ Backend failed to start${NC}"
        echo "Checking backend logs:"
        docker-compose logs backend
        exit 1
    fi

    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

# Display status
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   🐳 DOCKER CONTAINERS READY              ║"
echo "║                                                            ║"
echo "║  🌐 Frontend:   http://localhost:3000                     ║"
echo "║  📡 Backend:    http://localhost:8001                     ║"
echo "║  📚 API Docs:   http://localhost:8001/docs                ║"
echo "║  🗄️  Database:   PostgreSQL on port 5432                  ║"
echo "║  📦 Redis:      Redis on port 6379                        ║"
echo "║                                                            ║"
echo "║  💡 To connect WhatsApp:                                   ║"
echo "║     1. Open http://localhost:3000                         ║"
echo "║     2. Click 'Connect' in WhatsApp status panel           ║"
echo "║     3. Scan QR code with your WhatsApp app                ║"
echo "║                                                            ║"
echo "║  📊 To view logs: docker-compose logs -f                  ║"
echo "║  🛑 To stop: Ctrl+C or docker-compose down               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Show container status
echo -e "${BLUE}Container Status:${NC}"
docker-compose ps

echo -e "\n${BLUE}Following logs... (Ctrl+C to stop)${NC}"
docker-compose logs -f