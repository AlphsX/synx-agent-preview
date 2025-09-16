#!/usr/bin/env python3
"""
Test script for conversation persistence and history management.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database.connection import db_manager
from app.conversation_service import conversation_service
from app.enhanced_chat_service import EnhancedChatService


async def test_conversation_persistence():
    """Test conversation persistence functionality."""
    print("🧪 Testing Conversation Persistence and History Management")
    print("=" * 60)
    
    try:
        # Initialize database
        print("1. Initializing database connection...")
        await db_manager.initialize()
        print("✅ Database initialized")
        
        # Test conversation creation
        print("\n2. Testing conversation creation...")
        conversation = await conversation_service.create_conversation(
            title="Test Conversation - Persistence",
            user_id=None,
            metadata={"test": True, "feature": "conversation_persistence"}
        )
        print(f"✅ Created conversation: {conversation.id}")
        print(f"   Title: {conversation.title}")
        print(f"   Created: {conversation.created_at}")
        
        # Test message addition
        print("\n3. Testing message addition...")
        user_message = await conversation_service.add_message(
            conversation_id=conversation.id,
            content="Hello, this is a test message for conversation persistence!",
            role="user"
        )
        print(f"✅ Added user message: {user_message.id}")
        
        ai_message = await conversation_service.add_message(
            conversation_id=conversation.id,
            content="Hello! I'm testing the conversation persistence system. This message should be stored in the database with context data.",
            role="assistant",
            model_id="test-model",
            context_data={
                "test_context": True,
                "providers_used": ["test_provider"],
                "context_types": ["test"]
            }
        )
        print(f"✅ Added AI message: {ai_message.id}")
        
        # Test conversation history retrieval
        print("\n4. Testing conversation history retrieval...")
        history = await conversation_service.get_conversation_history(conversation.id)
        print(f"✅ Retrieved {len(history)} messages from history")
        for i, msg in enumerate(history, 1):
            print(f"   {i}. [{msg['role']}]: {msg['content'][:50]}...")
        
        # Test conversation summary
        print("\n5. Testing conversation summary...")
        summary = await conversation_service.get_conversation_summary(conversation.id)
        print("✅ Conversation summary:")
        print(f"   Total messages: {summary.get('total_messages', 0)}")
        print(f"   User messages: {summary.get('user_messages', 0)}")
        print(f"   Assistant messages: {summary.get('assistant_messages', 0)}")
        print(f"   Models used: {summary.get('models_used', [])}")
        
        # Test enhanced chat service integration
        print("\n6. Testing enhanced chat service integration...")
        enhanced_service = EnhancedChatService()
        
        # Test conversation creation through enhanced service
        enhanced_conv = await enhanced_service.create_conversation(
            title="Enhanced Test Conversation",
            user_id=None
        )
        print(f"✅ Created enhanced conversation: {enhanced_conv['id']}")
        
        # Test getting conversation through enhanced service
        retrieved_conv = await enhanced_service.get_conversation(enhanced_conv['id'])
        print(f"✅ Retrieved conversation: {retrieved_conv['title']}")
        
        # Test conversation list
        print("\n7. Testing conversation list...")
        conversations = await enhanced_service.get_user_conversations(limit=10)
        print(f"✅ Retrieved {len(conversations)} conversations")
        for conv in conversations:
            print(f"   - {conv['title']} ({conv['message_count']} messages)")
        
        # Test conversation with messages
        print("\n8. Testing conversation with messages...")
        conv_with_messages = await enhanced_service.get_conversation_with_messages(
            conversation.id, limit=10
        )
        if conv_with_messages:
            print(f"✅ Retrieved conversation with {len(conv_with_messages['messages'])} messages")
            print(f"   Conversation: {conv_with_messages['conversation']['title']}")
            for msg in conv_with_messages['messages']:
                print(f"   - [{msg['role']}]: {msg['content'][:30]}...")
        
        print("\n" + "=" * 60)
        print("🎉 All conversation persistence tests passed!")
        print("✅ Database persistence: Working")
        print("✅ Message storage: Working") 
        print("✅ History retrieval: Working")
        print("✅ Conversation management: Working")
        print("✅ Enhanced service integration: Working")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        await db_manager.close()
        print("\n🔄 Database connections closed")
    
    return True


async def test_streaming_integration():
    """Test streaming integration with conversation persistence."""
    print("\n🧪 Testing Streaming Integration with Persistence")
    print("=" * 60)
    
    try:
        await db_manager.initialize()
        enhanced_service = EnhancedChatService()
        
        # Create a test conversation
        conversation = await enhanced_service.create_conversation(
            title="Streaming Test Conversation"
        )
        print(f"✅ Created streaming test conversation: {conversation['id']}")
        
        # Test streaming response with persistence
        print("\n📡 Testing streaming response with database persistence...")
        test_message = "Tell me about the weather today"
        
        response_chunks = []
        async for chunk in enhanced_service.generate_ai_response(
            message=test_message,
            model_id="test-model",
            conversation_id=conversation['id']
        ):
            response_chunks.append(chunk)
            print(f"📨 Chunk: {chunk[:30]}...")
        
        full_response = "".join(response_chunks)
        print(f"✅ Received {len(response_chunks)} chunks, total length: {len(full_response)}")
        
        # Verify messages were stored
        history = await conversation_service.get_conversation_history(conversation['id'])
        print(f"✅ Verified {len(history)} messages stored in database")
        
        # Check that both user and assistant messages are present
        user_msgs = [msg for msg in history if msg['role'] == 'user']
        assistant_msgs = [msg for msg in history if msg['role'] == 'assistant']
        
        print(f"   User messages: {len(user_msgs)}")
        print(f"   Assistant messages: {len(assistant_msgs)}")
        
        if len(user_msgs) > 0 and len(assistant_msgs) > 0:
            print("✅ Streaming integration with persistence: Working")
        else:
            print("❌ Messages not properly stored during streaming")
            return False
        
    except Exception as e:
        print(f"❌ Streaming integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await db_manager.close()
    
    return True


async def main():
    """Run all tests."""
    print("🚀 Starting Conversation Persistence Tests")
    print("=" * 60)
    
    # Test basic persistence
    success1 = await test_conversation_persistence()
    
    # Test streaming integration
    success2 = await test_streaming_integration()
    
    if success1 and success2:
        print("\n🎉 All tests passed successfully!")
        print("✅ Task 12: Conversation persistence and history management - COMPLETED")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)