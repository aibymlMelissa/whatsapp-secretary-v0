import React, { useEffect, useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { useWhatsAppStore } from '@/store/whatsapp';
import { websocketService } from '@/services/websocket';
import { AuthenticationModal } from './AuthenticationModal';
import { Wifi, WifiOff, Loader2, RefreshCw } from 'lucide-react';

export const ConnectionStatus: React.FC = () => {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const {
    status,
    qrCode,
    loading,
    error,
    connect,
    disconnect,
    resetSession,
    fetchStatus,
    fetchQrCode,
  } = useWhatsAppStore();

  useEffect(() => {
    // Initialize WebSocket connection
    websocketService.connect();

    // Fetch initial status
    fetchStatus();

    return () => {
      websocketService.disconnect();
    };
  }, [fetchStatus]);

  useEffect(() => {
    if (status?.connecting || (status && !status.connected)) {
      fetchQrCode();
    }
  }, [status, fetchQrCode]);

  const handleConnect = async () => {
    await connect();
    setAuthModalOpen(true);

    // Clear any existing polling
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    // Poll for status updates to detect when connected
    pollIntervalRef.current = setInterval(async () => {
      await fetchStatus();
      if (status?.connected) {
        setAuthModalOpen(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }
    }, 2000); // Poll every 2 seconds

    // Clear interval after 2 minutes to prevent infinite polling
    setTimeout(() => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }, 120000);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const handleDisconnect = async () => {
    await disconnect();
  };

  const getStatusIcon = () => {
    if (loading) {
      return <Loader2 className="h-4 w-4 animate-spin" />;
    }
    if (status?.connected) {
      return <Wifi className="h-4 w-4 text-green-500" />;
    }
    return <WifiOff className="h-4 w-4 text-red-500" />;
  };

  const getStatusText = () => {
    if (loading) return 'Loading...';
    if (status?.connected) return 'Connected';
    if (status?.connecting) return 'Connecting...';
    return 'Disconnected';
  };

  const getStatusColor = () => {
    if (status?.connected) return 'text-green-600';
    if (status?.connecting) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-4 border rounded-lg bg-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className={`font-medium ${getStatusColor()}`}>
            WhatsApp {getStatusText()}
          </span>
        </div>

        <div className="flex gap-2">
          {status?.connected ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDisconnect}
              disabled={loading}
            >
              Disconnect
            </Button>
          ) : (
            <Button
              variant="default"
              size="sm"
              onClick={handleConnect}
              disabled={loading}
            >
              Connect
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {(status?.connecting || authModalOpen) && (
        <div className="mt-4">
          <AuthenticationModal
            isOpen={authModalOpen || (Boolean(status?.connecting) && !Boolean(status?.connected))}
            onOpenChange={setAuthModalOpen}
            qrData={qrCode || undefined}
            onRefreshQR={resetSession}
          />
        </div>
      )}

      {status && (
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Process:</span>{' '}
            <span className={status.process_running ? 'text-green-600' : 'text-red-600'}>
              {status.process_running ? 'Running' : 'Stopped'}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Session:</span>{' '}
            <span className={status.session_exists ? 'text-green-600' : 'text-gray-600'}>
              {status.session_exists ? 'Exists' : 'Not found'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};