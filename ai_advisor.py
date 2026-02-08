import logging
import re
import os
from flask import current_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ai_advisor')

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google GenAI not installed. Run: pip install google-genai")

class AIAdvisor:
    def __init__(self, app=None):
        self.app = app
        self.db = None
        self.Course = None
        self.client = None
        self.model_id = "gemini-2.5-flash" 
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if GEMINI_AVAILABLE and api_key:
            try:
                # Initialize modern client
                self.client = genai.Client(api_key=api_key)
                logger.info(f"🚀 Gemini {self.model_id} online")
            except Exception as e:
                logger.error(f"Failed to init Gemini: {e}")
                self.client = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        from extensions import db
        from models import Course
        self.db = db
        self.Course = Course

    def get_response(self, user_id, message):
        """Main advisor interface"""
        if self.client:
            return self._get_gemini_response(message)
        return self._get_rule_based_response(message)

    def _get_gemini_response(self, message):
        try:
            # 1. SEARCH DATABASE FIRST (Grounding)
            topics = self._extract_topics(message)
            context_courses = []
            if topics:
                # Get more results to give AI plenty of real context
                db_results = self._find_course_by_topic(topics[0], limit=8)
                context_courses = [f"{c.name}: {c.description}" for c in db_results]
            
            course_text = "\n".join(context_courses) if context_courses else "Refer to general TxST CS guidelines."

            # 2. SYSTEM INSTRUCTIONS (Strict Behavior)
            system_instruction = """You are the Texas State University Computer Science Advisor.
            RULES:
            1. ONLY recommend courses listed in the 'PROVIDED CONTEXT'. 
            2. If a course isn't there, say you don't have its specific details and suggest the official catalog.
            3. NEVER use Markdown bolding (no **) or italics. Use plain text only.
            4. Keep responses under 120 words.
            5. Be encouraging but factually strict."""

            # 3. CALL GEMINI
            response = self.client.models.generate_content(
                model=self.model_id,
                config=types.GenerateContentConfig(system_instruction=system_instruction),
                contents=f"PROVIDED CONTEXT:\n{course_text}\n\nSTUDENT QUESTION: {message}"
            )
            
            # Final clean-up of any bolding the AI might have missed
            clean_text = response.text.strip().replace("**", "").replace("__", "")

            # 4. PACKAGE DATA
            recommended = self._find_course_by_topic(topics[0] if topics else "", limit=3)
            return {
                "message": clean_text,
                "courses": [self._get_course_details(c) for c in recommended]
            }

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._get_rule_based_response(message)

    def _extract_topics(self, message):
        keywords = ["python", "web", "data", "security", "ai", "software", "machine learning", "coding"]
        found = [k for k in keywords if k in message.lower()]
        codes = re.findall(r'CS\s?\d{4}', message.upper())
        return codes + found

    def _find_course_by_topic(self, topic, limit=3):
        if not self.app or not topic: return []
        with self.app.app_context():
            return self.Course.query.filter(
                (self.Course.name.ilike(f"%{topic}%")) | 
                (self.Course.description.ilike(f"%{topic}%"))
            ).limit(limit).all()

    def _get_course_details(self, course):
        return {
            "id": course.id,
            "name": course.name,
            "description": course.description[:150] + "...",
            "department": getattr(course, 'department', 'CS')
        }

    def _get_rule_based_response(self, message):
        return {
            "message": "I'm operating in basic mode. Please check the Texas State CS catalog for specific course numbers like CS 1428 or CS 2308.",
            "courses": []
        }

def init_advisor(app):
    return AIAdvisor(app)