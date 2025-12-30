# WhatsApp Secretary

An AI-powered WhatsApp assistant with appointment booking, intelligent conversation management, and automated responses.

## Features

- **WhatsApp Web Integration**: Connect to WhatsApp Web using a Node.js client
- **AI-Powered Responses**: Automated intelligent responses using OpenAI/Anthropic LLMs
- **Appointment Management**: Natural language appointment booking and scheduling
- **Real-time Dashboard**: Modern React frontend with real-time updates
- **Message History**: Store and search conversation history
- **File Management**: Handle media files and document attachments
- **WebSocket Support**: Real-time communication between frontend and backend

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM with SQLite/PostgreSQL support
- **WhatsApp Web.js**: Node.js client for WhatsApp Web
- **OpenAI/Anthropic APIs**: LLM integration for intelligent responses
- **WebSockets**: Real-time communication
- **Pydantic**: Data validation and serialization

### Frontend
- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Zustand**: Lightweight state management
- **React Query**: Server state management

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd WhatsAppSecretary_v0
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp ../.env.example .env
   # Edit .env with your configuration
   python app.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

### Docker Setup

1. **Using Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001

## Configuration

### Environment Variables

The `.env` file has been created with the following configuration:

```env
# Database
DATABASE_URL=sqlite:///./whatsapp_secretary.db

# WhatsApp
WHATSAPP_SESSION_PATH=./whatsapp-session
MEDIA_DOWNLOAD_PATH=./downloads

# LLM APIs
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DEFAULT_LLM_PROVIDER=openai

# API Configuration
API_PORT=8001
CORS_ORIGINS=["http://localhost:3000"]
```

## WhatsApp Connection

1. Start the backend server
2. Navigate to the dashboard
3. Click "Connect" in the WhatsApp Connection Status panel
4. Scan the QR code with your WhatsApp mobile app
5. Once connected, you can view and manage conversations

## Project Structure

```
WhatsAppSecretary_v0/
├── backend/
│   ├── app.py                 # Main FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend Docker configuration
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API and WebSocket services
│   │   ├── store/            # Zustand state management
│   │   ├── types/            # TypeScript type definitions
│   │   └── pages/            # React pages
│   ├── package.json          # Node.js dependencies
│   └── Dockerfile           # Frontend Docker configuration
├── WhatsAppSecretary_v2/     # Core WhatsApp service logic
├── docker-compose.yml        # Multi-container orchestration
├── .env                      # Environment configuration
└── README.md                # This file
```

## API Endpoints

### WhatsApp
- `POST /api/whatsapp/connect` - Connect to WhatsApp
- `POST /api/whatsapp/disconnect` - Disconnect from WhatsApp
- `GET /api/whatsapp/status` - Get connection status
- `GET /api/whatsapp/qr` - Get QR code for authentication
- `GET /api/whatsapp/chats` - List all chats
- `GET /api/whatsapp/chats/{chat_id}/messages` - Get chat messages
- `POST /api/whatsapp/send-message` - Send a message

### Appointments
- `POST /api/appointments/` - Create appointment
- `GET /api/appointments/` - List appointments
- `GET /api/appointments/{id}` - Get appointment details
- `PUT /api/appointments/{id}` - Update appointment
- `DELETE /api/appointments/{id}` - Cancel appointment

### LLM
- `GET /api/llm/status` - Get LLM service status
- `POST /api/llm/generate` - Generate AI response
- `POST /api/llm/clear-cache` - Clear conversation cache

### Files
- `GET /api/files/downloads` - List downloaded files
- `DELETE /api/files/downloads/{filename}` - Delete file
- `GET /api/files/stats` - Get storage statistics

## Usage Instructions

### 1. Setting up WhatsApp Integration

1. **Start the backend**: `python backend/app.py`
2. **Access the dashboard**: Open http://localhost:3000 in your browser
3. **Connect WhatsApp**: Click the "Connect" button in the Connection Status panel
4. **Scan QR Code**: Use your WhatsApp mobile app to scan the displayed QR code
5. **Wait for Connection**: The status will update to "Connected" when successful

### 2. Managing Conversations

- **View Chats**: All your WhatsApp conversations will appear in the chat list
- **Select Chat**: Click on any chat to view its message history
- **Send Messages**: Use the chat window to send replies
- **Media Support**: The system handles images, documents, and other media files

### 3. AI Assistant Features

- **Automatic Responses**: The AI will analyze incoming messages and suggest responses
- **Appointment Booking**: Natural language appointment requests are automatically processed
- **Context Awareness**: The AI maintains conversation context for better responses

### 4. Appointment Management

- **View Appointments**: Check the appointments tab for scheduled meetings
- **Create Appointments**: Book new appointments through natural language
- **Manage Schedule**: Update or cancel existing appointments
- **Availability**: System respects business hours and working days

## Technical Details

### Core Components Used from WhatsAppSecretary_v2

The refined solution leverages the following core components from WhatsAppSecretary_v2:

1. **WhatsApp Service** (`backend/app/services/whatsapp_service.py:17-577`):
   - Node.js subprocess management for WhatsApp Web client
   - QR code generation and authentication handling
   - Message processing and callback handling
   - Session management and reconnection logic

2. **API Routers** (`backend/app/routers/whatsapp.py:1-169`):
   - RESTful endpoints for WhatsApp operations
   - Connection, disconnection, and status management
   - Chat and message retrieval
   - Message sending functionality

3. **Frontend Services** (`frontend/src/services/api.ts:1-71`, `frontend/src/services/websocket.ts:1-149`):
   - Axios-based API client with error handling
   - WebSocket service for real-time communication
   - TypeScript interfaces for type safety

4. **Database Models**: Complete SQLAlchemy models for chat, message, and appointment data

5. **LLM Integration**: OpenAI and Anthropic API integration for intelligent responses

### Key Refinements Made

1. **Unified Architecture**: Integrated WhatsAppSecretary_v2 components into a single cohesive application
2. **Modern Frontend**: Rebuilt the UI using React 18, TypeScript, and Tailwind CSS with modern design patterns
3. **Enhanced Backend**: Updated FastAPI application with improved error handling and modern Python practices
4. **Docker Support**: Added comprehensive Docker and docker-compose configuration
5. **Development Tools**: Configured Vite, ESLint, TypeScript, and other modern development tools
6. **State Management**: Implemented Zustand for efficient client-side state management
7. **UI Components**: Used Radix UI primitives for accessible, customizable components

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs` when running the server
- Review the configuration files for setup details