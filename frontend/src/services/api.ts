import axios from 'axios';
import { Chat, Message, Appointment, WhatsAppStatus, LLMStatus } from '@/types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
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
  getDownloads: () => api.get('/files/downloads'),
  deleteFile: (filename: string) => api.delete(`/files/downloads/${filename}`),
  getStorageStats: () => api.get('/files/stats'),
};

export default api;