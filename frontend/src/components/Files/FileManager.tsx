import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const FileManager: React.FC = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>File Manager</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <h4 className="text-sm font-medium">Shared Files</h4>
            <button className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600">
              Upload
            </button>
          </div>

          <div className="space-y-2">
            <div className="text-center text-sm text-muted-foreground py-8">
              No files uploaded yet
            </div>

            {/* Example file structure */}
            {/* <div className="border rounded-lg p-3 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium">document.pdf</p>
                    <p className="text-xs text-muted-foreground">2.5 MB • 2 hours ago</p>
                  </div>
                </div>
                <button className="text-xs text-blue-600 hover:text-blue-800">
                  Download
                </button>
              </div>
            </div> */}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};