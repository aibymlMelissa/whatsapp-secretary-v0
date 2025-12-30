import React from 'react';
import { Calendar, FileText, Workflow } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface QuickAction {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  variant?: 'default' | 'outline';
}

interface QuickActionsProps {
  onAppointmentsClick?: () => void;
  onFilesClick?: () => void;
  onFlowDiagramClick?: () => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  onAppointmentsClick,
  onFilesClick,
  onFlowDiagramClick
}) => {
  const actions: QuickAction[] = [
    {
      icon: <Workflow className="h-4 w-4" />,
      label: 'System Flow',
      onClick: onFlowDiagramClick || (() => {}),
      variant: 'default'
    },
    {
      icon: <Calendar className="h-4 w-4" />,
      label: 'Appointments',
      onClick: onAppointmentsClick || (() => {}),
      variant: 'outline'
    },
    {
      icon: <FileText className="h-4 w-4" />,
      label: 'Files',
      onClick: onFilesClick || (() => {}),
      variant: 'outline'
    }
  ];

  return (
    <Card className="border border-gray-200 dark:border-gray-700">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {actions.map((action, index) => (
          <Button
            key={index}
            variant={action.variant}
            className="w-full justify-start gap-2"
            onClick={action.onClick}
          >
            {action.icon}
            {action.label}
          </Button>
        ))}
      </CardContent>
    </Card>
  );
};
