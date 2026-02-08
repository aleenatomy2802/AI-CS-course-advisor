import logging
import re
import os
import io
import pypdf
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

    def analyze_resume(self, file_storage):
        """RAG-powered resume audit grounded in the local course database"""
        if not self.client:
            return "Resume analysis is currently offline."

        try:
            # 1. Extract text from the PDF
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_storage.read()))
            resume_text = ""
            for page in pdf_reader.pages:
                resume_text += page.extract_text() or ""

            if len(resume_text.strip()) < 50:
                return "I couldn't find enough text in that file. Please upload a digital PDF."

            # 2. RETRIEVAL: Find REAL TXST courses based on resume content
            # We search the database for courses related to what's in the resume
            resume_topics = self._extract_topics(resume_text)
            relevant_db_courses = []
            if resume_topics:
                # Search for keywords from the resume to find relevant TXST courses
                for topic in resume_topics[:5]:
                    matches = self._find_course_by_topic(topic, limit=2)
                    relevant_db_courses.extend([f"{c.name}: {c.description}" for c in matches])
            
            # Format the "Truth" context for the AI
            valid_course_context = "\n".join(list(set(relevant_db_courses))) if relevant_db_courses else "Consult the TXST CS catalog."

            # 3. GROUNDED PROMPT (Persona: Encouraging Advisor)
            prompt = f"""
            ACT AS: A supportive and encouraging Texas State University CS Academic Advisor.
            TASK: Provide a constructive audit of the student's resume and recommend REAL courses.
            
            ---
            VALID TEXAS STATE COURSES (ONLY RECOMMEND FROM THIS LIST):
            {valid_course_context}
            ---
            STUDENT RESUME TEXT:
            {resume_text}
            ---
            STRICT RULES:
            1. NEVER make up a course number. ONLY recommend courses from the 'VALID TEXAS STATE COURSES' list above.
            2. If the document is NOT a resume, politely explain what a professional CS resume should include.
            3. Tone: Be positive, encouraging, and helpful. Start with a compliment about their existing skills.
            4. Identify 2 specific technical areas for growth and recommend 2 courses from the provided list to help.
            5. FORMAT: Use plain text only. NO bolding (**), NO italics, NO markdown.
            6. Keep the response under 150 words.
            """

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            # Clean up any residual markdown formatting
            return response.text.strip().replace("**", "").replace("__", "")

        except Exception as e:
            logger.error(f"Resume RAG error: {e}")
            return "I encountered an error reading your PDF. Please ensure it's a standard digital file."

    def get_response(self, user_id, message):
        """Main advisor interface for chat"""
        if self.client:
            return self._get_gemini_response(message)
        return self._get_rule_based_response(message)

    def _get_gemini_response(self, message):
        try:
            topics = self._extract_topics(message)
            context_courses = []
            if topics:
                db_results = self._find_course_by_topic(topics[0], limit=8)
                context_courses = [f"{c.name}: {c.description}" for c in db_results]
            
            course_text = "\n".join(context_courses) if context_courses else "Refer to general TxST CS guidelines."

            system_instruction = """You are the Texas State University Computer Science Advisor.
            RULES:
            1. ONLY recommend courses listed in the 'PROVIDED CONTEXT'. 
            2. If a course isn't there, say you don't have its specific details and suggest the official catalog.
            3. NEVER use Markdown bolding (no **) or italics. Use plain text only.
            4. Keep responses under 120 words.
            5. Be encouraging but factually strict."""

            response = self.client.models.generate_content(
                model=self.model_id,
                config=types.GenerateContentConfig(system_instruction=system_instruction),
                contents=f"PROVIDED CONTEXT:\n{course_text}\n\nSTUDENT QUESTION: {message}"
            )
            
            clean_text = response.text.strip().replace("**", "").replace("__", "")
            recommended = self._find_course_by_topic(topics[0] if topics else "", limit=3)
            
            return {
                "message": clean_text,
                "courses": [self._get_course_details(c) for c in recommended]
            }

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._get_rule_based_response(message)

    def _extract_topics(self, message):
        keywords = ["python", "web", "data", "security", "ai", "software", "machine learning", "coding", "java", "c++", "cloud"]
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