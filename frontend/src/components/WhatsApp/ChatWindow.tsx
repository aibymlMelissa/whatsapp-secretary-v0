import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const ChatWindow: React.FC = () => {
  return (
    <div className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="text-lg">Chat</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto bg-gray-50 rounded-lg p-4 mb-4">
          <div className="space-y-3">
            <div className="text-center text-sm text-muted-foreground">
              Select a chat to start messaging
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type a message..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled
          />
          <button
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            disabled
          >
            Send
          </button>
        </div>
      </CardContent>
    </div>
  );
};