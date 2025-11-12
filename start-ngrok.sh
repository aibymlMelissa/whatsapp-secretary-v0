#!/bin/bash

# Start WhatsApp Secretary with ngrok support
echo "🚀 Starting WhatsApp Secretary with ngrok support..."

# Check if ngrok is running and get the URL
NGROK_URL=$(curl -s localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok-free\.app' | head -1)

if [ -z "$NGROK_URL" ]; then
    echo "❌ No ngrok tunnel found. Please start ngrok first:"
    echo "   ngrok http 8001"
    exit 1
fi

echo "🔗 Found ngrok URL: $NGROK_URL"

# Update the backend CORS settings with the ngrok URL
echo "📝 Updating backend CORS settings..."
if ! grep -q "$NGROK_URL" backend/app.py; then
    # Add ngrok URL to CORS origins in backend
    sed -i.bak "s|\"http://curious-ferret-tight.ngrok-free.app\"|\"$NGROK_URL\"|g" backend/app.py
    sed -i.bak "s|\"https://curious-ferret-tight.ngrok-free.app\"|\"$NGROK_URL\"|g" backend/app.py
fi

# Create environment file for frontend
echo "🌐 Setting up frontend environment for ngrok..."
cat > frontend/.env.local << EOF
VITE_BACKEND_URL=$NGROK_URL
VITE_WS_URL=${NGROK_URL/https/wss}
EOF

# Start backend in background
echo "🚀 Starting backend server..."
cd backend
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend with ngrok environment
echo "🚀 Starting frontend with ngrok proxy..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ Services started!"
echo "🌐 Backend: $NGROK_URL"
echo "🖥️  Frontend: ${NGROK_URL/8001/3004}"
echo ""
echo "To stop services, press Ctrl+C"

# Handle cleanup on exit
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait