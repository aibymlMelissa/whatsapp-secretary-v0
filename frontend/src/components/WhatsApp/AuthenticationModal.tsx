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
import { QrCode, Wifi } from 'lucide-react';

interface AuthenticationModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  qrData?: string;
  onRefreshQR?: () => void;
  trigger?: React.ReactNode;
}

export const AuthenticationModal: React.FC<AuthenticationModalProps> = ({
  isOpen,
  onOpenChange,
  qrData,
  onRefreshQR,
  trigger
}) => {
  const defaultTrigger = (
    <Button className="flex items-center gap-2">
      <Wifi className="h-4 w-4" />
      Connect WhatsApp
    </Button>
  );

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        {trigger || defaultTrigger}
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wifi className="h-5 w-5" />
            Connect to WhatsApp
          </DialogTitle>
          <DialogDescription>
            Scan the QR code with your WhatsApp mobile app to connect your account.
          </DialogDescription>
        </DialogHeader>

        <div className="mt-6">
          {qrData ? (
            <QRCodeDisplay
              qrData={qrData}
              onRefresh={onRefreshQR}
              className="border-0 p-0"
            />
          ) : (
            <div className="text-center py-8">
              <QrCode className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Generating QR code...</p>
              <p className="text-sm text-gray-500 mt-2">
                Please wait while we prepare the QR code for scanning
              </p>
            </div>
          )}
        </div>

        <div className="mt-6 pt-4 border-t">
          <div className="text-center">
            <p className="text-xs text-gray-500">
              Open WhatsApp on your phone → Settings → Linked Devices → Link a Device
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};