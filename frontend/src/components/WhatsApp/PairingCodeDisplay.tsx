import React, { useState } from 'react';
import { Smartphone, Key, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface PairingCodeDisplayProps {
  pairingCode?: string;
  phoneNumber?: string;
  onRequestCode: (phoneNumber: string) => Promise<void>;
  onRefresh?: () => void;
  className?: string;
  isRequesting?: boolean;
}

export const PairingCodeDisplay: React.FC<PairingCodeDisplayProps> = ({
  pairingCode,
  phoneNumber: currentPhoneNumber,
  onRequestCode,
  onRefresh,
  className = '',
  isRequesting = false
}) => {
  const [phoneNumber, setPhoneNumber] = useState(currentPhoneNumber || '');
  const [isValidPhone, setIsValidPhone] = useState(false);

  const validatePhoneNumber = (phone: string) => {
    // Basic phone validation - starts with + and has 10-15 digits
    const phoneRegex = /^\+[1-9]\d{9,14}$/;
    return phoneRegex.test(phone);
  };

  const handlePhoneChange = (value: string) => {
    setPhoneNumber(value);
    setIsValidPhone(validatePhoneNumber(value));
  };

  const handleRequestCode = async () => {
    if (isValidPhone && !isRequesting) {
      await onRequestCode(phoneNumber);
    }
  };

  const formatPairingCode = (code: string) => {
    // Format as XXXX-XXXX for better readability
    if (code && code.length === 8) {
      return `${code.substring(0, 4)}-${code.substring(4)}`;
    }
    return code;
  };

  return (
    <div className={`bg-white p-6 border rounded-lg ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Smartphone className="h-5 w-5" />
          <span className="font-semibold">WhatsApp Phone Authentication</span>
        </div>
        {onRefresh && pairingCode && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        )}
      </div>

      {!pairingCode ? (
        <div className="space-y-4">
          <div>
            <Label htmlFor="phone-number" className="text-sm font-medium">
              Phone Number
            </Label>
            <Input
              id="phone-number"
              type="tel"
              placeholder="+1234567890"
              value={phoneNumber}
              onChange={(e) => handlePhoneChange(e.target.value)}
              className={`mt-1 ${!isValidPhone && phoneNumber ? 'border-red-500' : ''}`}
              disabled={isRequesting}
            />
            {!isValidPhone && phoneNumber && (
              <p className="text-sm text-red-500 mt-1">
                Please enter a valid phone number with country code (e.g., +1234567890)
              </p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              Include country code (e.g., +1 for US, +44 for UK)
            </p>
          </div>

          <Button
            onClick={handleRequestCode}
            disabled={!isValidPhone || isRequesting}
            className="w-full"
          >
            {isRequesting ? (
              <div className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4 animate-spin" />
                Requesting Code...
              </div>
            ) : (
              'Request Pairing Code'
            )}
          </Button>

          <div className="text-center text-sm text-gray-600">
            <p>Enter your WhatsApp phone number to receive a pairing code</p>
          </div>
        </div>
      ) : (
        <div className="text-center space-y-6">
          <div className="bg-gray-50 p-6 rounded-lg border-2 border-dashed border-gray-300">
            <div className="flex items-center justify-center mb-4">
              <Key className="h-8 w-8 text-blue-500" />
            </div>
            <div className="text-3xl font-mono font-bold text-gray-800 tracking-widest">
              {formatPairingCode(pairingCode)}
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Pairing Code for {currentPhoneNumber}
            </p>
          </div>

          <div className="space-y-3">
            <p className="text-sm font-medium text-gray-800">
              Enter this code in your WhatsApp mobile app:
            </p>
            <ol className="text-sm text-gray-600 space-y-1 text-left max-w-xs mx-auto">
              <li>1. Open WhatsApp on your phone</li>
              <li>2. Go to <span className="font-medium">Settings → Linked Devices</span></li>
              <li>3. Tap <span className="font-medium">"Link a Device"</span></li>
              <li>4. Choose <span className="font-medium">"Link with phone number instead"</span></li>
              <li>5. Enter the code: <span className="font-mono font-bold">{formatPairingCode(pairingCode)}</span></li>
            </ol>
          </div>

          <div className="pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => {
                setPhoneNumber('');
                onRefresh && onRefresh();
              }}
              className="text-sm"
            >
              Use Different Number
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};