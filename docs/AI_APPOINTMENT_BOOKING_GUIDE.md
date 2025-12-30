# AI Appointment Booking System - User Guide

## Overview
The WhatsApp Secretary now has **AI-powered appointment booking** capabilities! Users can book appointments naturally through WhatsApp messages, and the AI will understand and process their requests automatically.

## How It Works

### 1. **Natural Language Understanding**
The AI recognizes appointment-related keywords in messages:
- "appointment", "book", "schedule", "reserve", "meeting"
- "available", "time", "date", "calendar"

### 2. **Intent Detection**
The AI can understand different intents:
- **Book Appointment**: "I need an appointment tomorrow at 2pm"
- **Check Availability**: "What times are available on Friday?"
- **Reschedule**: "Can I move my appointment to next week?"
- **Cancel**: "I need to cancel my appointment"

### 3. **Information Extraction**
The AI automatically extracts:
- Customer name (from WhatsApp contact or message)
- Phone number (from WhatsApp)
- Service type (Consultation, Meeting, Service Call, etc.)
- Preferred date and time
- Additional notes

## Example Conversations

### Booking an Appointment
```
User: "Hi, I'd like to book a consultation for tomorrow at 10am"

WhatsApp Secretary:
✅ **Appointment Confirmed!**

📋 Service: Consultation
📅 Date: 2025-10-05
⏰ Time: 10:00
⏱️ Duration: 60 minutes
👤 Customer: John Doe
🔖 Confirmation: apt_1759550747_8901

You'll receive reminders:
• 24 hours before
• 1 hour before

Thank you for booking with us! 🙏
```

### Checking Availability
```
User: "What time slots are available tomorrow?"

WhatsApp Secretary:
📅 Available time slots for 2025-10-05:

⏰ 09:00
⏰ 11:00
⏰ 12:00
⏰ 13:00
⏰ 14:00
⏰ 15:00
⏰ 16:00

Please let me know which time works best for you!
```

### Time Slot Conflict
```
User: "Book me for 10am tomorrow"

WhatsApp Secretary:
⚠️ The requested time slot is not available. Please choose a different time.

Would you like me to show you available time slots for that day?
```

## Technical Details

### Business Hours
- **Default**: 9:00 AM - 5:00 PM
- Configurable per business needs

### Appointment Duration
- **Default**: 60 minutes
- Customizable per service type

### Available Services
- Consultation
- Meeting
- Service Call
- Checkup
- General (default)

### Confidence Threshold
- AI requires **70% confidence** to auto-book
- Lower confidence messages receive general AI responses

## API Endpoints

### Create Appointment (AI Tool)
```python
await tools.create_appointment(
    chat_id="chat_id",
    customer_name="John Doe",
    customer_phone="+1234567890",
    service_type="Consultation",
    appointment_date="2025-10-05",
    appointment_time="10:00",
    duration_minutes=60,
    notes="Optional notes"
)
```

### Check Availability (AI Tool)
```python
await tools.check_availability(
    date="2025-10-05",
    duration_minutes=60
)
```

### Manual Appointment Creation (REST API)
```bash
curl -X POST http://localhost:8001/api/appointments/ \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "chat_id",
    "customer_name": "John Doe",
    "customer_phone": "+1234567890",
    "title": "Consultation",
    "service_type": "Consultation",
    "appointment_date": "2025-10-05T10:00:00",
    "duration_minutes": 60
  }'
```

## Features

### ✅ Implemented
- [x] Natural language appointment parsing
- [x] Intent detection (book, check availability)
- [x] Date/time extraction
- [x] Service type recognition
- [x] Conflict detection
- [x] Automatic appointment creation
- [x] Rich confirmation messages
- [x] Available slot suggestions
- [x] Database persistence

### 🔄 Upcoming Features
- [ ] Appointment rescheduling via chat
- [ ] Appointment cancellation via chat
- [ ] 24-hour and 1-hour automated reminders
- [ ] Multiple time zone support
- [ ] Service-specific pricing
- [ ] Calendar integration (Google Calendar, Outlook)

## Database Schema

Appointments are stored with:
- Unique ID and external reference ID
- Customer information (name, phone, email)
- Service type and title
- Date, time, and duration
- Status (scheduled, confirmed, cancelled, completed)
- Notes and pricing
- Reminder tracking

## Testing

### Test Appointment Creation
```python
from services.llm_tools import SecureLLMTools
from services.authorization_service import AuthorizationService

tools = SecureLLMTools(AuthorizationService())
result = await tools.create_appointment(...)
```

### Check Current Appointments
```bash
curl http://localhost:8001/api/
```

### View Statistics
```bash
curl http://localhost:8001/api/whatsapp/stats
```

## Troubleshooting

### No appointments being created?
1. Check if AI is enabled for the chat
2. Verify confidence threshold (>70%)
3. Check backend logs for errors
4. Ensure appointment keywords are in message

### Conflicts not detected?
1. Verify appointment datetime format
2. Check database for existing appointments
3. Review conflict detection logic

### AI not understanding requests?
1. Use clear, direct language
2. Include specific dates and times
3. Mention service type explicitly
4. Check LLM service status

## Configuration

Edit `backend/core/config.py`:
```python
# Business hours
BUSINESS_START_HOUR = 9
BUSINESS_END_HOUR = 17

# Default appointment duration
DEFAULT_APPOINTMENT_DURATION = 60

# LLM confidence threshold
APPOINTMENT_CONFIDENCE_THRESHOLD = 0.7
```

---

**Generated**: October 4, 2025
**Version**: 2.0.0
