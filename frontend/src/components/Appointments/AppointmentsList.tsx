import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const AppointmentsList: React.FC = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upcoming Appointments</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="text-center text-sm text-muted-foreground py-8">
            No appointments scheduled
          </div>

          {/* Example appointment structure */}
          {/* <div className="border rounded-lg p-4 space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium">Meeting with John Doe</h4>
                <p className="text-sm text-muted-foreground">
                  Tomorrow at 2:00 PM
                </p>
              </div>
              <div className="text-right">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Pending
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              Discuss project timeline and deliverables
            </p>
          </div> */}
        </div>
      </CardContent>
    </Card>
  );
};