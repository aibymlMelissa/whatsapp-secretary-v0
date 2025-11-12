#!/bin/bash
# Script to whitelist contacts and enable AI

# List of phone numbers to whitelist
PHONES=("85256878772" "85260552717")

echo "🔍 Whitelisting ${#PHONES[@]} contacts..."

# Wait for backend to be ready
echo "⏳ Waiting for backend..."
until curl -s http://localhost:8001/health > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Backend is ready"
echo ""

# Process each phone number
for PHONE in "${PHONES[@]}"; do
    CHAT_ID="${PHONE}@c.us"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📱 Processing ${PHONE}..."

    # Enable whitelist
    echo "🔐 Adding to whitelist..."
    curl -s -X POST "http://localhost:8001/api/whatsapp/chats/${CHAT_ID}/toggle-whitelist?whitelisted=true" \
        -H "Content-Type: application/json" > /dev/null

    # Enable AI
    echo "🤖 Enabling AI..."
    curl -s -X POST "http://localhost:8001/api/whatsapp/chats/${CHAT_ID}/toggle-ai?enabled=true" \
        -H "Content-Type: application/json" > /dev/null

    echo "✅ ${PHONE} configured"
    echo ""
done

# Verify all contacts
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Verification:"
echo ""

curl -s "http://localhost:8001/api/whatsapp/chats" | python3 -c "
import sys, json
chats = json.load(sys.stdin)['chats']
phones = ['85256878772', '85260552717']
found = 0

for phone in phones:
    for chat in chats:
        if phone in chat['id']:
            found += 1
            status = '✅' if chat['is_whitelisted'] and chat['ai_enabled'] else '⚠️'
            print(f\"{status} {chat['name']} ({chat['phone_number']})\")
            print(f\"   Whitelisted: {'✓' if chat['is_whitelisted'] else '✗'}\")
            print(f\"   AI Enabled: {'✓' if chat['ai_enabled'] else '✗'}\")
            print()
            break

if found == 0:
    print('❌ No contacts found. Make sure WhatsApp has messages from these numbers first.')
else:
    print(f'✨ {found} contact(s) configured successfully!')
"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Whitelist configuration complete!"
echo ""
echo "📋 Whitelisted numbers:"
echo "   • 85256878772"
echo "   • 85260552717"
echo ""
echo "💡 These contacts can now:"
echo "   ✓ Use AI auto-responses"
echo "   ✓ Book appointments via chat"
echo "   ✓ Check availability"
