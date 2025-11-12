#!/bin/bash
# Enable AI for all existing chats

echo "🤖 Enabling AI for all chats..."
echo ""

# Wait for backend
until curl -s http://localhost:8001/health > /dev/null 2>&1; do
    echo "⏳ Waiting for backend..."
    sleep 1
done

# Get all chats
CHATS=$(curl -s http://localhost:8001/api/whatsapp/chats | python3 -c "
import sys, json
data = json.load(sys.stdin)
chats = data.get('chats', [])
for chat in chats:
    if chat.get('id') and '@' in chat.get('id', ''):
        print(chat['id'])
")

COUNT=0
ENABLED=0

for CHAT_ID in $CHATS; do
    COUNT=$((COUNT + 1))

    # Skip status broadcasts
    if [[ "$CHAT_ID" == *"status@broadcast"* ]]; then
        echo "⏭️  Skipping: $CHAT_ID (status broadcast)"
        continue
    fi

    # Enable AI for this chat
    RESPONSE=$(curl -s -X POST "http://localhost:8001/api/whatsapp/chats/${CHAT_ID}/toggle-ai?enabled=true" -H "Content-Type: application/json")

    if [[ $RESPONSE == *"success"*true* ]]; then
        ENABLED=$((ENABLED + 1))
        echo "✅ AI enabled for: $CHAT_ID"
    else
        echo "⚠️  Failed to enable AI for: $CHAT_ID"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ AI Auto-Reply Enabled!"
echo ""
echo "📊 Results:"
echo "   Total chats: $COUNT"
echo "   AI enabled: $ENABLED"
echo ""
echo "🤖 All incoming messages will now receive AI responses!"
echo ""
echo "💡 To disable AI for specific chats:"
echo "   Open http://localhost:3004"
echo "   Click on a chat"
echo "   Toggle the 'AI' switch OFF"
