import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sqlalchemy

# Add current directory to Python path for local imports
sys.path.insert(0, str(current_dir))

from routers import whatsapp, appointments, llm, files, conversations
from routers import settings as settings_router
from websocket.manager import ConnectionManager
from services.whatsapp_service import WhatsAppService
from services.llm_service import LLMService
from services.agent_service import initialize_agent_service, get_agent_service
from core.config import settings
from database.database import engine, Base
from tasks.scheduled_tasks import start_scheduled_tasks, stop_scheduled_tasks
from tasks.task_manager import TaskManager

# Global services
whatsapp_service = None
llm_service = None
agent_service = None
task_manager = TaskManager()
connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global whatsapp_service, llm_service, agent_service

    # Create database tables using async method
    from database.database import init_db
    await init_db()

    # Initialize services
    llm_service = LLMService()
    whatsapp_service = WhatsAppService(connection_manager)
    whatsapp_service.set_llm_service(llm_service)

    # Initialize agent service
    agent_service = initialize_agent_service(llm_service)

    # Inject services into routers
    whatsapp.whatsapp_service = whatsapp_service
    llm.llm_service = llm_service

    # Start scheduled tasks
    start_scheduled_tasks()

    # Start agent service task processing in background
    asyncio.create_task(agent_service.start_processing(task_manager))

    print("🚀 WhatsApp Secretary backend started")

    yield

    # Shutdown
    if agent_service:
        agent_service.stop_processing()

    if whatsapp_service:
        await whatsapp_service.cleanup()

    # Stop scheduled tasks
    stop_scheduled_tasks()

    print("🛑 WhatsApp Secretary backend stopped")

app = FastAPI(
    title="WhatsApp Secretary",
    description="AI-powered WhatsApp assistant with appointment booking",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
# Build CORS origins list from environment variable or use defaults
cors_origins_str = os.getenv("CORS_ORIGINS", "")
if cors_origins_str:
    # Parse comma-separated CORS origins from environment
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
else:
    # Default origins for local development
    cors_origins = [
        "http://localhost:3004",
        "http://127.0.0.1:3004",
        "http://localhost:3005",
        "http://127.0.0.1:3005",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8004",
        "http://127.0.0.1:8004",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["whatsapp"])
app.include_router(appointments.router, prefix="/api", tags=["appointments"])
app.include_router(llm.router, prefix="/api", tags=["llm"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(settings_router.router, tags=["settings"])
app.include_router(conversations.router, tags=["conversations"])

# Static files
static_path = current_dir / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def root():
    return {
        "message": "WhatsApp Secretary API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    global whatsapp_service
    from database.database import engine, Base

    # Check database
    db_status = {}
    try:
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        tables = list(Base.metadata.tables.keys())
        db_status = {
            "connected": True,
            "type": "postgresql" if "postgresql" in str(engine.url) else "sqlite",
            "tables_count": len(tables),
            "sample_tables": tables[:5]
        }
    except Exception as e:
        db_status = {
            "connected": False,
            "error": str(e)
        }

    # Check WhatsApp service
    whatsapp_status = None
    if whatsapp_service:
        whatsapp_status = await whatsapp_service.get_status()

    return {
        "status": "healthy",
        "database": db_status,
        "whatsapp": whatsapp_status,
        "services": {
            "whatsapp_service": whatsapp_service is not None,
            "llm_service": llm_service is not None
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages
            await connection_manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )