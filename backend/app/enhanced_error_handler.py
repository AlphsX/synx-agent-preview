"""
Enhanced Error Handler for Better User Experience
"""

import logging
from typing import Dict, Any, Optional
import traceback

logger = logging.getLogger(__name__)

class EnhancedErrorHandler:
    """Enhanced error handler with user-friendly messages"""
    
    @staticmethod
    def handle_api_error(error: Exception, context: str = "") -> Dict[str, Any]:
        """Handle API errors with user-friendly messages"""
        
        error_message = str(error)
        error_type = type(error).__name__
        
        # Log the full error for debugging
        logger.error(f"API Error in {context}: {error_type}: {error_message}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Create user-friendly response
        if "NoneType" in error_message and "subscriptable" in error_message:
            return {
                "error": False,  # Don't treat as error for user
                "content": "ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผลข้อมูล 😅 ให้ผมลองช่วยคุณด้วยวิธีอื่นนะครับ! 💫",
                "type": "fallback_response",
                "suggestions": [
                    "ลองถามคำถามเฉพาะเจาะจงมากขึ้น",
                    "ใช้คำศัพท์ที่ง่ายกว่า", 
                    "แบ่งคำถามออกเป็นส่วนย่อยๆ"
                ]
            }
        
        elif "timeout" in error_message.lower():
            return {
                "error": False,
                "content": "การเชื่อมต่อใช้เวลานานเกินไป 🕐 ลองถามใหม่อีกครั้งนะครับ หรือลองใช้คำถามที่สั้นกว่านี้ 😊",
                "type": "timeout_error"
            }
        
        elif "rate limit" in error_message.lower():
            return {
                "error": False,
                "content": "ขออภัยครับ ระบบกำลังยุ่งอยู่ 🚦 รอสักครู่แล้วลองใหม่นะครับ ขอบคุณสำหรับความอดทนครับ! 🙏",
                "type": "rate_limit_error"
            }
        
        elif "api key" in error_message.lower() or "unauthorized" in error_message.lower():
            return {
                "error": False,
                "content": "เกิดปัญหาการเชื่อมต่อกับระบบ 🔑 ผมจะลองตอบด้วยความรู้ที่มีแทนนะครับ! 💪",
                "type": "auth_error"
            }
        
        else:
            return {
                "error": False,
                "content": f"เกิดข้อผิดพลาดเล็กน้อย 😅 ลองถามใหม่หรือเปลี่ยนรูปแบบคำถามดูนะครับ! 🔄\n\nหากปัญหายังคงอยู่ ลองรีเฟรชหน้าเว็บดูครับ 🔄",
                "type": "general_error",
                "technical_details": error_message if logger.level <= logging.DEBUG else None
            }
    
    @staticmethod
    def create_helpful_response(query: str) -> str:
        """Create helpful response based on query content"""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["trending", "news", "latest", "current"]):
            return """ขออภัยครับ ตอนนี้ผมไม่สามารถเข้าถึงข้อมูลแบบเรียลไทม์ได้ 📡 

แต่ผมแนะนำแหล่งข้อมูลที่น่าเชื่อถือสำหรับข่าวสารล่าสุด:

📰 **ข่าวเทคโนโลยี**
• TechCrunch - ข่าวสตาร์ทอัพและเทคโนโลยี
• The Verge - รีวิวและข่าวเทค
• Wired - เทคโนโลยีและวิทยาศาสตร์

🤖 **AI & Machine Learning**
• OpenAI Blog - ข่าวจาก OpenAI
• Google AI Blog - งานวิจัย AI จาก Google
• Anthropic - ข่าวและงานวิจัย AI

🌐 **Trending Topics**
• Twitter/X Trends - หัวข้อที่กำลังฮิต
• Reddit Popular - สิ่งที่คนกำลังพูดถึง
• Google Trends - คำค้นหายอดนิยม

ลองถามคำถามเฉพาะเจาะจงมากขึ้น เช่น "อธิบายเทคโนโลยี AI ล่าสุด" แทนนะครับ! 😊"""

        elif any(word in query_lower for word in ["crypto", "bitcoin", "ethereum", "price"]):
            return """ขออภัยครับ ผมไม่สามารถให้ข้อมูลราคา cryptocurrency แบบเรียลไทม์ได้ 💰

แต่ผมแนะนำแหล่งข้อมูลที่เชื่อถือได้:

📈 **ราคาและข้อมูลตลาด**
• CoinGecko - ข้อมูลครบถ้วน
• CoinMarketCap - ราคาและสถิติ
• Binance - ราคาแบบเรียลไทม์

🔍 **การวิเคราะห์**
• TradingView - กราฟและการวิเคราะห์
• CryptoCompare - เปรียบเทียบราคา
• Messari - ข้อมูลเชิงลึก

💡 **ข้อมูลทั่วไป**
• CoinDesk - ข่าวและบทความ
• Cointelegraph - ข่าว crypto

ลองถามเกี่ยวกับเทคโนโลยี blockchain หรือแนวคิดเบื้องหลัง crypto แทนนะครับ! 🚀"""

        elif any(word in query_lower for word in ["weather", "temperature", "rain", "forecast"]):
            return """ขออภัยครับ ผมไม่สามารถให้ข้อมูลสภาพอากาศแบบเรียลไทม์ได้ 🌤️

แนะนำแหล่งข้อมูลสภาพอากาศที่เชื่อถือได้:

🌦️ **สำหรับประเทศไทย**
• กรมอุตุนิยมวิทยา - tmd.go.th
• Weather.com - ข้อมูลโลก
• AccuWeather - พยากรณ์แม่นยำ

📱 **แอปมือถือ**
• Weather (iOS/Android)
• AccuWeather App
• Weather Underground

ลองถามเกี่ยวกับสภาพภูมิอากาศหรือปรากฏการณ์ทางอุตุนิยมวิทยาแทนนะครับ! 🌍"""

        else:
            return """ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผลคำถามของคุณ 😅

💡 **เคล็ดลับการถามคำถาม:**
• ใช้ประโยคที่ชัดเจนและเฉพาะเจาะจง
• หลีกเลี่ยงคำถามที่ต้องการข้อมูลแบบเรียลไทม์
• ลองแบ่งคำถามซับซ้อนออกเป็นส่วนย่อยๆ

🚀 **ผมช่วยได้ในเรื่อง:**
• อธิบายแนวคิดและทฤษฎี
• ให้คำแนะนำและข้อเสนอแนะ
• วิเคราะห์และสรุปข้อมูล
• เขียนและแก้ไขเนื้อหา

ลองถามใหม่ด้วยรูปแบบที่ต่างออกไปนะครับ! 😊"""

# Global error handler instance
error_handler = EnhancedErrorHandler()