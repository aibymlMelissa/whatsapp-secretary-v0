import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { whatsappApi } from '@/services/api';

interface Stats {
  active_chats: number;
  messages_today: number;
  upcoming_appointments: number;
  total_files: number;
  ai_enabled_chats: number;
}

export const QuickStats: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
    // Refresh stats every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const response = await whatsappApi.getStats();
      if (response.data.success) {
        setStats(response.data.stats);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Quick Stats</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Active Chats</span>
            <span className="font-medium">
              {loading ? '...' : stats?.active_chats ?? 0}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Messages Today</span>
            <span className="font-medium">
              {loading ? '...' : stats?.messages_today ?? 0}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Appointments</span>
            <span className="font-medium">
              {loading ? '...' : stats?.upcoming_appointments ?? 0}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Total Files</span>
            <span className="font-medium">
              {loading ? '...' : stats?.total_files ?? 0}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">AI Enabled</span>
            <span className="font-medium">
              {loading ? '...' : stats?.ai_enabled_chats ?? 0}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
