import React from 'react';
import { MessageSquare, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface HeaderProps {
  onSettingsClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onSettingsClick }) => {
  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="container mx-auto px-4 md:px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-green-500 p-2 rounded-lg">
            <MessageSquare className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-gray-800 dark:text-white">
              WhatsApp Secretary AI
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Your AI-powered communication assistant
            </p>
          </div>
        </div>
        {onSettingsClick && (
          <Button
            onClick={onSettingsClick}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Button>
        )}
      </div>
    </header>
  );
};
