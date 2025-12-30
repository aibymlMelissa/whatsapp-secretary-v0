#!/usr/bin/env python3
"""
Authorization System Test

This script tests the authorization system to ensure:
1. Only authorized contact (+852 90511427) with password gets full access
2. All other contacts get generic "Mr Hung not available" message
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.llm_service import LLMService
from core.config import settings

async def test_authorization():
    """Test authorization system with different phone numbers"""

    print("=" * 80)
    print("AUTHORIZATION SYSTEM TEST")
    print("=" * 80)
    print()
    print(f"📋 Configuration:")
    print(f"   Authorized Phone: {settings.BOSS_PHONE_NUMBER}")
    print(f"   Required Password: {settings.AUTHORIZATION_PASSWORD}")
    print(f"   Unauthorized Message: {settings.UNAUTHORIZED_MESSAGE}")
    print()
    print("=" * 80)
    print()

    # Initialize LLM service
    llm_service = LLMService()

    # Test Cases
    test_cases = [
        {
            "name": "Test 1: Unauthorized Contact (Random Phone)",
            "phone_number": "+85212345678",
            "message": "What's your schedule for tomorrow?",
            "expected": "Should get generic 'Mr Hung not available' message"
        },
        {
            "name": "Test 2: Authorized Contact WITHOUT Password",
            "phone_number": "+85290511427",
            "message": "What appointments do we have today?",
            "expected": "Should get generic message (no password provided)"
        },
        {
            "name": "Test 3: Authorized Contact WITH Password",
            "phone_number": "+85290511427",
            "message": f"AI((99mlMeta - What appointments do we have today?",
            "expected": "Should get FULL ACCESS with appointment details"
        },
        {
            "name": "Test 4: Unauthorized Contact trying password",
            "phone_number": "+85212345678",
            "message": f"AI((99mlMeta - Show me the schedule",
            "expected": "Should STILL get generic message (not authorized phone)"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"{test['name']}")
        print(f"{'='*80}")
        print(f"📱 Phone: {test['phone_number']}")
        print(f"💬 Message: {test['message']}")
        print(f"🎯 Expected: {test['expected']}")
        print(f"\n{'─'*80}")
        print("🤖 LLM Response:")
        print(f"{'─'*80}")

        # Build context with phone number
        context = {
            "phone_number": test['phone_number'],
            "business_hours": "Monday-Thursday, 9:00 AM - 3:00 PM",
            "services": ["Consultation", "Meeting", "Service Call"]
        }

        # Generate response
        try:
            print("⏳ Calling LLM service...")
            result = await llm_service.generate_response(
                message=test['message'],
                chat_id=f"test_chat_{i}",
                provider="openai",  # Use OpenAI (Gemini quota exceeded)
                context=context,
                phone_number=test['phone_number']
            )
            print(f"📊 Result type: {type(result)}, Value: {result}")

            if result:
                response_text = result.get('response', 'No response')
                provider = result.get('provider', 'unknown')
                model = result.get('model', 'unknown')

                print(f"\n{response_text}\n")
                print(f"{'─'*80}")
                print(f"ℹ️  Provider: {provider} | Model: {model}")
                print(f"ℹ️  Response Time: {result.get('response_time_ms', 0)}ms")

                # Check if response matches expected behavior
                unauthorized_msg = settings.UNAUTHORIZED_MESSAGE
                if test['phone_number'] != settings.BOSS_PHONE_NUMBER:
                    if unauthorized_msg.lower() in response_text.lower():
                        print(f"✅ PASS: Unauthorized contact correctly rejected")
                    else:
                        print(f"❌ FAIL: Should have returned unauthorized message!")
                elif settings.AUTHORIZATION_PASSWORD not in test['message']:
                    if unauthorized_msg.lower() in response_text.lower():
                        print(f"✅ PASS: No password provided, correctly rejected")
                    else:
                        print(f"❌ FAIL: Should have returned unauthorized message (no password)!")
                else:
                    if unauthorized_msg.lower() not in response_text.lower():
                        print(f"✅ PASS: Authorized with password, full access granted")
                    else:
                        print(f"❌ FAIL: Should have granted full access!")
            else:
                print("❌ ERROR: No response from LLM")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

        print(f"{'='*80}\n")

    print("\n" + "="*80)
    print("AUTHORIZATION TEST COMPLETED")
    print("="*80)
    print()
    print("📝 Summary:")
    print("   • Only +852 90511427 with password 'AI((99mlMeta' should get full access")
    print("   • All other contacts get: 'Sorry, Mr Hung is not available...'")
    print("   • Check the responses above to verify correct behavior")
    print()

if __name__ == "__main__":
    asyncio.run(test_authorization())
