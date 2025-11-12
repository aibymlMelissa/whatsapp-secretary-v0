import React, { useState, useEffect, useRef } from 'react';
import { useWhatsAppStore } from '@/store/whatsapp';
import { whatsappApi } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, MessageCircle, Bot, Shield, ShieldOff } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export const ChatWindow: React.FC = () => {
  const { currentChat, messages, sendMessage, fetchMessages, fetchChats } = useWhatsAppStore();
  const [messageInput, setMessageInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isTogglingAI, setIsTogglingAI] = useState(false);
  const [isTogglingWhitelist, setIsTogglingWhitelist] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentMessages = currentChat ? messages[currentChat.id] || [] : [];

  useEffect(() => {
    if (currentChat) {
      fetchMessages(currentChat.id);
    }
  }, [currentChat, fetchMessages]);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages]);

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !currentChat || isSending) return;

    setIsSending(true);
    try {
      await sendMessage(currentChat.id, messageInput.trim());
      setMessageInput('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatMessageTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '';
    }
  };

  const handleToggleAI = async () => {
    if (!currentChat || isTogglingAI) return;

    setIsTogglingAI(true);
    try {
      await whatsappApi.toggleAI(currentChat.id, !currentChat.ai_enabled);
      // Refresh chats to get updated ai_enabled status
      await fetchChats();
    } catch (error) {
      console.error('Failed to toggle AI:', error);
    } finally {
      setIsTogglingAI(false);
    }
  };

  const handleToggleWhitelist = async () => {
    if (!currentChat || isTogglingWhitelist) return;

    setIsTogglingWhitelist(true);
    try {
      await whatsappApi.toggleWhitelist(currentChat.id, !currentChat.is_whitelisted);
      // Refresh chats to get updated whitelist status
      await fetchChats();
    } catch (error) {
      console.error('Failed to toggle whitelist:', error);
    } finally {
      setIsTogglingWhitelist(false);
    }
  };

  if (!currentChat) {
    return (
      <div className="h-full flex flex-col">
        <CardHeader>
          <CardTitle className="text-lg">Chat</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <MessageCircle className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <p className="text-sm text-muted-foreground">
              Select a chat to start messaging
            </p>
          </div>
        </CardContent>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{currentChat.name}</CardTitle>
            {currentChat.phone_number && (
              <p className="text-xs text-muted-foreground">{currentChat.phone_number}</p>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant={currentChat.is_whitelisted ? "default" : "outline"}
              size="sm"
              onClick={handleToggleWhitelist}
              disabled={isTogglingWhitelist}
            >
              {currentChat.is_whitelisted ? (
                <>
                  <Shield className="h-4 w-4 mr-2" />
                  Trusted
                </>
              ) : (
                <>
                  <ShieldOff className="h-4 w-4 mr-2" />
                  Untrusted
                </>
              )}
            </Button>
            <Button
              variant={currentChat.ai_enabled ? "default" : "outline"}
              size="sm"
              onClick={handleToggleAI}
              disabled={isTogglingAI}
            >
              {currentChat.ai_enabled ? (
                <>
                  <Bot className="h-4 w-4 mr-2" />
                  AI On
                </>
              ) : (
                <>
                  <Bot className="h-4 w-4 mr-2 opacity-50" />
                  AI Off
                </>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-0">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {currentMessages.length === 0 ? (
              <div className="text-center text-sm text-muted-foreground py-8">
                No messages yet. Start the conversation!
              </div>
            ) : (
              currentMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.from_me ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg px-4 py-2 ${
                      message.from_me
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap break-words">
                      {message.body}
                    </p>
                    <p
                      className={`text-xs mt-1 ${
                        message.from_me
                          ? 'text-primary-foreground/70'
                          : 'text-muted-foreground'
                      }`}
                    >
                      {formatMessageTime(message.timestamp)}
                    </p>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        <div className="border-t p-4">
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder="Type a message..."
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isSending}
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!messageInput.trim() || isSending}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </div>
  );
};