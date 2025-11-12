import React, { useEffect } from 'react';
import { useWhatsAppStore } from '@/store/whatsapp';
import { Chat } from '@/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';
import { MessageCircle, Users, Shield } from 'lucide-react';

export const ChatList: React.FC = () => {
  const { chats, currentChat, fetchChats, setCurrentChat, loading } = useWhatsAppStore();

  useEffect(() => {
    fetchChats();
  }, [fetchChats]);

  const handleChatSelect = (chat: Chat) => {
    setCurrentChat(chat);
  };

  const getChatInitials = (chat: Chat) => {
    return chat.name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatLastMessageTime = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return '';
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-2 text-sm text-muted-foreground">Loading chats...</p>
      </div>
    );
  }

  if (chats.length === 0) {
    return (
      <div className="p-4 text-center">
        <MessageCircle className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground">No chats available</p>
        <p className="text-xs text-muted-foreground mt-1">
          Connect WhatsApp to see your conversations
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-1 p-2">
        {chats.map((chat) => (
          <div
            key={chat.id}
            onClick={() => handleChatSelect(chat)}
            className={`
              flex items-center p-3 rounded-lg cursor-pointer transition-colors
              hover:bg-accent hover:text-accent-foreground
              ${currentChat?.id === chat.id ? 'bg-accent text-accent-foreground' : ''}
            `}
          >
            <Avatar className="h-10 w-10 mr-3">
              <AvatarFallback className="bg-primary/10">
                {getChatInitials(chat)}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium truncate">{chat.name}</h3>
                  {chat.is_group && (
                    <Users className="h-3 w-3 text-muted-foreground" />
                  )}
                  {chat.is_whitelisted && (
                    <Shield className="h-3 w-3 text-green-500" />
                  )}
                  {chat.unread_count && chat.unread_count > 0 && (
                    <Badge variant="default" className="h-5 min-w-5 flex items-center justify-center text-xs px-1.5">
                      {chat.unread_count}
                    </Badge>
                  )}
                </div>
                {chat.last_message && (
                  <span className="text-xs text-muted-foreground">
                    {formatLastMessageTime(chat.last_message.timestamp)}
                  </span>
                )}
              </div>

              {chat.phone_number && (
                <p className="text-xs text-muted-foreground">
                  {chat.phone_number}
                </p>
              )}

              {chat.last_message && (
                <div className="flex items-center justify-between mt-1">
                  <p className="text-sm text-muted-foreground truncate">
                    {chat.last_message.from_me && 'You: '}
                    {chat.last_message.body}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
};