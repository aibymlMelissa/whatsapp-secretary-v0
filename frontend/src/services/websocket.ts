import { WebSocketMessage } from '@/types';

class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Function[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10; // Increased from 5
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  connect(url?: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    // Dynamically determine WebSocket URL if not provided
    if (!url) {
      if (import.meta.env.VITE_WS_URL) {
        url = `${import.meta.env.VITE_WS_URL}/ws`;
      } else if (window.location.hostname.includes('ngrok-free.app')) {
        // Use wss for ngrok https URLs
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        url = `${protocol}//${window.location.host}/ws`;
      } else {
        // Default for local development
        url = `ws://${window.location.host}/ws`;
      }
    }

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.reconnectAttempts = 0;
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
        this.startHeartbeat();
        this.emit('connection', { connected: true });
      };

      this.ws.onclose = (event) => {
        console.log('❌ WebSocket disconnected:', event.code, event.reason);
        this.emit('connection', { connected: false, code: event.code, reason: event.reason });

        if (event.code !== 1000) {
          this.attemptReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('connection_error', { error });
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.emit(message.type || 'message', message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.emit('connection_error', { error });
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    if (this.reconnectTimer) {
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.listeners.clear();
    this.reconnectAttempts = 0;
  }

  private startHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    // Send ping every 30 seconds to keep connection alive
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send('ping');
      }
    }, 30000);
  }

  send(type: string, data?: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = { type, data, timestamp: Date.now() };
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', { type, data });
    }
  }

  on(eventType: string, callback: Function) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)!.push(callback);
  }

  off(eventType: string, callback?: Function) {
    if (!callback) {
      this.listeners.delete(eventType);
      return;
    }

    const callbacks = this.listeners.get(eventType);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(eventType: string, data: any) {
    const callbacks = this.listeners.get(eventType);
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket event callback for ${eventType}:`, error);
        }
      });
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const websocketService = new WebSocketService();
export default WebSocketService;