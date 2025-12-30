import React, { useEffect, useRef } from 'react';
import QRCode from 'qrcode';
import { QrCode, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface QRCodeDisplayProps {
  qrData: string;
  onRefresh?: () => void;
  className?: string;
}

export const QRCodeDisplay: React.FC<QRCodeDisplayProps> = ({
  qrData,
  onRefresh,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const generateQR = async () => {
      if (qrData && canvasRef.current) {
        try {
          await QRCode.toCanvas(canvasRef.current, qrData, {
            width: 256,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#FFFFFF'
            }
          });
        } catch (error) {
          console.error('Error generating QR code:', error);
        }
      }
    };

    generateQR();
  }, [qrData]);

  if (!qrData) {
    return (
      <div className={`flex items-center justify-center p-8 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg ${className}`}>
        <div className="text-center">
          <QrCode className="h-12 w-12 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">No QR code available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white p-6 border rounded-lg ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <QrCode className="h-5 w-5" />
          <span className="font-semibold">WhatsApp QR Code</span>
        </div>
        {onRefresh && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Generate New QR
          </Button>
        )}
      </div>

      <div className="flex justify-center">
        <div className="p-4 bg-white border-2 border-gray-200 rounded-lg">
          <canvas
            ref={canvasRef}
            className="max-w-full h-auto"
          />
        </div>
      </div>

      <div className="mt-4 text-center">
        <p className="text-sm text-gray-600">
          Open WhatsApp on your phone, go to{' '}
          <span className="font-medium">Settings → Linked Devices</span>{' '}
          and scan this QR code to connect.
        </p>
      </div>
    </div>
  );
};