#!/usr/bin/env python3
"""
Test script to verify AI response formatting
"""

import asyncio
from app.enhanced_chat_service import EnhancedChatService

async def test_formatting():
    """Test response formatting with different queries"""
    
    service = EnhancedChatService()
    
    test_cases = [
        {
            "name": "Trending Query",
            "message": "What's trending on the internet today?",
            "model": "llama-3.1-70b-versatile"
        },
        {
            "name": "News Query",
            "message": "Latest news in AI development",
            "model": "llama-3.1-70b-versatile"
        },
        {
            "name": "Explanation Query",
            "message": "Explain how machine learning works",
            "model": "llama-3.1-70b-versatile"
        },
        {
            "name": "List Query",
            "message": "What are the top 5 programming languages in 2025?",
            "model": "llama-3.1-70b-versatile"
        }
    ]
    
    print("=" * 80)
    print("🎨 TESTING AI RESPONSE FORMATTING")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {test['name']}")
        print(f"Query: {test['message']}")
        print(f"Model: {test['model']}")
        print("=" * 80)
        print()
        
        response_parts = []
        try:
            async for chunk in service.generate_ai_response(
                message=test['message'],
                model_id=test['model'],
                conversation_history=[],
                user_context={
                    "user_id": None,
                    "username": "test_user",
                    "is_authenticated": False
                }
            ):
                response_parts.append(chunk)
                print(chunk, end="", flush=True)
            
            print("\n")
            print("-" * 80)
            
            # Analyze formatting
            full_response = ''.join(response_parts)
            
            formatting_score = 0
            feedback = []
            
            # Check for bold text
            if "**" in full_response:
                formatting_score += 20
                feedback.append("✅ Uses bold formatting")
            else:
                feedback.append("❌ Missing bold formatting")
            
            # Check for bullet points
            if "•" in full_response or "- " in full_response:
                formatting_score += 20
                feedback.append("✅ Uses bullet points")
            else:
                feedback.append("⚠️  Could use more bullet points")
            
            # Check for emojis
            emoji_count = sum(1 for char in full_response if ord(char) > 127 and ord(char) < 128512)
            if emoji_count > 0:
                formatting_score += 15
                feedback.append(f"✅ Uses emojis ({emoji_count} found)")
            else:
                feedback.append("⚠️  No emojis for visual breaks")
            
            # Check for blank lines (good spacing)
            blank_lines = full_response.count("\n\n")
            if blank_lines >= 2:
                formatting_score += 20
                feedback.append(f"✅ Good spacing ({blank_lines} blank lines)")
            else:
                feedback.append("❌ Needs more spacing between sections")
            
            # Check for numbered lists
            if any(f"{n}." in full_response for n in range(1, 6)):
                formatting_score += 15
                feedback.append("✅ Uses numbered lists")
            else:
                feedback.append("⚠️  Could use numbered lists")
            
            # Check response length
            if len(full_response) > 100:
                formatting_score += 10
                feedback.append(f"✅ Good length ({len(full_response)} chars)")
            else:
                feedback.append(f"⚠️  Response too short ({len(full_response)} chars)")
            
            print("\nFORMATTING ANALYSIS:")
            print(f"Score: {formatting_score}/100")
            for item in feedback:
                print(f"  {item}")
            
            if formatting_score >= 80:
                print("\n🎉 Excellent formatting!")
            elif formatting_score >= 60:
                print("\n👍 Good formatting, minor improvements possible")
            elif formatting_score >= 40:
                print("\n⚠️  Formatting needs improvement")
            else:
                print("\n❌ Poor formatting, needs major improvements")
            
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("FORMATTING TEST COMPLETE")
    print("=" * 80)


async def show_formatting_examples():
    """Show examples of good vs bad formatting"""
    
    print("\n" + "=" * 80)
    print("📚 FORMATTING EXAMPLES")
    print("=" * 80)
    
    print("\n❌ BAD FORMATTING:")
    print("-" * 80)
    bad_example = """Here are some trending topics: AI breakthrough in healthcare researchers announce new model, Climate summit 2025 world leaders gather, Tech giant launches new product revolutionary device announced. These are from various sources like TechCrunch and BBC News."""
    print(bad_example)
    print("\nProblems:")
    print("• No structure or hierarchy")
    print("• Hard to scan quickly")
    print("• No visual breaks")
    print("• Missing emphasis on key terms")
    
    print("\n✅ GOOD FORMATTING:")
    print("-" * 80)
    good_example = """Here's what's trending today:

**1. AI Breakthrough in Healthcare**
Researchers announce new AI model for early disease detection
📰 TechCrunch • 2 hours ago

**2. Climate Summit 2025**
World leaders gather to discuss climate action
📰 BBC News • 4 hours ago

**3. Tech Giant Launches New Product**
Revolutionary device announced at conference
📰 The Verge • 6 hours ago

Would you like more details on any of these topics?"""
    print(good_example)
    print("\nStrengths:")
    print("• Clear hierarchy with numbered items")
    print("• Bold titles for easy scanning")
    print("• Proper spacing between items")
    print("• Source attribution with emojis")
    print("• Engaging closing question")


async def main():
    """Run all formatting tests"""
    
    # Show examples first
    await show_formatting_examples()
    
    # Run actual tests
    await test_formatting()
    
    print("\n💡 TIPS FOR BETTER FORMATTING:")
    print("=" * 80)
    print("1. Always use **bold** for titles and key terms")
    print("2. Add blank lines between sections (use \\n\\n)")
    print("3. Use bullet points (•) or numbered lists for multiple items")
    print("4. Add emojis sparingly for visual breaks (📰 🔥 💡 ✨)")
    print("5. Keep paragraphs short (2-3 sentences max)")
    print("6. End with an engaging question or call-to-action")
    print("7. Use consistent formatting throughout the response")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
