import React, { useEffect, useState } from 'react';
import { CheckCircle, X, AlertCircle, Info } from 'lucide-react';

interface NotificationProps {
  message: string | null;
  type?: 'success' | 'error' | 'info';
  onClose: () => void;
}

export const Notification: React.FC<NotificationProps> = ({
  message,
  type = 'success',
  onClose
}) => {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (message) {
      setShow(true);
      const timer = setTimeout(() => {
        setShow(false);
        setTimeout(onClose, 300);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [message, onClose]);

  if (!message) return null;

  const icons = {
    success: <CheckCircle className="h-5 w-5 text-green-400" />,
    error: <AlertCircle className="h-5 w-5 text-red-400" />,
    info: <Info className="h-5 w-5 text-blue-400" />
  };

  const bgColors = {
    success: 'bg-gray-800',
    error: 'bg-red-900',
    info: 'bg-blue-900'
  };

  return (
    <div
      className={`fixed top-5 left-1/2 -translate-x-1/2 z-50 w-full max-w-md p-4 rounded-lg shadow-lg ${bgColors[type]} text-white flex items-center justify-between transition-all duration-300 ${
        show ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-5'
      }`}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-center space-x-3">
        {icons[type]}
        <p className="font-medium">{message}</p>
      </div>
      <button
        onClick={() => {
          setShow(false);
          setTimeout(onClose, 300);
        }}
        className="p-1 rounded-full hover:bg-gray-700 transition-colors"
        aria-label="Close notification"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};
