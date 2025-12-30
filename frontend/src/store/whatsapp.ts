import { create } from 'zustand';
import { Chat, Message, WhatsAppStatus } from '@/types';
import { whatsappApi } from '@/services/api';
import { websocketService } from '@/services/websocket';

interface WhatsAppStore {
  status: WhatsAppStatus | null;
  qrCode: string | null;
  chats: Chat[];
  currentChat: Chat | null;
  messages: { [chatId: string]: Message[] };
  loading: boolean;
  error: string | null;

  // Actions
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  resetSession: () => Promise<void>;
  fetchStatus: () => Promise<void>;
  fetchQrCode: () => Promise<void>;
  fetchChats: () => Promise<void>;
  fetchMessages: (chatId: string) => Promise<void>;
  sendMessage: (chatId: string, message: string, mediaPath?: string) => Promise<void>;
  setCurrentChat: (chat: Chat | null) => void;
  addMessage: (message: Message) => void;
  updateStatus: (status: Partial<WhatsAppStatus>) => void;
  setQrCode: (qrCode: string | null) => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useWhatsAppStore = create<WhatsAppStore>((set, get) => ({
  status: null,
  qrCode: null,
  chats: [],
  currentChat: null,
  messages: {},
  loading: false,
  error: null,

  connect: async () => {
    try {
      set({ loading: true, error: null });
      await whatsappApi.connect();
      get().fetchStatus();
    } catch (error: any) {
      set({ error: error.message || 'Failed to connect WhatsApp' });
    } finally {
      set({ loading: false });
    }
  },

  disconnect: async () => {
    try {
      set({ loading: true, error: null });
      await whatsappApi.disconnect();
      set({ status: null, qrCode: null });
    } catch (error: any) {
      set({ error: error.message || 'Failed to disconnect WhatsApp' });
    } finally {
      set({ loading: false });
    }
  },

  resetSession: async () => {
    try {
      set({ loading: true, error: null, qrCode: null });
      await whatsappApi.resetSession();
      // Wait a moment for new QR code to be generated
      await new Promise(resolve => setTimeout(resolve, 2000));
      await get().fetchQrCode();
      await get().fetchStatus();
    } catch (error: any) {
      set({ error: error.message || 'Failed to reset session' });
    } finally {
      set({ loading: false });
    }
  },

  fetchStatus: async () => {
    try {
      const response = await whatsappApi.getStatus();
      if (response.data.success) {
        set({ status: response.data.status });
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch status' });
    }
  },

  fetchQrCode: async () => {
    try {
      const response = await whatsappApi.getQrCode();
      if (response.data.success) {
        set({ qrCode: response.data.qr_code });
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch QR code' });
    }
  },


  fetchChats: async () => {
    try {
      set({ loading: true, error: null });
      const response = await whatsappApi.getChats();
      if (response.data.success) {
        set({ chats: response.data.chats });
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch chats' });
    } finally {
      set({ loading: false });
    }
  },

  fetchMessages: async (chatId: string) => {
    try {
      const response = await whatsappApi.getChatMessages(chatId);
      if (response.data.success) {
        set((state) => ({
          messages: {
            ...state.messages,
            [chatId]: response.data.messages,
          },
        }));
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch messages' });
    }
  },

  sendMessage: async (chatId: string, message: string, mediaPath?: string) => {
    try {
      await whatsappApi.sendMessage(chatId, message, mediaPath);
      // Message will be updated via WebSocket
    } catch (error: any) {
      set({ error: error.message || 'Failed to send message' });
    }
  },

  setCurrentChat: (chat: Chat | null) => {
    set({ currentChat: chat });
    if (chat) {
      get().fetchMessages(chat.id);
    }
  },

  addMessage: (message: Message) => {
    set((state) => ({
      messages: {
        ...state.messages,
        [message.chat_id]: [
          ...(state.messages[message.chat_id] || []),
          message,
        ],
      },
    }));
  },

  updateStatus: (status: Partial<WhatsAppStatus>) => {
    set((state) => ({
      status: state.status ? { ...state.status, ...status } : status as WhatsAppStatus,
    }));
  },

  setQrCode: (qrCode: string | null) => set({ qrCode }),
  setError: (error: string | null) => set({ error }),
  setLoading: (loading: boolean) => set({ loading }),
}));

// Initialize WebSocket listeners
websocketService.on('whatsapp_status', (data: any) => {
  useWhatsAppStore.getState().updateStatus(data);
});

websocketService.on('qr_code', (data: any) => {
  useWhatsAppStore.getState().setQrCode(data.qr);
});

websocketService.on('new_message', (message: any) => {
  console.log('New message received:', message);
  const messageData = message.data || message;

  // Add message to store if we have the chat open
  if (messageData.chatId) {
    useWhatsAppStore.getState().addMessage({
      id: messageData.messageId || messageData.id,
      chat_id: messageData.chatId,
      body: messageData.body,
      message_type: 'text',
      from_me: messageData.fromMe || false,
      timestamp: messageData.timestamp,
      has_media: messageData.hasMedia || false,
      llm_processed: false,
    });
  }

  // Refresh chat list to update last message and timestamps
  useWhatsAppStore.getState().fetchChats();
});

websocketService.on('message_sent', (data: any) => {
  // Handle sent message confirmation
  console.log('Message sent:', data);
});

// Pairing code functionality removed