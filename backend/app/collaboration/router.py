"""
API router for real-time collaboration features.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Body
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime
from uuid import uuid4

from app.collaboration.service import collaboration_service
from app.collaboration.websocket_manager import collaboration_websocket_manager
from app.collaboration.models import CollaborationRole, PresenceStatus
from app.auth.middleware import get_optional_user, get_current_active_user
from app.auth.schemas import UserResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for API requests/responses

class CreateSharedConversationRequest(BaseModel):
    conversation_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = False
    allow_anonymous: bool = False
    max_participants: int = 10
    default_role: str = "viewer"

class JoinSharedConversationRequest(BaseModel):
    share_token: str
    display_name: Optional[str] = None

class CreateBranchRequest(BaseModel):
    parent_message_id: str
    title: str
    description: Optional[str] = None
    branch_type: str = "alternative"

class UpdatePresenceRequest(BaseModel):
    status: str  # online, away, busy, offline

class TypingIndicatorRequest(BaseModel):
    is_typing: bool
    typing_text: Optional[str] = None

# Shared Conversation Endpoints

@router.post("/conversations/{conversation_id}/share")
async def create_shared_conversation(
    conversation_id: str,
    request: CreateSharedConversationRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Create a shared conversation space for collaboration."""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required to share conversations")
        
        # Map string role to enum
        role_mapping = {
            "owner": CollaborationRole.OWNER,
            "editor": CollaborationRole.EDITOR,
            "viewer": CollaborationRole.VIEWER,
            "commenter": CollaborationRole.COMMENTER
        }
        
        default_role = role_mapping.get(request.default_role.lower(), CollaborationRole.VIEWER)
        
        shared_conversation = await collaboration_service.create_shared_conversation(
            conversation_id=conversation_id,
            owner_id=str(current_user.id),
            title=request.title,
            description=request.description,
            is_public=request.is_public,
            allow_anonymous=request.allow_anonymous,
            max_participants=request.max_participants,
            default_role=default_role
        )
        
        logger.info(f"Created shared conversation for {conversation_id} by user {current_user.username}")
        
        return {
            "success": True,
            "shared_conversation": shared_conversation,
            "message": "Conversation shared successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating shared conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create shared conversation")

@router.post("/shared/join")
async def join_shared_conversation(
    request: JoinSharedConversationRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Join a shared conversation using a share token."""
    try:
        user_id = str(current_user.id) if current_user else None
        display_name = request.display_name
        
        if not display_name and current_user:
            display_name = current_user.username
        
        session_id = str(uuid4())
        
        result = await collaboration_service.join_shared_conversation(
            share_token=request.share_token,
            user_id=user_id,
            display_name=display_name,
            session_id=session_id
        )
        
        logger.info(f"User {display_name} joined shared conversation via token {request.share_token[:8]}...")
        
        return {
            "success": True,
            "result": result,
            "message": "Successfully joined shared conversation"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error joining shared conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to join shared conversation")

@router.get("/shared/{shared_conversation_id}/participants")
async def get_participants(
    shared_conversation_id: str,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get all participants in a shared conversation."""
    try:
        participants = await collaboration_service.get_participants(shared_conversation_id)
        
        return {
            "shared_conversation_id": shared_conversation_id,
            "participants": participants,
            "total_participants": len(participants),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting participants: {e}")
        raise HTTPException(status_code=500, detail="Failed to get participants")

@router.post("/shared/{shared_conversation_id}/leave")
async def leave_shared_conversation(
    shared_conversation_id: str,
    session_id: str = Body(..., embed=True),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Leave a shared conversation."""
    try:
        user_id = str(current_user.id) if current_user else None
        
        success = await collaboration_service.leave_shared_conversation(
            shared_conversation_id=shared_conversation_id,
            session_id=session_id,
            user_id=user_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Successfully left shared conversation"
            }
        else:
            raise HTTPException(status_code=404, detail="Participant not found")
        
    except Exception as e:
        logger.error(f"Error leaving shared conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to leave shared conversation")

# Typing Indicators and Presence

@router.get("/conversations/{conversation_id}/typing")
async def get_typing_indicators(
    conversation_id: str,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get current typing indicators for a conversation."""
    try:
        indicators = await collaboration_service.get_typing_indicators(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "typing_indicators": indicators,
            "count": len(indicators),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting typing indicators: {e}")
        raise HTTPException(status_code=500, detail="Failed to get typing indicators")

@router.post("/conversations/{conversation_id}/typing")
async def update_typing_indicator(
    conversation_id: str,
    request: TypingIndicatorRequest,
    session_id: str = Query(..., description="Session ID for the typing user"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Update typing indicator for a user in a conversation."""
    try:
        user_id = str(current_user.id) if current_user else None
        display_name = current_user.username if current_user else "Anonymous"
        
        result = await collaboration_service.update_typing_status(
            conversation_id=conversation_id,
            session_id=session_id,
            user_id=user_id,
            display_name=display_name,
            is_typing=request.is_typing,
            typing_text=request.typing_text
        )
        
        return {
            "success": True,
            "typing_status": result,
            "message": "Typing indicator updated"
        }
        
    except Exception as e:
        logger.error(f"Error updating typing indicator: {e}")
        raise HTTPException(status_code=500, detail="Failed to update typing indicator")

@router.post("/shared/{shared_conversation_id}/presence")
async def update_presence_status(
    shared_conversation_id: str,
    request: UpdatePresenceRequest,
    session_id: str = Query(..., description="Session ID for the user"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Update presence status for a participant."""
    try:
        # Map string to enum
        status_mapping = {
            "online": PresenceStatus.ONLINE,
            "away": PresenceStatus.AWAY,
            "busy": PresenceStatus.BUSY,
            "offline": PresenceStatus.OFFLINE
        }
        
        status = status_mapping.get(request.status.lower(), PresenceStatus.ONLINE)
        
        success = await collaboration_service.update_presence_status(
            shared_conversation_id=shared_conversation_id,
            session_id=session_id,
            status=status
        )
        
        if success:
            return {
                "success": True,
                "status": request.status,
                "message": "Presence status updated"
            }
        else:
            raise HTTPException(status_code=404, detail="Participant not found")
        
    except Exception as e:
        logger.error(f"Error updating presence status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update presence status")

# Conversation Branching

@router.post("/shared/{shared_conversation_id}/branches")
async def create_branch(
    shared_conversation_id: str,
    request: CreateBranchRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Create a new conversation branch."""
    try:
        creator_id = str(current_user.id) if current_user else None
        
        branch = await collaboration_service.create_branch(
            shared_conversation_id=shared_conversation_id,
            parent_message_id=request.parent_message_id,
            creator_id=creator_id,
            title=request.title,
            description=request.description,
            branch_type=request.branch_type
        )
        
        logger.info(f"Created branch {branch['id']} in shared conversation {shared_conversation_id}")
        
        return {
            "success": True,
            "branch": branch,
            "message": "Branch created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to create branch")

@router.get("/shared/{shared_conversation_id}/branches")
async def get_branches(
    shared_conversation_id: str,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get all branches for a shared conversation."""
    try:
        branches = await collaboration_service.get_branches(shared_conversation_id)
        
        return {
            "shared_conversation_id": shared_conversation_id,
            "branches": branches,
            "total_branches": len(branches),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting branches: {e}")
        raise HTTPException(status_code=500, detail="Failed to get branches")

@router.post("/branches/{branch_id}/merge")
async def merge_branch(
    branch_id: str,
    merge_strategy: str = Query("append", description="Merge strategy: append, replace"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Merge a branch back into the main conversation."""
    try:
        merger_id = str(current_user.id) if current_user else None
        
        result = await collaboration_service.merge_branch(
            branch_id=branch_id,
            merger_id=merger_id,
            merge_strategy=merge_strategy
        )
        
        logger.info(f"Merged branch {branch_id} using {merge_strategy} strategy")
        
        return {
            "success": True,
            "merge_result": result,
            "message": "Branch merged successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error merging branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to merge branch")

# WebSocket Endpoint

@router.websocket("/ws/{conversation_id}")
async def collaboration_websocket(
    websocket: WebSocket,
    conversation_id: str,
    session_id: str = Query(..., description="Unique session ID"),
    shared_conversation_id: Optional[str] = Query(None, description="Shared conversation ID if applicable"),
    display_name: str = Query("Anonymous", description="Display name for the user"),
    user_id: Optional[str] = Query(None, description="User ID if authenticated")
):
    """WebSocket endpoint for real-time collaboration."""
    
    await collaboration_websocket_manager.connect(
        websocket=websocket,
        conversation_id=conversation_id,
        session_id=session_id,
        user_id=user_id,
        display_name=display_name,
        shared_conversation_id=shared_conversation_id
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle the message
            await collaboration_websocket_manager.handle_message(session_id, message_data)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        await collaboration_websocket_manager.disconnect(session_id)

# Status and Monitoring

@router.get("/conversations/{conversation_id}/status")
async def get_conversation_status(
    conversation_id: str,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get real-time status of a conversation."""
    try:
        status = await collaboration_websocket_manager.get_conversation_status(conversation_id)
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting conversation status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation status")

@router.get("/collaboration/stats")
async def get_collaboration_stats(
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get overall collaboration statistics."""
    try:
        # Get stats from WebSocket manager
        total_conversations = len(collaboration_websocket_manager.active_connections)
        total_connections = sum(
            len(sessions) for sessions in collaboration_websocket_manager.active_connections.values()
        )
        total_typing = sum(
            len(typing) for typing in collaboration_websocket_manager.typing_status.values()
        )
        
        return {
            "active_conversations": total_conversations,
            "total_connections": total_connections,
            "users_typing": total_typing,
            "features_enabled": [
                "shared_conversations",
                "real_time_typing",
                "presence_indicators",
                "conversation_branching",
                "collaborative_editing"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting collaboration stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get collaboration statistics")

@router.get("/health")
async def collaboration_health_check():
    """Health check endpoint for collaboration services."""
    try:
        # Basic health checks
        websocket_manager_healthy = collaboration_websocket_manager is not None
        service_healthy = collaboration_service is not None
        
        return {
            "status": "healthy" if websocket_manager_healthy and service_healthy else "unhealthy",
            "services": {
                "websocket_manager": "healthy" if websocket_manager_healthy else "unhealthy",
                "collaboration_service": "healthy" if service_healthy else "unhealthy"
            },
            "features": [
                "real_time_collaboration",
                "typing_indicators",
                "presence_status",
                "conversation_branching",
                "shared_conversations"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in collaboration health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }