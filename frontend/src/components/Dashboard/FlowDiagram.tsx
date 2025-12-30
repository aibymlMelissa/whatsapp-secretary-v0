import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import {
  MessageSquare,
  Shield,
  Users,
  UserCheck,
  Bot,
  CheckCircle,
  XCircle,
  Clock,
  Calendar,
  FileText,
  HelpCircle,
  Zap,
  Database,
  ArrowRight,
  AlertCircle,
  Archive,
  RefreshCw,
  Trash2,
  Tags,
  FileImage
} from 'lucide-react';

interface FlowNode {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  type: 'start' | 'decision' | 'process' | 'end';
}

interface FlowPath {
  from: string;
  to: string;
  label?: string;
  color: string;
}

export const FlowDiagram: React.FC = () => {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'detailed'>('overview');

  // Define flow nodes
  const overviewNodes: FlowNode[] = [
    {
      id: 'message',
      label: 'Incoming Message',
      description: 'WhatsApp message received from any user',
      icon: <MessageSquare className="w-5 h-5" />,
      color: 'bg-blue-500',
      type: 'start'
    },
    {
      id: 'auth-check',
      label: 'User Type Check',
      description: 'Determine if sender is Boss, Trusted, or Non-trusted',
      icon: <Shield className="w-5 h-5" />,
      color: 'bg-purple-500',
      type: 'decision'
    },
    {
      id: 'boss',
      label: 'Boss Route',
      description: 'Full access - All requests processed immediately',
      icon: <UserCheck className="w-5 h-5" />,
      color: 'bg-green-500',
      type: 'process'
    },
    {
      id: 'trusted',
      label: 'Trusted User Route',
      description: 'AI-enabled - Auto-respond with AI assistance',
      icon: <Users className="w-5 h-5" />,
      color: 'bg-blue-500',
      type: 'process'
    },
    {
      id: 'non-trusted',
      label: 'Non-trusted Route',
      description: 'Authorization required for sensitive operations',
      icon: <AlertCircle className="w-5 h-5" />,
      color: 'bg-orange-500',
      type: 'process'
    },
    {
      id: 'orchestrator',
      label: 'AI Orchestrator',
      description: 'Analyzes intent using LLM + keywords',
      icon: <Bot className="w-5 h-5" />,
      color: 'bg-indigo-500',
      type: 'process'
    },
    {
      id: 'task-create',
      label: 'Create Task',
      description: 'Persist task to database with priority',
      icon: <Database className="w-5 h-5" />,
      color: 'bg-cyan-500',
      type: 'process'
    },
    {
      id: 'routing',
      label: 'Route to Agent',
      description: 'Appointment, Inquiry, File, Conversation, or Document agent',
      icon: <Zap className="w-5 h-5" />,
      color: 'bg-yellow-500',
      type: 'decision'
    },
    {
      id: 'appointment',
      label: 'Appointment Agent',
      description: 'Book, reschedule, cancel appointments',
      icon: <Calendar className="w-5 h-5" />,
      color: 'bg-pink-500',
      type: 'process'
    },
    {
      id: 'inquiry',
      label: 'Inquiry Agent',
      description: 'Answer questions, provide information',
      icon: <HelpCircle className="w-5 h-5" />,
      color: 'bg-teal-500',
      type: 'process'
    },
    {
      id: 'file',
      label: 'File Agent',
      description: 'Process documents and media',
      icon: <FileText className="w-5 h-5" />,
      color: 'bg-violet-500',
      type: 'process'
    },
    {
      id: 'conversation',
      label: 'Conversation Manager',
      description: 'Archive, sync, cleanup, and metadata',
      icon: <Archive className="w-5 h-5" />,
      color: 'bg-amber-500',
      type: 'process'
    },
    {
      id: 'document',
      label: 'Document Analyzer',
      description: 'Summarize PDFs/docs, explain images',
      icon: <FileImage className="w-5 h-5" />,
      color: 'bg-rose-500',
      type: 'process'
    },
    {
      id: 'response',
      label: 'Send Response',
      description: 'Reply sent back via WhatsApp',
      icon: <CheckCircle className="w-5 h-5" />,
      color: 'bg-green-500',
      type: 'end'
    }
  ];

  const overviewPaths: FlowPath[] = [
    { from: 'message', to: 'auth-check', label: 'Analyze', color: 'stroke-gray-400' },
    { from: 'auth-check', to: 'boss', label: 'Boss', color: 'stroke-green-500' },
    { from: 'auth-check', to: 'trusted', label: 'Trusted', color: 'stroke-blue-500' },
    { from: 'auth-check', to: 'non-trusted', label: 'Non-trusted', color: 'stroke-orange-500' },
    { from: 'boss', to: 'orchestrator', label: '', color: 'stroke-green-500' },
    { from: 'trusted', to: 'orchestrator', label: '', color: 'stroke-blue-500' },
    { from: 'non-trusted', to: 'orchestrator', label: 'Request Auth', color: 'stroke-orange-500' },
    { from: 'orchestrator', to: 'task-create', label: 'Classify Intent', color: 'stroke-indigo-500' },
    { from: 'task-create', to: 'routing', label: 'Queue', color: 'stroke-cyan-500' },
    { from: 'routing', to: 'appointment', label: 'Booking Intent', color: 'stroke-pink-500' },
    { from: 'routing', to: 'inquiry', label: 'Info Query', color: 'stroke-teal-500' },
    { from: 'routing', to: 'file', label: 'File Upload', color: 'stroke-violet-500' },
    { from: 'routing', to: 'conversation', label: 'Scheduled Task', color: 'stroke-amber-500' },
    { from: 'routing', to: 'document', label: 'Doc/Image Analysis', color: 'stroke-rose-500' },
    { from: 'appointment', to: 'response', label: '', color: 'stroke-pink-500' },
    { from: 'inquiry', to: 'response', label: '', color: 'stroke-teal-500' },
    { from: 'file', to: 'response', label: '', color: 'stroke-violet-500' },
    { from: 'conversation', to: 'response', label: '', color: 'stroke-amber-500' },
    { from: 'document', to: 'response', label: '', color: 'stroke-rose-500' }
  ];

  const renderNode = (node: FlowNode, index: number) => {
    const isHovered = hoveredNode === node.id;
    const positions = {
      'message': 'top-0 left-1/2 -translate-x-1/2',
      'auth-check': 'top-32 left-1/2 -translate-x-1/2',
      'boss': 'top-64 left-12',
      'trusted': 'top-64 left-1/2 -translate-x-1/2',
      'non-trusted': 'top-64 right-12',
      'orchestrator': 'top-96 left-1/2 -translate-x-1/2',
      'task-create': 'top-[32rem] left-1/2 -translate-x-1/2',
      'routing': 'top-[40rem] left-1/2 -translate-x-1/2',
      'appointment': 'top-[48rem] left-2',
      'inquiry': 'top-[48rem] left-[22%]',
      'file': 'top-[48rem] left-[44%]',
      'conversation': 'top-[48rem] right-[22%]',
      'document': 'top-[48rem] right-2',
      'response': 'top-[60rem] left-1/2 -translate-x-1/2'
    };

    return (
      <div
        key={node.id}
        className={`absolute ${positions[node.id as keyof typeof positions]} transition-all duration-300 ${
          isHovered ? 'scale-110 z-10' : 'scale-100'
        }`}
        onMouseEnter={() => setHoveredNode(node.id)}
        onMouseLeave={() => setHoveredNode(null)}
      >
        <div
          className={`${node.color} text-white p-4 rounded-lg shadow-lg min-w-[160px] ${
            isHovered ? 'shadow-2xl' : ''
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            {node.icon}
            <span className="font-bold text-sm tracking-wide" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
              {node.label}
            </span>
          </div>
          {isHovered && (
            <p className="text-xs mt-2 text-white/90">{node.description}</p>
          )}
        </div>
      </div>
    );
  };

  const renderPath = (path: FlowPath) => {
    const positions: Record<string, { x: number; y: number }> = {
      'message': { x: 50, y: 6 },
      'auth-check': { x: 50, y: 20 },
      'boss': { x: 20, y: 34 },
      'trusted': { x: 50, y: 34 },
      'non-trusted': { x: 80, y: 34 },
      'orchestrator': { x: 50, y: 48 },
      'task-create': { x: 50, y: 60 },
      'routing': { x: 50, y: 73 },
      'appointment': { x: 15, y: 87 },
      'inquiry': { x: 37, y: 87 },
      'file': { x: 63, y: 87 },
      'conversation': { x: 85, y: 87 },
      'response': { x: 50, y: 105 }
    };

    const from = positions[path.from];
    const to = positions[path.to];

    if (!from || !to) return null;

    // Calculate control points for curved path
    const midY = (from.y + to.y) / 2;
    const pathD = `M ${from.x} ${from.y} Q ${from.x} ${midY}, ${to.x} ${to.y}`;

    // Extract color from className
    const colorMap: Record<string, string> = {
      'stroke-gray-400': '#9ca3af',
      'stroke-green-500': '#22c55e',
      'stroke-blue-500': '#3b82f6',
      'stroke-orange-500': '#f97316',
      'stroke-indigo-500': '#6366f1',
      'stroke-cyan-500': '#06b6d4',
      'stroke-pink-500': '#ec4899',
      'stroke-teal-500': '#14b8a6',
      'stroke-violet-500': '#8b5cf6',
      'stroke-amber-500': '#f59e0b'
    };
    const strokeColor = colorMap[path.color] || '#9ca3af';

    return (
      <g key={`${path.from}-${path.to}`} stroke={strokeColor}>
        <path
          d={pathD}
          fill="none"
          className="transition-all duration-300"
          strokeWidth="0.2"
          markerEnd="url(#arrowhead)"
        />
        {path.label && (
          <text
            x={(from.x + to.x) / 2}
            y={midY}
            fontSize="2.5"
            fill="#1f2937"
            fontFamily="Arial, Helvetica, sans-serif"
            fontWeight="400"
            className="dark:fill-gray-200"
            textAnchor="middle"
            style={{
              paintOrder: 'stroke fill',
              stroke: 'white',
              strokeWidth: '0.5',
              strokeLinejoin: 'round'
            }}
          >
            {path.label}
          </text>
        )}
      </g>
    );
  };

  return (
    <div className="w-full h-full">
      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'overview'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
          }`}
        >
          System Overview
        </button>
        <button
          onClick={() => setActiveTab('detailed')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'detailed'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
          }`}
        >
          User Type Details
        </button>
      </div>

      {activeTab === 'overview' ? (
        <div className="relative w-full" style={{ height: '60rem' }}>
          {/* SVG for paths */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <marker
                id="arrowhead"
                markerWidth="4"
                markerHeight="4"
                refX="3.5"
                refY="1.5"
                orient="auto"
              >
                <polygon points="0 0, 4 1.5, 0 3" fill="currentColor" />
              </marker>
            </defs>
            {overviewPaths.map(renderPath)}
          </svg>

          {/* Nodes */}
          {overviewNodes.map((node, index) => renderNode(node, index))}

          {/* Legend */}
          <div className="absolute top-4 right-4 bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg z-10">
            <h4 className="font-bold mb-3 text-sm">User Types</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded"></div>
                <span className="text-xs font-medium">Boss - Full Access</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded"></div>
                <span className="text-xs font-medium">Trusted - AI Enabled</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-orange-500 rounded"></div>
                <span className="text-xs font-medium">Non-trusted - Auth Required</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Boss Card */}
          <Card className="p-6 border-l-4 border-green-500">
            <div className="flex items-start gap-4">
              <div className="bg-green-500 p-3 rounded-lg">
                <UserCheck className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-green-700 dark:text-green-400 mb-2">
                  Boss (Owner/Administrator)
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Identified by specific phone number in settings. Has complete control over the system.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-sm mb-2">Full Permissions:</h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>✓ Create/modify/cancel appointments</li>
                      <li>✓ Access all database information</li>
                      <li>✓ Manage settings and configurations</li>
                      <li>✓ View all conversations</li>
                      <li>✓ No authorization required</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-2">Message Flow:</h4>
                    <div className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-2">
                        <ArrowRight className="w-4 h-4" />
                        <span>Message received</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ArrowRight className="w-4 h-4" />
                        <span>Immediate processing</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ArrowRight className="w-4 h-4" />
                        <span>AI analyzes intent</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ArrowRight className="w-4 h-4" />
                        <span>Direct execution</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ArrowRight className="w-4 h-4" />
                        <span>Response sent</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Trusted User Card */}
          <Card className="p-6 border-l-4 border-blue-500">
            <div className="flex items-start gap-4">
              <div className="bg-blue-500 p-3 rounded-lg">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-blue-700 dark:text-blue-400 mb-2">
                  Trusted Users (Whitelisted)
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Users marked as whitelisted with AI enabled. Can interact with AI assistant for common tasks.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-sm mb-2">Limited Permissions:</h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>✓ Book appointments (auto-confirmed)</li>
                      <li>✓ Query business information</li>
                      <li>✓ Receive AI-powered responses</li>
                      <li>✓ Upload files for processing</li>
                      <li>✗ Cannot access other users' data</li>
                      <li>✗ Cannot modify system settings</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-2">AI Assistance:</h4>
                    <div className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-2">
                        <Bot className="w-4 h-4" />
                        <span>Automatic AI responses</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>Smart appointment booking</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <HelpCircle className="w-4 h-4" />
                        <span>FAQ answering</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>Business hours info</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Non-trusted User Card */}
          <Card className="p-6 border-l-4 border-orange-500">
            <div className="flex items-start gap-4">
              <div className="bg-orange-500 p-3 rounded-lg">
                <AlertCircle className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-orange-700 dark:text-orange-400 mb-2">
                  Non-trusted Users (Public)
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Unknown or unverified users. Requires Boss approval for sensitive operations.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-sm mb-2">Restricted Access:</h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>✓ Basic information queries</li>
                      <li>✓ Request appointments (pending approval)</li>
                      <li>⚠ Sensitive data requires authorization</li>
                      <li>⚠ Boss must approve requests</li>
                      <li>✗ No automatic AI responses</li>
                      <li>✗ Limited database access</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-2">Authorization Flow:</h4>
                    <div className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-2">
                        <ArrowRight className="w-4 h-4" />
                        <span>Request received</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ArrowRight className="w-4 h-4" />
                        <span>Authorization request created</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ArrowRight className="w-4 h-4" />
                        <span>Boss notified</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>Awaiting Boss approval</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        <span>Approved → Execute</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <XCircle className="w-4 h-4" />
                        <span>Denied → Notify user</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Task System Info */}
          <Card className="p-6 border-l-4 border-indigo-500">
            <div className="flex items-start gap-4">
              <div className="bg-indigo-500 p-3 rounded-lg">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-indigo-700 dark:text-indigo-400 mb-2">
                  Agentic Task System
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  All messages are processed through an intelligent task orchestration system.
                </p>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <h4 className="font-medium text-sm mb-2">Orchestrator:</h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>• Analyzes message intent</li>
                      <li>• Uses LLM + keywords</li>
                      <li>• 85%+ accuracy</li>
                      <li>• Routes to specialist</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-2">Specialized Agents:</h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>📅 Appointment Agent</li>
                      <li>❓ Inquiry Agent</li>
                      <li>📄 File Processing Agent</li>
                      <li>📦 Conversation Manager (NEW)</li>
                      <li>👋 Triage Agent</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-2">Benefits:</h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>✓ Task persistence</li>
                      <li>✓ Auto-retry on failure</li>
                      <li>✓ Priority handling</li>
                      <li>✓ Full analytics</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Conversation Manager Card (NEW) */}
          <Card className="p-6 border-l-4 border-amber-500">
            <div className="flex items-start gap-4">
              <div className="bg-amber-500 p-3 rounded-lg">
                <Archive className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-amber-700 dark:text-amber-400 mb-2">
                  ConversationManagerAgent (NEW in v2.1.0)
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Automated conversation lifecycle management with AI-powered metadata extraction.
                </p>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                      <Archive className="w-4 h-4" />
                      Auto-Archive:
                    </h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>• Archive old conversations (90+ days)</li>
                      <li>• Compress archived data</li>
                      <li>• Free up database space</li>
                      <li>• Scheduled daily at 3 AM</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                      <RefreshCw className="w-4 h-4" />
                      Message Sync:
                    </h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>• Sync with WhatsApp</li>
                      <li>• Incremental updates</li>
                      <li>• Runs every 30 minutes</li>
                      <li>• Error tracking & retry</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                      <Trash2 className="w-4 h-4" />
                      Database Cleanup:
                    </h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>• Remove old archives</li>
                      <li>• Delete orphaned records</li>
                      <li>• Optimize tables (VACUUM)</li>
                      <li>• Scheduled daily at 2 AM</li>
                    </ul>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                    <Tags className="w-4 h-4" />
                    AI-Powered Metadata:
                  </h4>
                  <div className="grid grid-cols-4 gap-2 text-xs text-gray-600 dark:text-gray-400">
                    <div className="bg-green-50 dark:bg-green-900/20 p-2 rounded">
                      <div className="font-medium text-green-700 dark:text-green-400">Sentiment Analysis</div>
                      <div className="mt-1">Positive, Negative, Neutral, Mixed</div>
                    </div>
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-2 rounded">
                      <div className="font-medium text-blue-700 dark:text-blue-400">Categorization</div>
                      <div className="mt-1">Appointment, Inquiry, Complaint, Feedback</div>
                    </div>
                    <div className="bg-purple-50 dark:bg-purple-900/20 p-2 rounded">
                      <div className="font-medium text-purple-700 dark:text-purple-400">Auto-Tagging</div>
                      <div className="mt-1">Urgent, Follow-up, Price, etc.</div>
                    </div>
                    <div className="bg-amber-50 dark:bg-amber-900/20 p-2 rounded">
                      <div className="font-medium text-amber-700 dark:text-amber-400">Scheduled Tasks</div>
                      <div className="mt-1">Weekly metadata updates on Sunday</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Document Analyzer Card (NEW) */}
          <Card className="p-6 border-l-4 border-rose-500">
            <div className="flex items-start gap-4">
              <div className="bg-rose-500 p-3 rounded-lg">
                <FileImage className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-rose-700 dark:text-rose-400 mb-2">
                  DocumentAnalyzerAgent (NEW in v2.2.0)
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  AI-powered document and image analysis exclusively for the Boss user.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      Document Analysis:
                    </h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>• PDF summarization & extraction</li>
                      <li>• Word document analysis</li>
                      <li>• Text file processing</li>
                      <li>• Key points & action items</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                      <FileImage className="w-4 h-4" />
                      Image Analysis:
                    </h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <li>• Image description & explanation</li>
                      <li>• Text extraction from images (OCR)</li>
                      <li>• Visual content analysis</li>
                      <li>• Powered by Gemini/Claude Vision</li>
                    </ul>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    Boss-Only Authentication:
                  </h4>
                  <div className="grid grid-cols-3 gap-2 text-xs text-gray-600 dark:text-gray-400">
                    <div className="bg-rose-50 dark:bg-rose-900/20 p-2 rounded">
                      <div className="font-medium text-rose-700 dark:text-rose-400">Phone Verification</div>
                      <div className="mt-1">Only Boss number authorized</div>
                    </div>
                    <div className="bg-rose-50 dark:bg-rose-900/20 p-2 rounded">
                      <div className="font-medium text-rose-700 dark:text-rose-400">Task Validation</div>
                      <div className="mt-1">Orchestrator confirms intent</div>
                    </div>
                    <div className="bg-rose-50 dark:bg-rose-900/20 p-2 rounded">
                      <div className="font-medium text-rose-700 dark:text-rose-400">Secure Processing</div>
                      <div className="mt-1">Files handled privately</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
