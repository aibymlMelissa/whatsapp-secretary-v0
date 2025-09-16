import React from 'react';
import { ConnectionStatus } from '@/components/WhatsApp/ConnectionStatus';
import { ChatList } from '@/components/WhatsApp/ChatList';
import { ChatWindow } from '@/components/WhatsApp/ChatWindow';
import { AppointmentsList } from '@/components/Appointments/AppointmentsList';
import { LLMStatus } from '@/components/LLM/LLMStatus';
import { FileManager } from '@/components/Files/FileManager';
import { LLMSettings } from '@/components/Settings/LLMSettings';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const Dashboard: React.FC = () => {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-foreground">WhatsApp Secretary</h1>
        <p className="text-muted-foreground">
          Manage your WhatsApp conversations with AI assistance
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* WhatsApp Connection Status */}
        <div className="lg:col-span-1">
          <ConnectionStatus />
        </div>

        {/* Main Chat Interface */}
        <div className="lg:col-span-2">
          <Card className="h-[600px]">
            <CardHeader>
              <CardTitle>Conversations</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="grid grid-cols-1 md:grid-cols-2 h-[550px]">
                <div className="border-r">
                  <ChatList />
                </div>
                <div>
                  <ChatWindow />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Side Panel */}
        <div className="lg:col-span-1 space-y-4">
          <LLMStatus />
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Active Chats</span>
                  <span className="font-medium">-</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Messages Today</span>
                  <span className="font-medium">-</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Appointments</span>
                  <span className="font-medium">-</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom Section with Tabs */}
      <Tabs defaultValue="appointments" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="appointments">Appointments</TabsTrigger>
          <TabsTrigger value="files">Files</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="appointments" className="space-y-4">
          <AppointmentsList />
        </TabsContent>

        <TabsContent value="files" className="space-y-4">
          <FileManager />
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <LLMSettings />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Analytics and insights will be displayed here.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;