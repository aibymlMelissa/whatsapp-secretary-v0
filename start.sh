#!/bin/bash

# WhatsApp Secretary - Main Startup Script
# This script starts the complete WhatsApp Secretary system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$host:$port/health" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to cleanup on exit
cleanup() {
    print_warning "Shutting down services..."

    # Kill backend if running
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        print_status "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi

    # Kill frontend if running
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        print_status "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    print_success "Cleanup completed"
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Main execution starts here
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    WhatsApp Secretary                        ║"
echo "║                   System Startup Script                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running in development or production mode
MODE=${1:-"dev"}

if [ "$MODE" = "docker" ]; then
    print_status "Starting WhatsApp Secretary in Docker mode..."

    # Check if Docker is installed
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if docker-compose is installed
    if ! command_exists docker-compose; then
        print_error "docker-compose is not installed. Please install docker-compose first."
        exit 1
    fi

    # Stop any existing containers
    print_status "Stopping existing containers..."
    docker-compose down 2>/dev/null || true

    # Build and start containers
    print_status "Building and starting Docker containers..."
    docker-compose up --build -d

    # Wait for services to be ready
    sleep 5

    print_status "Checking service health..."
    if wait_for_service "http://localhost" "8001" "Backend API"; then
        print_success "Backend is running at http://localhost:8001"
        print_success "API Documentation available at http://localhost:8001/docs"
    fi

    print_success "Frontend is running at http://localhost:3000"
    print_success "WhatsApp Secretary is ready! 🚀"

    # Follow logs
    print_status "Following container logs (Ctrl+C to stop)..."
    docker-compose logs -f

elif [ "$MODE" = "dev" ] || [ "$MODE" = "development" ]; then
    print_status "Starting WhatsApp Secretary in Development mode..."

    # Check prerequisites
    print_status "Checking prerequisites..."

    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.11+"
        exit 1
    fi

    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 18+"
        exit 1
    fi

    if ! command_exists npm; then
        print_error "npm is not installed. Please install npm"
        exit 1
    fi

    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
        print_warning "Python version $python_version detected. Python 3.11+ is recommended."
    fi

    # Check Node.js version
    node_version=$(node --version | cut -d'v' -f2)
    if ! node -e 'process.exit(process.version.match(/^v(\d+)/)[1] >= 18 ? 0 : 1)'; then
        print_warning "Node.js version $node_version detected. Node.js 18+ is recommended."
    fi

    # Check if ports are available
    if check_port 8001; then
        print_error "Port 8001 is already in use. Please stop the service using this port."
        exit 1
    fi

    if check_port 3000; then
        print_error "Port 3000 is already in use. Please stop the service using this port."
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env file from template"
            print_warning "Please edit .env file with your API keys before proceeding"
            read -p "Press Enter to continue after editing .env file..."
        else
            print_error ".env file is required. Please create one with the necessary configuration."
            exit 1
        fi
    fi

    # Setup backend
    print_status "Setting up backend environment..."
    cd backend

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate

    # Install backend dependencies
    print_status "Installing backend dependencies..."
    pip install -r requirements.txt

    # Start backend
    print_status "Starting backend server..."
    python app.py &
    BACKEND_PID=$!

    cd ..

    # Wait for backend to be ready
    if wait_for_service "http://localhost" "8001" "Backend API"; then
        print_success "Backend is running at http://localhost:8001"
        print_success "API Documentation available at http://localhost:8001/docs"
    else
        print_error "Backend failed to start"
        exit 1
    fi

    # Setup frontend
    print_status "Setting up frontend environment..."
    cd frontend

    # Install frontend dependencies
    if [ ! -d "node_modules" ]; then
        print_status "Installing frontend dependencies..."
        npm install
    fi

    # Start frontend
    print_status "Starting frontend development server..."
    npm run dev &
    FRONTEND_PID=$!

    cd ..

    # Wait a moment for frontend to start
    sleep 3

    print_success "Frontend is starting at http://localhost:3000"

    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🚀 SYSTEM READY! 🚀                      ║"
    echo "║                                                              ║"
    echo "║  Frontend:  http://localhost:3000                           ║"
    echo "║  Backend:   http://localhost:8001                           ║"
    echo "║  API Docs:  http://localhost:8001/docs                      ║"
    echo "║                                                              ║"
    echo "║  Press Ctrl+C to stop all services                          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Keep script running and show logs
    print_status "Services are running. Monitoring logs..."
    print_status "Backend PID: $BACKEND_PID"
    print_status "Frontend PID: $FRONTEND_PID"

    # Wait for user interrupt
    while true; do
        sleep 1
        # Check if processes are still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            break
        fi
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            break
        fi
    done

else
    print_error "Invalid mode: $MODE"
    print_status "Usage: $0 [dev|docker]"
    print_status "  dev    - Start in development mode (default)"
    print_status "  docker - Start using Docker containers"
    exit 1
fi