#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
import subprocess

app = FastAPI(title="WhatsApp Test API")

# File paths for communication with Node.js
QR_FILE = "/Users/aibyml.com/WhatsAppSecretary_v0/backend/whatsapp_client/qr_code.txt"
STATUS_FILE = "/Users/aibyml.com/WhatsAppSecretary_v0/backend/whatsapp_client/status.json"
BRIDGE_SCRIPT = "/Users/aibyml.com/WhatsAppSecretary_v0/backend/whatsapp_client/simple_bridge.js"

whatsapp_process = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005", "http://localhost:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def read_status():
    """Read status from Node.js bridge"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        "connected": False,
        "connecting": False,
        "qr_code": None,
        "ready": False
    }

def read_qr_code():
    """Read QR code from Node.js bridge"""
    try:
        if os.path.exists(QR_FILE):
            with open(QR_FILE, 'r') as f:
                qr_code = f.read().strip()
                if qr_code:
                    return qr_code
    except:
        pass
    return None

@app.get("/api/whatsapp/status")
async def get_status():
    node_status = read_status()
    return {
        "success": True,
        "status": {
            "connected": node_status.get("connected", False),
            "connecting": node_status.get("connecting", False),
            "process_running": whatsapp_process is not None and whatsapp_process.poll() is None,
            "has_qr_code": node_status.get("qr_code") is not None,
            "session_exists": True
        }
    }

@app.post("/api/whatsapp/connect")
async def connect():
    global whatsapp_process

    # Start Node.js bridge if not running
    if whatsapp_process is None or whatsapp_process.poll() is not None:
        try:
            whatsapp_process = subprocess.Popen(
                ['node', BRIDGE_SCRIPT],
                cwd="/Users/aibyml.com/WhatsAppSecretary_v0/backend/whatsapp_client"
            )
            return {"success": True, "message": "WhatsApp connection initiated"}
        except Exception as e:
            return {"success": False, "message": f"Failed to start WhatsApp: {str(e)}"}

    return {"success": True, "message": "WhatsApp already connecting"}

@app.get("/api/whatsapp/qr")
async def get_qr():
    # Try to read real QR code from Node.js bridge
    qr_code = read_qr_code()

    if not qr_code:
        # Fallback to sample QR code
        qr_code = "2@9jqNfHeCGgQI2Z4AfrOd2+IfBZZTYqV5l5Gw=="

    return {
        "success": True,
        "qr_code": qr_code,
        "has_qr": qr_code is not None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)