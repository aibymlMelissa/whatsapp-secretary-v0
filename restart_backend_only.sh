#!/bin/bash
# Restart backend only (without cleaning database)

echo "🔄 Restarting backend..."

# Kill backend processes
echo "⏹️  Stopping backend..."
pkill -9 -f "python.*app.py" 2>/dev/null
pkill -9 -f "uvicorn" 2>/dev/null
sleep 2

# Start backend
echo "🚀 Starting backend..."
cd /Users/aibyml.com/WhatsAppSecretary_v0/backend
source venv/bin/activate
python app.py > ../logs/backend.log 2>&1 &

# Wait for backend
echo "⏳ Waiting for backend..."
sleep 5

for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start"
        exit 1
    fi
done

echo ""
echo "✨ Backend restarted successfully!"
echo "📊 Check status: curl http://localhost:8001/health"
