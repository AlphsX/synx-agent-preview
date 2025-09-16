"""
Streaming response system for real-time chat with SSE and WebSocket support.
Provides response chunking, buffering, and connection management.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime
from fastapi import WebSocket
from fastapi.responses import StreamingResponse
import time

logger = logging.getLogger(__name__)


class StreamingManager:
    """
    Manages streaming responses with buffering, chunking, and error recovery.
    Supports both Server-Sent Events (SSE) and WebSocket protocols.
    """
    
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.buffer_size = 1024  # Buffer size for chunking
        self.chunk_delay = 0.01  # Delay between chunks for smooth streaming
        
    def create_sse_stream(
        self, 
        stream_id: str, 
        generator: AsyncGenerator[str, None],
        metadata: Dict[str, Any] = None
    ) -> StreamingResponse:
        """
        Create Server-Sent Events stream from async generator.
        
        Args:
            stream_id: Unique identifier for the stream
            generator: Async generator yielding content chunks
            metadata: Additional metadata for the stream
            
        Returns:
            StreamingResponse configured for SSE
        """
        
        async def sse_generator():
            try:
                # Register stream
                self.active_streams[stream_id] = {
                    "type": "sse",
                    "start_time": datetime.now(),
                    "metadata": metadata or {},
                    "chunks_sent": 0,
                    "bytes_sent": 0
                }
                
                # Send initial connection event
                yield self._format_sse_event("connected", {
                    "stream_id": stream_id,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": metadata
                })
                
                # Buffer for smooth streaming
                buffer = ""
                
                async for chunk in generator:
                    if chunk:
                        buffer += chunk
                        
                        # Send buffer when it reaches size limit or contains complete sentences
                        if (len(buffer) >= self.buffer_size or 
                            buffer.endswith(('.', '!', '?', '\n'))):
                            
                            yield self._format_sse_event("content", {
                                "content": buffer,
                                "stream_id": stream_id,
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # Update stream stats
                            stream_info = self.active_streams.get(stream_id, {})
                            stream_info["chunks_sent"] = stream_info.get("chunks_sent", 0) + 1
                            stream_info["bytes_sent"] = stream_info.get("bytes_sent", 0) + len(buffer)
                            
                            buffer = ""
                            await asyncio.sleep(self.chunk_delay)
                
                # Send any remaining buffer content
                if buffer:
                    yield self._format_sse_event("content", {
                        "content": buffer,
                        "stream_id": stream_id,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Send completion event
                stream_info = self.active_streams.get(stream_id, {})
                yield self._format_sse_event("done", {
                    "stream_id": stream_id,
                    "timestamp": datetime.now().isoformat(),
                    "stats": {
                        "chunks_sent": stream_info.get("chunks_sent", 0),
                        "bytes_sent": stream_info.get("bytes_sent", 0),
                        "duration": (datetime.now() - stream_info.get("start_time", datetime.now())).total_seconds()
                    }
                })
                
            except Exception as e:
                logger.error(f"SSE stream error for {stream_id}: {e}")
                yield self._format_sse_event("error", {
                    "stream_id": stream_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            finally:
                # Clean up stream
                if stream_id in self.active_streams:
                    del self.active_streams[stream_id]
        
        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
    async def stream_to_websocket(
        self,
        websocket: WebSocket,
        stream_id: str,
        generator: AsyncGenerator[str, None],
        metadata: Dict[str, Any] = None
    ):
        """
        Stream content to WebSocket with chunking and error handling.
        
        Args:
            websocket: WebSocket connection
            stream_id: Unique identifier for the stream
            generator: Async generator yielding content chunks
            metadata: Additional metadata for the stream
        """
        try:
            # Register stream
            self.active_streams[stream_id] = {
                "type": "websocket",
                "start_time": datetime.now(),
                "metadata": metadata or {},
                "chunks_sent": 0,
                "bytes_sent": 0
            }
            
            # Send initial message
            await websocket.send_text(json.dumps({
                "type": "stream_start",
                "stream_id": stream_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata
            }))
            
            # Buffer for smooth streaming
            buffer = ""
            
            async for chunk in generator:
                if chunk:
                    buffer += chunk
                    
                    # Send buffer when it reaches size limit or contains complete words
                    if (len(buffer) >= self.buffer_size or 
                        buffer.endswith((' ', '.', '!', '?', '\n'))):
                        
                        await websocket.send_text(json.dumps({
                            "type": "content",
                            "content": buffer,
                            "stream_id": stream_id,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        # Update stream stats
                        stream_info = self.active_streams.get(stream_id, {})
                        stream_info["chunks_sent"] = stream_info.get("chunks_sent", 0) + 1
                        stream_info["bytes_sent"] = stream_info.get("bytes_sent", 0) + len(buffer)
                        
                        buffer = ""
                        await asyncio.sleep(self.chunk_delay)
            
            # Send any remaining buffer content
            if buffer:
                await websocket.send_text(json.dumps({
                    "type": "content",
                    "content": buffer,
                    "stream_id": stream_id,
                    "timestamp": datetime.now().isoformat()
                }))
            
            # Send completion message
            stream_info = self.active_streams.get(stream_id, {})
            await websocket.send_text(json.dumps({
                "type": "stream_complete",
                "stream_id": stream_id,
                "timestamp": datetime.now().isoformat(),
                "stats": {
                    "chunks_sent": stream_info.get("chunks_sent", 0),
                    "bytes_sent": stream_info.get("bytes_sent", 0),
                    "duration": (datetime.now() - stream_info.get("start_time", datetime.now())).total_seconds()
                }
            }))
            
        except Exception as e:
            logger.error(f"WebSocket stream error for {stream_id}: {e}")
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "stream_id": stream_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
            except:
                pass  # Connection might be closed
        finally:
            # Clean up stream
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
    
    def _format_sse_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    
    def get_active_streams(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active streams"""
        return self.active_streams.copy()
    
    def get_stream_stats(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific stream"""
        return self.active_streams.get(stream_id)
    
    async def close_stream(self, stream_id: str):
        """Force close a stream"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
            logger.info(f"Closed stream: {stream_id}")


class ResponseBuffer:
    """
    Buffer for managing response chunks with intelligent splitting.
    Ensures smooth streaming by buffering content and releasing it at optimal points.
    """
    
    def __init__(self, max_size: int = 512, sentence_endings: List[str] = None):
        self.max_size = max_size
        self.sentence_endings = sentence_endings or ['.', '!', '?', '\n']
        self.buffer = ""
        self.word_buffer = ""
    
    def add_content(self, content: str) -> List[str]:
        """
        Add content to buffer and return chunks ready for streaming.
        
        Args:
            content: Content to add to buffer
            
        Returns:
            List of chunks ready to be sent
        """
        chunks_to_send = []
        self.buffer += content
        
        # Check if we should release buffer content
        while self.buffer:
            # If buffer is too large, find a good break point
            if len(self.buffer) >= self.max_size:
                break_point = self._find_break_point()
                if break_point > 0:
                    chunk = self.buffer[:break_point]
                    chunks_to_send.append(chunk)
                    self.buffer = self.buffer[break_point:].lstrip()
                else:
                    # No good break point, send partial buffer
                    chunk = self.buffer[:self.max_size]
                    chunks_to_send.append(chunk)
                    self.buffer = self.buffer[self.max_size:]
            
            # Check for sentence endings
            elif any(self.buffer.endswith(ending) for ending in self.sentence_endings):
                chunks_to_send.append(self.buffer)
                self.buffer = ""
                break
            
            # Check for word boundaries
            elif self.buffer.endswith(' ') and len(self.buffer) > 50:
                chunks_to_send.append(self.buffer)
                self.buffer = ""
                break
            
            else:
                break  # Wait for more content
        
        return chunks_to_send
    
    def flush(self) -> str:
        """Flush remaining buffer content"""
        content = self.buffer
        self.buffer = ""
        return content
    
    def _find_break_point(self) -> int:
        """Find optimal break point in buffer"""
        # Look for sentence endings first
        for ending in self.sentence_endings:
            pos = self.buffer.rfind(ending, 0, self.max_size)
            if pos > 0:
                return pos + len(ending)
        
        # Look for word boundaries
        pos = self.buffer.rfind(' ', 0, self.max_size)
        if pos > 0:
            return pos + 1
        
        # No good break point found
        return 0


# Global streaming manager instance
streaming_manager = StreamingManager()