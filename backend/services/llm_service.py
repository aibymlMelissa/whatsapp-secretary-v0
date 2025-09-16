# backend/app/services/llm_service.py
import asyncio
import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from core.config import settings
from database.models import LLMProvider, ConversationHistory
from database.database import get_db
from services.user_service import UserService

class LLMService:
    """
    Unified LLM service supporting both Ollama (Llama 4) and Google Gemini
    """
    
    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL
        
        self.conversation_cache: Dict[str, List[Dict]] = {}
        self.max_context_length = 20
        self.context_timeout = 1800  # 30 minutes
        
        # Initialize Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_client = genai.GenerativeModel(self.gemini_model)
        else:
            self.gemini_client = None
    
    async def initialize(self):
        """Initialize LLM service"""
        print("🤖 Initializing LLM Service...")
        
        # Test Ollama connection
        if await self.test_ollama_connection():
            print(f"✅ Ollama connected: {self.ollama_model}")
        else:
            print("❌ Ollama connection failed")
        
        # Test Gemini connection
        if await self.test_gemini_connection():
            print(f"✅ Gemini connected: {self.gemini_model}")
        else:
            print("❌ Gemini connection failed")
    
    async def test_ollama_connection(self) -> bool:
        """Test connection to Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return any(model.get("name", "").startswith(self.ollama_model) for model in models)
            return False
        except Exception as e:
            print(f"Ollama connection test failed: {e}")
            return False
    
    async def test_gemini_connection(self) -> bool:
        """Test connection to Google Gemini"""
        try:
            if not self.gemini_client:
                return False
            
            # Simple test prompt
            response = await self.generate_gemini_response("Hello", "test_chat")
            return response is not None
        except Exception as e:
            print(f"Gemini connection test failed: {e}")
            return False
    
    def get_user_config(self, phone_number: str) -> Optional[Dict]:
        """Get user-specific LLM configuration"""
        try:
            db = next(get_db())
            return UserService.get_user_llm_config(phone_number, db)
        except Exception as e:
            print(f"Error getting user config: {e}")
            return None

    async def generate_response(
        self,
        message: str,
        chat_id: str,
        provider: str = "auto",
        context: Optional[Dict] = None,
        phone_number: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate response using specified LLM provider with user-specific configuration
        """
        start_time = time.time()

        try:
            # Get user-specific configuration
            user_config = None
            if phone_number:
                user_config = self.get_user_config(phone_number)

            # Use user config if available, otherwise use system defaults
            if user_config:
                provider = user_config.get('preferred_provider', provider)
                max_tokens = user_config.get('max_tokens', 500)
                temperature = user_config.get('temperature', 0.7)
            else:
                max_tokens = 500
                temperature = 0.7

            # Auto-select provider if not specified
            if provider == "auto":
                provider = await self.select_best_provider(message)

            # Generate response based on provider
            if provider == "ollama":
                response = await self.generate_ollama_response(
                    message, chat_id, context, user_config, max_tokens, temperature
                )
                actual_provider = LLMProvider.OLLAMA
                model_name = user_config.get('ollama_model', self.ollama_model) if user_config else self.ollama_model
            elif provider == "gemini":
                response = await self.generate_gemini_response(
                    message, chat_id, context, user_config, max_tokens, temperature
                )
                actual_provider = LLMProvider.GEMINI
                model_name = user_config.get('gemini_model', self.gemini_model) if user_config else self.gemini_model
            elif provider == "openai":
                response = await self.generate_openai_response(
                    message, chat_id, context, user_config, max_tokens, temperature
                )
                actual_provider = LLMProvider.OPENAI
                model_name = user_config.get('openai_model', 'gpt-4o-mini') if user_config else 'gpt-4o-mini'
            elif provider == "anthropic":
                response = await self.generate_anthropic_response(
                    message, chat_id, context, user_config, max_tokens, temperature
                )
                actual_provider = LLMProvider.ANTHROPIC
                model_name = user_config.get('anthropic_model', 'claude-3-haiku-20240307') if user_config else 'claude-3-haiku-20240307'
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            if not response:
                return None

            response_time = int((time.time() - start_time) * 1000)

            # Save to conversation history
            await self.save_conversation_history(
                chat_id=chat_id,
                user_input=message,
                llm_response=response,
                provider=actual_provider,
                response_time_ms=response_time
            )

            return {
                "response": response,
                "provider": provider,
                "model": model_name,
                "response_time_ms": response_time,
                "used_user_config": user_config is not None
            }

        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return None
    
    async def generate_ollama_response(
        self,
        message: str,
        chat_id: str,
        context: Optional[Dict] = None,
        user_config: Optional[Dict] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Generate response using Ollama (Llama 4)"""
        try:
            # Prepare conversation context
            conversation_history = self.get_conversation_context(chat_id)
            
            # Build prompt with context
            system_prompt = self.get_system_prompt(context)

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": message})

            # Use user-specific settings
            ollama_url = user_config.get('ollama_base_url', self.ollama_base_url) if user_config else self.ollama_base_url
            ollama_model = user_config.get('ollama_model', self.ollama_model) if user_config else self.ollama_model

            # Ollama API call
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "top_p": 0.9
                    }
                }
                
                response = await client.post(
                    f"{ollama_url}/api/chat",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("message", {}).get("content", "").strip()
                    
                    if ai_response:
                        self.update_conversation_context(chat_id, message, ai_response)
                        return ai_response
                
                return None
                
        except Exception as e:
            print(f"Ollama API error: {e}")
            return None
    
    async def generate_gemini_response(
        self,
        message: str,
        chat_id: str,
        context: Optional[Dict] = None,
        user_config: Optional[Dict] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Generate response using Google Gemini"""
        try:
            if not self.gemini_client:
                return None
            
            # Prepare conversation context
            conversation_history = self.get_conversation_context(chat_id)
            
            # Build chat history for Gemini
            chat_history = []
            for msg in conversation_history:
                if msg["role"] == "user":
                    chat_history.append({"role": "user", "parts": [msg["content"]]})
                elif msg["role"] == "assistant":
                    chat_history.append({"role": "model", "parts": [msg["content"]]})
            
            # Create chat session
            chat = self.gemini_client.start_chat(history=chat_history)
            
            # Add system context to the message
            system_prompt = self.get_system_prompt(context)
            enhanced_message = f"System Context: {system_prompt}\n\nUser Message: {message}"
            
            # Configure safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            # Generate response
            response = await asyncio.to_thread(
                chat.send_message,
                enhanced_message,
                safety_settings=safety_settings
            )
            
            ai_response = response.text.strip()
            
            if ai_response:
                self.update_conversation_context(chat_id, message, ai_response)
                return ai_response
            
            return None
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None

    async def generate_openai_response(
        self,
        message: str,
        chat_id: str,
        context: Optional[Dict] = None,
        user_config: Optional[Dict] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Generate response using OpenAI GPT"""
        try:
            if not user_config or not user_config.get('openai_api_key'):
                return None

            # Prepare conversation context
            conversation_history = self.get_conversation_context(chat_id)

            # Build messages
            system_prompt = self.get_system_prompt(context)
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": message})

            # OpenAI API call
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {user_config['openai_api_key']}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": user_config.get('openai_model', 'gpt-4o-mini'),
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }

                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    ai_response = data["choices"][0]["message"]["content"].strip()

                    if ai_response:
                        self.update_conversation_context(chat_id, message, ai_response)
                        return ai_response

                return None

        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None

    async def generate_anthropic_response(
        self,
        message: str,
        chat_id: str,
        context: Optional[Dict] = None,
        user_config: Optional[Dict] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Generate response using Anthropic Claude"""
        try:
            if not user_config or not user_config.get('anthropic_api_key'):
                return None

            # Prepare conversation context
            conversation_history = self.get_conversation_context(chat_id)

            # Build messages for Anthropic format
            messages = []
            for msg in conversation_history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append(msg)
            messages.append({"role": "user", "content": message})

            # Anthropic API call
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {user_config['anthropic_api_key']}",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }

                # Add system prompt to the first user message
                system_prompt = self.get_system_prompt(context)
                if messages and messages[0]["role"] == "user":
                    messages[0]["content"] = f"System: {system_prompt}\n\nUser: {messages[0]['content']}"
                else:
                    messages.insert(0, {"role": "user", "content": f"System: {system_prompt}\n\nUser: {message}"})

                payload = {
                    "model": user_config.get('anthropic_model', 'claude-3-haiku-20240307'),
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }

                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    ai_response = data["content"][0]["text"].strip()

                    if ai_response:
                        self.update_conversation_context(chat_id, message, ai_response)
                        return ai_response

                return None

        except Exception as e:
            print(f"Anthropic API error: {e}")
            return None

    async def select_best_provider(self, message: str) -> str:
        """Auto-select the best provider based on message content"""
        message_lower = message.lower()
        
        # Use Gemini for complex queries, appointments, and analysis
        gemini_keywords = [
            "appointment", "schedule", "book", "calendar", "remind",
            "analyze", "summarize", "explain", "compare", "review",
            "plan", "strategy", "recommendation"
        ]
        
        # Use Ollama for general conversation and simple queries
        ollama_keywords = [
            "hello", "hi", "thanks", "help", "how", "what", "when",
            "simple", "quick", "status", "confirm", "cancel"
        ]
        
        if any(keyword in message_lower for keyword in gemini_keywords):
            return "gemini" if self.gemini_client else "ollama"
        elif any(keyword in message_lower for keyword in ollama_keywords):
            return "ollama"
        else:
            # Default to Gemini for complex queries, Ollama for simple ones
            return "gemini" if len(message.split()) > 10 and self.gemini_client else "ollama"
    
    def get_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Get system prompt with context"""
        base_prompt = """You are an intelligent WhatsApp business assistant specializing in appointment management and customer service.

CORE CAPABILITIES:
- Schedule, modify, and cancel appointments
- Check availability and suggest time slots
- Send reminders and confirmations
- Handle customer inquiries professionally
- Process natural language booking requests

APPOINTMENT SYSTEM:
- Business hours: 9:00 AM - 5:00 PM (configurable)
- Default appointment duration: 1 hour
- Services: Consultation, Meeting, Service Call, etc.
- Automatic conflict detection and resolution

COMMUNICATION STYLE:
- Be friendly, professional, and helpful
- Confirm all booking details clearly
- Offer alternatives when requested times aren't available
- Use emojis appropriately (📅 for dates, ⏰ for times, ✅ for confirmations)
- Keep responses concise but informative

IMPORTANT: Always try to be helpful and provide actionable next steps."""

        if context:
            if context.get("business_hours"):
                base_prompt += f"\n\nCurrent business hours: {context['business_hours']}"
            if context.get("services"):
                base_prompt += f"\nAvailable services: {', '.join(context['services'])}"
            if context.get("customer_name"):
                base_prompt += f"\nCustomer name: {context['customer_name']}"
        
        return base_prompt
    
    def get_conversation_context(self, chat_id: str) -> List[Dict]:
        """Get conversation context for a chat"""
        if chat_id not in self.conversation_cache:
            return []
        
        context = self.conversation_cache[chat_id]
        
        # Remove expired context
        current_time = time.time()
        context = [msg for msg in context if (current_time - msg.get("timestamp", 0)) < self.context_timeout]
        
        # Keep only recent messages
        context = context[-self.max_context_length:]
        
        self.conversation_cache[chat_id] = context
        return [{"role": msg["role"], "content": msg["content"]} for msg in context]
    
    def update_conversation_context(self, chat_id: str, user_message: str, ai_response: str):
        """Update conversation context"""
        if chat_id not in self.conversation_cache:
            self.conversation_cache[chat_id] = []
        
        current_time = time.time()
        
        # Add user message
        self.conversation_cache[chat_id].append({
            "role": "user",
            "content": user_message,
            "timestamp": current_time
        })
        
        # Add AI response
        self.conversation_cache[chat_id].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": current_time
        })
        
        # Trim if too long
        if len(self.conversation_cache[chat_id]) > self.max_context_length:
            self.conversation_cache[chat_id] = self.conversation_cache[chat_id][-self.max_context_length:]
    
    async def save_conversation_history(
        self,
        chat_id: str,
        user_input: str,
        llm_response: str,
        provider: LLMProvider,
        response_time_ms: int
    ):
        """Save conversation to database"""
        try:
            db = next(get_db())
            
            history_record = ConversationHistory(
                chat_id=chat_id,
                user_input=user_input,
                llm_response=llm_response,
                provider=provider,
                model_name=self.ollama_model if provider == LLMProvider.OLLAMA else self.gemini_model,
                response_time_ms=response_time_ms
            )
            
            db.add(history_record)
            db.commit()
            
        except Exception as e:
            print(f"Error saving conversation history: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get LLM service status"""
        ollama_status = await self.test_ollama_connection()
        gemini_status = await self.test_gemini_connection()
        
        return {
            "ollama": {
                "available": ollama_status,
                "model": self.ollama_model,
                "base_url": self.ollama_base_url
            },
            "gemini": {
                "available": gemini_status,
                "model": self.gemini_model,
                "api_key_configured": bool(self.gemini_api_key)
            },
            "active_conversations": len(self.conversation_cache),
            "cache_size": sum(len(msgs) for msgs in self.conversation_cache.values())
        }
    
    async def clear_conversation_cache(self, chat_id: Optional[str] = None):
        """Clear conversation cache"""
        if chat_id:
            self.conversation_cache.pop(chat_id, None)
        else:
            self.conversation_cache.clear()
    
    async def process_appointment_request(self, message: str, chat_id: str) -> Optional[Dict]:
        """Process natural language appointment requests"""
        context = {
            "business_hours": "9:00 AM - 5:00 PM",
            "services": ["Consultation", "Meeting", "Service Call", "Checkup"]
        }
        
        enhanced_prompt = f"""
        Process this appointment request and extract structured information:
        
        Message: "{message}"
        
        Please respond with a JSON object containing:
        {{
            "intent": "book_appointment|check_availability|reschedule|cancel",
            "service": "extracted service type or 'General'",
            "preferred_date": "YYYY-MM-DD or null",
            "preferred_time": "HH:MM or null",
            "customer_name": "extracted name or null",
            "customer_phone": "extracted phone or null",
            "notes": "any additional information",
            "confidence": 0.0-1.0
        }}
        
        Only return the JSON object, no other text.
        """
        
        response = await self.generate_response(enhanced_prompt, chat_id, "gemini", context)
        
        if response and response.get("response"):
            try:
                # Try to parse JSON from response
                json_str = response["response"].strip()
                if json_str.startswith("```json"):
                    json_str = json_str.replace("```json", "").replace("```", "").strip()
                
                appointment_data = json.loads(json_str)
                return appointment_data
            except json.JSONDecodeError:
                print("Failed to parse appointment JSON from LLM response")
        
        return None
    
    async def generate_appointment_confirmation(self, appointment_data: Dict) -> str:
        """Generate appointment confirmation message"""
        prompt = f"""
        Generate a professional appointment confirmation message for:
        
        Service: {appointment_data.get('service', 'General')}
        Date: {appointment_data.get('date')}
        Time: {appointment_data.get('time')}
        Customer: {appointment_data.get('customer_name', 'Valued Customer')}
        
        Include:
        - Confirmation with appointment details
        - Appointment ID reference
        - Reminder about 24h and 1h notifications
        - Professional but friendly tone
        - Relevant emojis
        """
        
        response = await self.generate_response(prompt, "system", "gemini")
        return response.get("response", "Appointment confirmed!") if response else "Appointment confirmed!"
    
    async def cleanup(self):
        """Cleanup LLM service"""
        self.conversation_cache.clear()
        print("🤖 LLM Service cleaned up")