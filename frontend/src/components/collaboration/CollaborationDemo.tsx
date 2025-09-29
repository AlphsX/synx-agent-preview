'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { 
  Users, 
  MessageCircle, 
  GitBranch, 
  Share2, 
  Eye, 
  Edit, 
  Crown,
  Wifi,
  WifiOff,
  Clock,
  Zap
} from 'lucide-react';

interface Participant {
  id: string;
  display_name: string;
  role: 'owner' | 'editor' | 'viewer' | 'commenter';
  presence_status: 'online' | 'away' | 'busy' | 'offline';
  is_typing: boolean;
  avatar_color: string;
}

interface TypingIndicator {
  session_id: string;
  display_name: string;
  typing_text?: string;
}

interface ConversationBranch {
  id: string;
  title: string;
  description?: string;
  branch_type: string;
  creator_id?: string;
  is_active: boolean;
  is_merged: boolean;
  vote_score: number;
  created_at: string;
}

const CollaborationDemo: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [typingIndicators, setTypingIndicators] = useState<TypingIndicator[]>([]);
  const [branches, setBranches] = useState<ConversationBranch[]>([]);
  const [shareToken, setShareToken] = useState<string>('');
  const [newBranchTitle, setNewBranchTitle] = useState('');
  const [currentMessage, setCurrentMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Mock data for demonstration
  useEffect(() => {
    // Simulate initial participants
    setParticipants([
      {
        id: '1',
        display_name: 'Alice (Owner)',
        role: 'owner',
        presence_status: 'online',
        is_typing: false,
        avatar_color: '#3B82F6'
      },
      {
        id: '2', 
        display_name: 'Bob',
        role: 'editor',
        presence_status: 'online',
        is_typing: true,
        avatar_color: '#10B981'
      },
      {
        id: '3',
        display_name: 'Charlie',
        role: 'viewer',
        presence_status: 'away',
        is_typing: false,
        avatar_color: '#F59E0B'
      }
    ]);

    // Simulate typing indicators
    setTypingIndicators([
      {
        session_id: '2',
        display_name: 'Bob',
        typing_text: 'I think we should consider...'
      }
    ]);

    // Simulate branches
    setBranches([
      {
        id: '1',
        title: 'Alternative Approach',
        description: 'Exploring a different solution path',
        branch_type: 'alternative',
        creator_id: '2',
        is_active: true,
        is_merged: false,
        vote_score: 3,
        created_at: new Date().toISOString()
      },
      {
        id: '2',
        title: 'Bug Fix Branch',
        description: 'Addressing the issue mentioned earlier',
        branch_type: 'correction',
        creator_id: '1',
        is_active: true,
        is_merged: true,
        vote_score: 5,
        created_at: new Date().toISOString()
      }
    ]);

    setShareToken('abc123def456');
  }, []);

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner': return <Crown className="w-4 h-4 text-yellow-500" />;
      case 'editor': return <Edit className="w-4 h-4 text-blue-500" />;
      case 'viewer': return <Eye className="w-4 h-4 text-gray-500" />;
      default: return <MessageCircle className="w-4 h-4 text-green-500" />;
    }
  };

  const getPresenceIcon = (status: string) => {
    switch (status) {
      case 'online': return <Wifi className="w-3 h-3 text-green-500" />;
      case 'away': return <Clock className="w-3 h-3 text-yellow-500" />;
      case 'busy': return <Zap className="w-3 h-3 text-red-500" />;
      default: return <WifiOff className="w-3 h-3 text-gray-400" />;
    }
  };

  const handleCreateBranch = () => {
    if (!newBranchTitle.trim()) return;

    const newBranch: ConversationBranch = {
      id: Date.now().toString(),
      title: newBranchTitle,
      description: 'New branch created from demo',
      branch_type: 'alternative',
      creator_id: '1',
      is_active: true,
      is_merged: false,
      vote_score: 0,
      created_at: new Date().toISOString()
    };

    setBranches(prev => [newBranch, ...prev]);
    setNewBranchTitle('');
  };

  const handleTyping = (text: string) => {
    setCurrentMessage(text);
    
    if (text.length > 0 && !isTyping) {
      setIsTyping(true);
      // Simulate typing indicator
      setTimeout(() => setIsTyping(false), 3000);
    }
  };

  const handleConnect = () => {
    setIsConnected(!isConnected);
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Real-time Collaboration Demo</h1>
        <p className="text-gray-600">
          Experience shared conversations, typing indicators, presence status, and branching
        </p>
      </div>

      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Share2 className="w-5 h-5" />
            Connection Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isConnected ? (
                <>
                  <Wifi className="w-4 h-4 text-green-500" />
                  <span className="text-green-600">Connected to shared conversation</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-500">Not connected</span>
                </>
              )}
            </div>
            <Button onClick={handleConnect} variant={isConnected ? "destructive" : "default"}>
              {isConnected ? 'Disconnect' : 'Connect'}
            </Button>
          </div>
          
          {shareToken && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">Share this conversation:</p>
              <div className="flex items-center gap-2">
                <Input 
                  value={`/shared/${shareToken}`} 
                  readOnly 
                  className="font-mono text-sm"
                />
                <Button size="sm" variant="outline">Copy</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Participants */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Participants ({participants.length})
            </CardTitle>
            <CardDescription>
              Users currently in this shared conversation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {participants.map((participant) => (
                <div key={participant.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                      style={{ backgroundColor: participant.avatar_color }}
                    >
                      {participant.display_name.charAt(0)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{participant.display_name}</span>
                        {getRoleIcon(participant.role)}
                      </div>
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        {getPresenceIcon(participant.presence_status)}
                        <span className="capitalize">{participant.presence_status}</span>
                      </div>
                    </div>
                  </div>
                  
                  {participant.is_typing && (
                    <Badge variant="secondary" className="text-xs">
                      Typing...
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Typing Indicators */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="w-5 h-5" />
              Live Typing Indicators
            </CardTitle>
            <CardDescription>
              See what others are typing in real-time
            </CardDescription>
          </CardHeader>
          <CardContent>
            {typingIndicators.length > 0 ? (
              <div className="space-y-3">
                {typingIndicators.map((indicator) => (
                  <div key={indicator.session_id} className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                      <span className="font-medium text-blue-700">{indicator.display_name} is typing</span>
                    </div>
                    {indicator.typing_text && (
                      <p className="text-sm text-gray-600 italic">"{indicator.typing_text}"</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No one is typing right now</p>
            )}
            
            {/* Demo typing input */}
            <div className="mt-4 pt-4 border-t">
              <label className="block text-sm font-medium mb-2">Try typing (demo):</label>
              <Textarea
                value={currentMessage}
                onChange={(e) => handleTyping(e.target.value)}
                placeholder="Start typing to see the indicator..."
                className="resize-none"
                rows={2}
              />
              {isTyping && (
                <p className="text-xs text-blue-600 mt-1">✨ Others can see you're typing!</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Conversation Branches */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="w-5 h-5" />
            Conversation Branches
          </CardTitle>
          <CardDescription>
            Alternative conversation paths and merged discussions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Create new branch */}
            <div className="flex gap-2">
              <Input
                value={newBranchTitle}
                onChange={(e) => setNewBranchTitle(e.target.value)}
                placeholder="Enter branch title..."
                className="flex-1"
              />
              <Button onClick={handleCreateBranch} disabled={!newBranchTitle.trim()}>
                Create Branch
              </Button>
            </div>

            {/* Existing branches */}
            <div className="space-y-3">
              {branches.map((branch) => (
                <div key={branch.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium">{branch.title}</h4>
                        <Badge variant={branch.is_merged ? "default" : "secondary"}>
                          {branch.is_merged ? 'Merged' : 'Active'}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {branch.branch_type}
                        </Badge>
                      </div>
                      {branch.description && (
                        <p className="text-sm text-gray-600">{branch.description}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <span>👍 {branch.vote_score}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Created {new Date(branch.created_at).toLocaleDateString()}</span>
                    {!branch.is_merged && (
                      <Button size="sm" variant="outline" className="text-xs">
                        Merge Branch
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Feature Summary */}
      <Card>
        <CardHeader>
          <CardTitle>🎉 Collaboration Features Implemented</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="font-medium">✅ Shared Conversation Spaces</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Multiple users can join conversations</li>
                <li>• Share tokens for easy access</li>
                <li>• Public/private conversation modes</li>
                <li>• Role-based permissions</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">✅ Real-time Typing Indicators</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Live typing status updates</li>
                <li>• Typing text preview</li>
                <li>• Auto-expiring indicators</li>
                <li>• WebSocket-based real-time sync</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">✅ Presence Status</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Online/Away/Busy/Offline status</li>
                <li>• Last seen timestamps</li>
                <li>• Automatic inactive detection</li>
                <li>• Real-time presence broadcasting</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">✅ Conversation Branching</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Create alternative conversation paths</li>
                <li>• Branch voting and scoring</li>
                <li>• Merge strategies (append/replace)</li>
                <li>• Branch metadata and tracking</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CollaborationDemo;