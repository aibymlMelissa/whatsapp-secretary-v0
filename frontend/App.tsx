import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from '@/components/ui/toast-provider';
import { Header } from '@/components/Layout/Header';
import { Notification } from '@/components/Layout/Notification';
import Dashboard from '@/pages/Dashboard';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { LLMSettings } from '@/components/Settings/LLMSettings';
import './src/globals.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const [notification, setNotification] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  const showNotification = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setNotification({ message, type });
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <Router>
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Header onSettingsClick={() => setShowSettings(true)} />
            <Notification
              message={notification?.message || null}
              type={notification?.type}
              onClose={() => setNotification(null)}
            />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>

            {/* Global Settings Modal */}
            <Dialog open={showSettings} onOpenChange={setShowSettings}>
              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Global Settings</DialogTitle>
                </DialogHeader>
                <LLMSettings />
              </DialogContent>
            </Dialog>
          </div>
        </Router>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;