import React, { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useWhatsAppStore } from '@/store/whatsapp';
import { websocketService } from '@/services/websocket';
import { QRCodeDisplay } from './QRCodeDisplay';
import { QRCodeModal } from './QRCodeModal';
import { Wifi, WifiOff, Loader2, Maximize } from 'lucide-react';

export const ConnectionStatus: React.FC = () => {
  const {
    status,
    qrCode,
    loading,
    error,
    connect,
    disconnect,
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
  };

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

      {status?.connecting && qrCode && (
        <div className="mt-4 space-y-3">
          <QRCodeDisplay
            qrData={qrCode}
            onRefresh={fetchQrCode}
          />
          <div className="flex justify-center">
            <QRCodeModal
              qrData={qrCode}
              onRefresh={fetchQrCode}
              trigger={
                <Button variant="outline" size="sm" className="flex items-center gap-2">
                  <Maximize className="h-4 w-4" />
                  View Larger QR Code
                </Button>
              }
            />
          </div>
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