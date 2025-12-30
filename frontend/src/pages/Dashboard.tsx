import React, { useState } from 'react';
import { ConnectionStatus } from '@/components/WhatsApp/ConnectionStatus';
import { ChatList } from '@/components/WhatsApp/ChatList';
import { ChatWindow } from '@/components/WhatsApp/ChatWindow';
import { AppointmentsList } from '@/components/Appointments/AppointmentsList';
import { LLMStatus } from '@/components/LLM/LLMStatus';
import { FileManager } from '@/components/Files/FileManager';
import { QuickStats } from '@/components/Dashboard/QuickStats';
import { QuickActions } from '@/components/Layout/QuickActions';
import { FlowDiagram } from '@/components/Dashboard/FlowDiagram';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

type ModalView = 'appointments' | 'files' | 'flow' | null;

const Dashboard: React.FC = () => {
  const [activeModal, setActiveModal] = useState<ModalView>(null);

  return (
    <div className="bg-gray-50 dark:bg-gray-900 min-h-screen">
      <main className="container mx-auto p-4 md:p-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Left Sidebar */}
          <div className="w-full md:w-1/4 space-y-6">
            <ConnectionStatus />
            <LLMStatus />
            <QuickStats />
            <QuickActions
              onFlowDiagramClick={() => setActiveModal('flow')}
              onAppointmentsClick={() => setActiveModal('appointments')}
              onFilesClick={() => setActiveModal('files')}
            />
          </div>

          {/* Main Content Area */}
          <div className="w-full md:w-3/4">
            <Card className="border border-gray-200 dark:border-gray-700">
              <CardHeader className="border-b border-gray-200 dark:border-gray-700">
                <CardTitle className="text-xl">Conversations</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[calc(100vh-16rem)]">
                  <div className="border-r border-gray-200 dark:border-gray-700">
                    <ChatList />
                  </div>
                  <div>
                    <ChatWindow />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      {/* Modals */}
      <Dialog open={activeModal === 'appointments'} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Appointments</DialogTitle>
          </DialogHeader>
          <AppointmentsList />
        </DialogContent>
      </Dialog>

      <Dialog open={activeModal === 'files'} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>File Manager</DialogTitle>
          </DialogHeader>
          <FileManager />
        </DialogContent>
      </Dialog>

      <Dialog open={activeModal === 'flow'} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>AI WhatsApp Secretary - System Flow</DialogTitle>
          </DialogHeader>
          <FlowDiagram />
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Dashboard;