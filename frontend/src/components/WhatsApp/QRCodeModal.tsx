import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { QRCodeDisplay } from './QRCodeDisplay';
import { QrCode, Maximize } from 'lucide-react';

interface QRCodeModalProps {
  qrData: string;
  onRefresh?: () => void;
  trigger?: React.ReactNode;
}

export const QRCodeModal: React.FC<QRCodeModalProps> = ({
  qrData,
  onRefresh,
  trigger
}) => {
  const defaultTrigger = (
    <Button variant="outline" size="sm" className="flex items-center gap-2">
      <Maximize className="h-4 w-4" />
      View Large QR Code
    </Button>
  );

  return (
    <Dialog>
      <DialogTrigger asChild>
        {trigger || defaultTrigger}
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <QrCode className="h-5 w-5" />
            WhatsApp QR Code
          </DialogTitle>
          <DialogDescription>
            Scan this QR code with your WhatsApp mobile app to connect your device.
          </DialogDescription>
        </DialogHeader>

        <div className="flex justify-center">
          <QRCodeDisplay
            qrData={qrData}
            onRefresh={onRefresh}
            className="border-0 p-0"
          />
        </div>

        <div className="text-center space-y-2">
          <p className="text-sm text-muted-foreground">
            <strong>Instructions:</strong>
          </p>
          <ol className="text-sm text-muted-foreground space-y-1 text-left">
            <li>1. Open WhatsApp on your phone</li>
            <li>2. Go to <span className="font-medium">Settings → Linked Devices</span></li>
            <li>3. Tap <span className="font-medium">"Link a Device"</span></li>
            <li>4. Scan this QR code</li>
          </ol>
        </div>
      </DialogContent>
    </Dialog>
  );
};