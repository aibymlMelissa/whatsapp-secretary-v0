export interface Chat {
  id: string;
  name: string;
  phone_number?: string;
  is_group: boolean;
  ai_enabled: boolean;
  is_whitelisted: boolean;
  unread_count?: number;
  last_message?: {
    body: string;
    timestamp: string;
    from_me: boolean;
  } | null;
  updated_at: string;
}

export interface Message {
  id: string;
  chat_id: string;
  body: string;
  message_type: string;
  from_me: boolean;
  timestamp: string;
  has_media: boolean;
  media_path?: string;
  llm_processed: boolean;
  llm_response?: string;
}

export interface Appointment {
  id: number;
  chat_id: string;
  client_name: string;
  client_phone: string;
  appointment_datetime: string;
  duration_minutes: number;
  service_type: string;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface WhatsAppStatus {
  connected: boolean;
  connecting: boolean;
  process_running: boolean;
  has_qr_code: boolean;
  session_exists: boolean;
}

export interface LLMStatus {
  available_providers: string[];
  current_provider: string;
  models: {
    [provider: string]: string[];
  };
  cache_size: number;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}