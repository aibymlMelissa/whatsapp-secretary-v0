import axios from 'axios';
import { Chat, Message, Appointment, WhatsAppStatus, LLMStatus } from '@/types';

// Dynamically determine API base URL
const getApiBaseUrl = () => {
  // Check if we have a custom backend URL from environment
  if (import.meta.env.VITE_BACKEND_URL) {
    return `${import.meta.env.VITE_BACKEND_URL}/api`;
  }

  // If we're running on ngrok-free.app, use the same host for API calls
  if (typeof window !== 'undefined' && window.location.hostname.includes('ngrok-free.app')) {
    // Extract the ngrok URL and point to backend port
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    // For ngrok, we need to use the backend URL (assuming it's on the same ngrok instance)
    return `${protocol}//${hostname}/api`;
  }

  // Default to relative path (works with Vite proxy)
  return '/api';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Increased timeout for ngrok
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    throw error;
  }
);

export const whatsappApi = {
  connect: () => api.post('/whatsapp/connect'),
  disconnect: () => api.post('/whatsapp/disconnect'),
  getStatus: (): Promise<{ data: { success: boolean; status: WhatsAppStatus } }> =>
    api.get('/whatsapp/status'),
  getQrCode: () => api.get('/whatsapp/qr'),
  sendMessage: (chatId: string, message: string, mediaPath?: string) =>
    api.post('/whatsapp/send-message', { chat_id: chatId, message, media_path: mediaPath }),
  getChats: (): Promise<{ data: { success: boolean; chats: Chat[] } }> =>
    api.get('/whatsapp/chats'),
  getChatMessages: (chatId: string, limit = 50): Promise<{ data: { success: boolean; messages: Message[] } }> =>
    api.get(`/whatsapp/chats/${chatId}/messages?limit=${limit}`),
  toggleAI: (chatId: string, enabled: boolean) =>
    api.post(`/whatsapp/chats/${chatId}/toggle-ai?enabled=${enabled}`),
  toggleWhitelist: (chatId: string, whitelisted: boolean) =>
    api.post(`/whatsapp/chats/${chatId}/toggle-whitelist?whitelisted=${whitelisted}`),
  getStats: () => api.get('/whatsapp/stats'),
};

export const appointmentsApi = {
  create: (appointmentData: Partial<Appointment>) =>
    api.post('/appointments/', appointmentData),
  getAll: (filters?: { chat_id?: string; status?: string; date_from?: string; date_to?: string }) =>
    api.get('/appointments/', { params: filters }),
  getById: (id: number): Promise<{ data: { success: boolean; appointment: Appointment } }> =>
    api.get(`/appointments/${id}`),
  update: (id: number, data: Partial<Appointment>) =>
    api.put(`/appointments/${id}`, data),
  cancel: (id: number) =>
    api.delete(`/appointments/${id}`),
  getAvailableSlots: (date: string, durationMinutes = 60) =>
    api.get(`/appointments/availability/slots?date=${date}&duration_minutes=${durationMinutes}`),
  processNLP: (message: string, chatId: string) =>
    api.post('/appointments/process-nlp', { message, chat_id: chatId }),
};

export const llmApi = {
  getStatus: (): Promise<{ data: { success: boolean; status: LLMStatus } }> =>
    api.get('/llm/status'),
  generateResponse: (message: string, chatId: string, provider = 'auto') =>
    api.post('/llm/generate', { message, chat_id: chatId, provider }),
  clearCache: (chatId?: string) =>
    api.post('/llm/clear-cache', { chat_id: chatId }),
};

export const filesApi = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  list: () => api.get('/files/list'),
  download: (fileId: number) => {
    return api.get(`/files/download/${fileId}`, {
      responseType: 'blob',
    });
  },
  delete: (fileId: number) => api.delete(`/files/delete/${fileId}`),
};

export default api;