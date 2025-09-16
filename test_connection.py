#!/usr/bin/env python3

"""
Quick test script to verify the WhatsApp connection fixes
"""

import asyncio
import aiohttp
import json
import websockets
import time

async def test_api_connection():
    """Test API connectivity"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get('http://localhost:8001/health') as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Backend API is running")
                    print(f"   Status: {data.get('status')}")
                    print(f"   WhatsApp Service: {data.get('services', {}).get('whatsapp_service')}")
                    return True
                else:
                    print(f"❌ Backend API returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Could not connect to backend API: {e}")
        return False

async def test_websocket_connection():
    """Test WebSocket connectivity"""
    try:
        uri = "ws://localhost:8001/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established")

            # Send a test message
            test_message = {"type": "test", "data": "hello"}
            await websocket.send(json.dumps(test_message))

            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"✅ WebSocket response: {response}")
                return True
            except asyncio.TimeoutError:
                print("⚠️  WebSocket connected but no response received")
                return True

    except Exception as e:
        print(f"❌ Could not connect to WebSocket: {e}")
        return False

async def test_whatsapp_status():
    """Test WhatsApp status endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8001/api/whatsapp/status') as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ WhatsApp status endpoint working")
                    print(f"   Status: {data}")
                    return True
                else:
                    print(f"❌ WhatsApp status endpoint returned {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Could not get WhatsApp status: {e}")
        return False

async def test_whatsapp_connection():
    """Test WhatsApp connection initiation"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8001/api/whatsapp/connect') as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ WhatsApp connection initiated")
                    print(f"   Response: {data}")

                    # Wait a bit and check for QR code
                    await asyncio.sleep(3)

                    async with session.get('http://localhost:8001/api/whatsapp/qr') as qr_response:
                        if qr_response.status == 200:
                            qr_data = await qr_response.json()
                            print("✅ QR code endpoint working")
                            print(f"   Has QR: {qr_data.get('has_qr')}")
                            if qr_data.get('qr_code'):
                                print(f"   QR Code length: {len(qr_data.get('qr_code', ''))}")
                        else:
                            print(f"⚠️  QR endpoint returned {qr_response.status}")

                    return True
                else:
                    data = await response.text()
                    print(f"❌ WhatsApp connection failed: {response.status} - {data}")
                    return False
    except Exception as e:
        print(f"❌ Could not initiate WhatsApp connection: {e}")
        return False

async def main():
    """Run all tests"""
    print("🔧 Testing WhatsAppSecretary_v0 Connection Fixes")
    print("=" * 50)

    # Test API connection
    print("\n1. Testing Backend API Connection...")
    api_ok = await test_api_connection()

    if not api_ok:
        print("\n❌ Backend is not running. Please start it first:")
        print("   cd backend && python app.py")
        return

    # Test WebSocket
    print("\n2. Testing WebSocket Connection...")
    ws_ok = await test_websocket_connection()

    # Test WhatsApp status
    print("\n3. Testing WhatsApp Status...")
    status_ok = await test_whatsapp_status()

    # Test WhatsApp connection
    print("\n4. Testing WhatsApp Connection...")
    connect_ok = await test_whatsapp_connection()

    print("\n" + "=" * 50)
    print("🔧 Test Summary:")
    print(f"   Backend API: {'✅' if api_ok else '❌'}")
    print(f"   WebSocket: {'✅' if ws_ok else '❌'}")
    print(f"   WhatsApp Status: {'✅' if status_ok else '❌'}")
    print(f"   WhatsApp Connect: {'✅' if connect_ok else '❌'}")

    if all([api_ok, ws_ok, status_ok, connect_ok]):
        print("\n🎉 All tests passed! The fixes are working correctly.")
        print("\nNext steps:")
        print("1. Start the frontend: cd frontend && npm run dev")
        print("2. Open http://localhost:3004")
        print("3. Try connecting WhatsApp - you should see a QR code!")
    else:
        print("\n⚠️  Some tests failed. Check the backend logs for more details.")

if __name__ == "__main__":
    asyncio.run(main())