"""
WebSocket manager for real-time collaboration features.
"""

import logging
import asyncio
import json
from typing import Dict, Set, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from app.collaboration.service import collaboration_service
from app.collaboration.models import PresenceStatus

logger = logging.getLogger(__name__)

class CollaborationWebSocketManager:
    """Manages WebSocket connections for real-time collaboration."""
    
    def __init__(self):
        # conversation_id -> {session_id: websocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        
        # session_id -> connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # conversation_id -> {session_id: typing_info}
        self.typing_status: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Background tasks
        self.cleanup_task = None
        self._tasks_started = False
    
    def start_background_tasks(self):
        """Start background cleanup tasks."""
        if not self._tasks_started:
            try:
                if not self.cleanup_task:
                    self.cleanup_task = asyncio.create_task(self._background_cleanup())
                self._tasks_started = True
            except RuntimeError:
                # No event loop running, tasks will be started later
                pass
    
    async def connect(
        self,
        websocket: WebSocket,
        conversation_id: str,
        session_id: str,
        user_id: Optional[str] = None,
        display_name: str = "Anonymous",
        shared_conversation_id: Optional[str] = None
    ):
        """Connect a WebSocket to a conversation."""
        await websocket.accept()
        
        # Start background tasks if not already started
        if not self._tasks_started:
            self.start_background_tasks()
        
        # Initialize conversation connections if needed
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = {}
        
        # Store connection
        self.active_connections[conversation_id][session_id] = websocket
        
        # Store metadata
        self.connection_metadata[session_id] = {
            "conversation_id": conversation_id,
            "shared_conversation_id": shared_conversation_id,
            "user_id": user_id,
            "display_name": display_name,
            "connected_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # Initialize typing status
        if conversation_id not in self.typing_status:
            self.typing_status[conversation_id] = {}
        
        # Send welcome message
        await self.send_to_session(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "conversation_id": conversation_id,
            "display_name": display_name,
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "real_time_messaging",
                "typing_indicators",
                "presence_status",
                "conversation_branching",
                "collaborative_editing"
            ]
        })
        
        # Notify other participants about new connection
        await self.broadcast_to_conversation(conversation_id, {
            "type": "user_joined",
            "session_id": session_id,
            "display_name": display_name,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_session=session_id)
        
        # Send current participants list
        if shared_conversation_id:
            participants = await collaboration_service.get_participants(shared_conversation_id)
            await self.send_to_session(session_id, {
                "type": "participants_list",
                "participants": participants,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"WebSocket connected: {session_id} to conversation {conversation_id}")
    
    async def disconnect(self, session_id: str):
        """Disconnect a WebSocket session."""
        metadata = self.connection_metadata.get(session_id)
        if not metadata:
            return
        
        conversation_id = metadata["conversation_id"]
        shared_conversation_id = metadata.get("shared_conversation_id")
        display_name = metadata["display_name"]
        
        # Remove from active connections
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].pop(session_id, None)
            
            # Clean up empty conversation
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        
        # Remove typing status
        if conversation_id in self.typing_status:
            self.typing_status[conversation_id].pop(session_id, None)
        
        # Update presence in database if it's a shared conversation
        if shared_conversation_id:
            await collaboration_service.leave_shared_conversation(
                shared_conversation_id,
                session_id,
                metadata.get("user_id")
            )
        
        # Notify other participants
        await self.broadcast_to_conversation(conversation_id, {
            "type": "user_left",
            "session_id": session_id,
            "display_name": display_name,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Clean up metadata
        self.connection_metadata.pop(session_id, None)
        
        logger.info(f"WebSocket disconnected: {session_id} from conversation {conversation_id}")
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]):
        """Send a message to a specific session."""
        metadata = self.connection_metadata.get(session_id)
        if not metadata:
            return False
        
        conversation_id = metadata["conversation_id"]
        websocket = self.active_connections.get(conversation_id, {}).get(session_id)
        
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
                
                # Update last activity
                metadata["last_activity"] = datetime.utcnow().isoformat()
                
                return True
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                await self.disconnect(session_id)
                return False
        
        return False
    
    async def broadcast_to_conversation(
        self,
        conversation_id: str,
        message: Dict[str, Any],
        exclude_session: Optional[str] = None
    ):
        """Broadcast a message to all sessions in a conversation."""
        if conversation_id not in self.active_connections:
            return
        
        sessions = list(self.active_connections[conversation_id].keys())
        if exclude_session:
            sessions = [s for s in sessions if s != exclude_session]
        
        # Send to all sessions concurrently
        tasks = []
        for session_id in sessions:
            tasks.append(self.send_to_session(session_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_typing_indicator(
        self,
        session_id: str,
        is_typing: bool,
        typing_text: Optional[str] = None
    ):
        """Handle typing indicator updates."""
        metadata = self.connection_metadata.get(session_id)
        if not metadata:
            return
        
        conversation_id = metadata["conversation_id"]
        display_name = metadata["display_name"]
        user_id = metadata.get("user_id")
        
        # Update typing status in memory
        if conversation_id not in self.typing_status:
            self.typing_status[conversation_id] = {}
        
        if is_typing:
            self.typing_status[conversation_id][session_id] = {
                "display_name": display_name,
                "typing_text": typing_text,
                "started_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        else:
            self.typing_status[conversation_id].pop(session_id, None)
        
        # Update in database
        await collaboration_service.update_typing_status(
            conversation_id=conversation_id,
            session_id=session_id,
            user_id=user_id,
            display_name=display_name,
            is_typing=is_typing,
            typing_text=typing_text
        )
        
        # Broadcast to other participants
        await self.broadcast_to_conversation(conversation_id, {
            "type": "typing_indicator",
            "session_id": session_id,
            "display_name": display_name,
            "is_typing": is_typing,
            "typing_text": typing_text,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_session=session_id)
    
    async def handle_presence_update(
        self,
        session_id: str,
        status: str
    ):
        """Handle presence status updates."""
        metadata = self.connection_metadata.get(session_id)
        if not metadata:
            return
        
        shared_conversation_id = metadata.get("shared_conversation_id")
        if not shared_conversation_id:
            return
        
        # Map string to enum
        presence_status = PresenceStatus.ONLINE
        if status == "away":
            presence_status = PresenceStatus.AWAY
        elif status == "busy":
            presence_status = PresenceStatus.BUSY
        elif status == "offline":
            presence_status = PresenceStatus.OFFLINE
        
        # Update in database
        await collaboration_service.update_presence_status(
            shared_conversation_id,
            session_id,
            presence_status
        )
        
        # Broadcast to other participants
        await self.broadcast_to_conversation(metadata["conversation_id"], {
            "type": "presence_update",
            "session_id": session_id,
            "display_name": metadata["display_name"],
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_session=session_id)
    
    async def handle_message(
        self,
        session_id: str,
        message_data: Dict[str, Any]
    ):
        """Handle incoming WebSocket messages."""
        try:
            message_type = message_data.get("type")
            
            if message_type == "typing":
                await self.handle_typing_indicator(
                    session_id,
                    message_data.get("is_typing", False),
                    message_data.get("typing_text")
                )
            
            elif message_type == "presence":
                await self.handle_presence_update(
                    session_id,
                    message_data.get("status", "online")
                )
            
            elif message_type == "chat_message":
                # Handle chat messages (this would integrate with the enhanced chat service)
                await self.handle_chat_message(session_id, message_data)
            
            elif message_type == "branch_create":
                # Handle branch creation
                await self.handle_branch_creation(session_id, message_data)
            
            elif message_type == "ping":
                # Handle ping/pong for connection health
                await self.send_to_session(session_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            else:
                logger.warning(f"Unknown message type: {message_type} from session {session_id}")
        
        except Exception as e:
            logger.error(f"Error handling message from session {session_id}: {e}")
            await self.send_to_session(session_id, {
                "type": "error",
                "message": "Failed to process message",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def handle_chat_message(
        self,
        session_id: str,
        message_data: Dict[str, Any]
    ):
        """Handle chat messages in collaborative conversations."""
        metadata = self.connection_metadata.get(session_id)
        if not metadata:
            return
        
        conversation_id = metadata["conversation_id"]
        display_name = metadata["display_name"]
        
        # Broadcast the message to other participants
        await self.broadcast_to_conversation(conversation_id, {
            "type": "chat_message",
            "session_id": session_id,
            "display_name": display_name,
            "content": message_data.get("content", ""),
            "model_id": message_data.get("model_id"),
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_session=session_id)
    
    async def handle_branch_creation(
        self,
        session_id: str,
        message_data: Dict[str, Any]
    ):
        """Handle branch creation requests."""
        metadata = self.connection_metadata.get(session_id)
        if not metadata:
            return
        
        shared_conversation_id = metadata.get("shared_conversation_id")
        if not shared_conversation_id:
            return
        
        try:
            # Create branch using collaboration service
            branch = await collaboration_service.create_branch(
                shared_conversation_id=shared_conversation_id,
                parent_message_id=message_data.get("parent_message_id"),
                creator_id=metadata.get("user_id"),
                title=message_data.get("title", "New Branch"),
                description=message_data.get("description"),
                branch_type=message_data.get("branch_type", "alternative")
            )
            
            # Broadcast branch creation to all participants
            await self.broadcast_to_conversation(metadata["conversation_id"], {
                "type": "branch_created",
                "branch": branch,
                "creator": {
                    "session_id": session_id,
                    "display_name": metadata["display_name"]
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            await self.send_to_session(session_id, {
                "type": "error",
                "message": f"Failed to create branch: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get status information for a conversation."""
        connections = self.active_connections.get(conversation_id, {})
        typing_users = self.typing_status.get(conversation_id, {})
        
        participants = []
        for session_id, websocket in connections.items():
            metadata = self.connection_metadata.get(session_id, {})
            is_typing = session_id in typing_users
            
            participants.append({
                "session_id": session_id,
                "display_name": metadata.get("display_name", "Unknown"),
                "user_id": metadata.get("user_id"),
                "connected_at": metadata.get("connected_at"),
                "last_activity": metadata.get("last_activity"),
                "is_typing": is_typing,
                "typing_info": typing_users.get(session_id) if is_typing else None
            })
        
        return {
            "conversation_id": conversation_id,
            "active_connections": len(connections),
            "typing_users": len(typing_users),
            "participants": participants,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _background_cleanup(self):
        """Background task to clean up expired data."""
        while True:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                
                # Clean up expired typing indicators
                await collaboration_service.cleanup_expired_typing_indicators()
                
                # Clean up inactive participants
                await collaboration_service.cleanup_inactive_participants()
                
                # Clean up stale typing status in memory
                current_time = datetime.utcnow()
                for conversation_id in list(self.typing_status.keys()):
                    for session_id in list(self.typing_status[conversation_id].keys()):
                        typing_info = self.typing_status[conversation_id][session_id]
                        updated_at = datetime.fromisoformat(typing_info["updated_at"])
                        
                        # Remove if older than 30 seconds
                        if (current_time - updated_at).total_seconds() > 30:
                            del self.typing_status[conversation_id][session_id]
                            
                            # Notify other participants that typing stopped
                            await self.broadcast_to_conversation(conversation_id, {
                                "type": "typing_indicator",
                                "session_id": session_id,
                                "display_name": typing_info["display_name"],
                                "is_typing": False,
                                "timestamp": current_time.isoformat()
                            })
                    
                    # Clean up empty conversation typing status
                    if not self.typing_status[conversation_id]:
                        del self.typing_status[conversation_id]
                
            except Exception as e:
                logger.error(f"Error in background cleanup: {e}")

# Global WebSocket manager instance
collaboration_websocket_manager = CollaborationWebSocketManager()