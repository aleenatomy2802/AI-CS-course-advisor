"""
AI Advisor service — RAG-powered chat using Google Gemini.
Single Responsibility: generate advising responses.
System prompt is loaded from prompts/advisor_system.txt (not hardcoded here).
"""

import logging
import re
import os
import io

import pypdf
from dotenv import load_dotenv

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


def _load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    path = os.path.join(base, 'prompts', 'advisor_system.txt')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"System prompt not found at {path}")
        return "You are a helpful academic advisor at Texas State University."


SYSTEM_PROMPT = _load_system_prompt()


class AIAdvisor:
    def __init__(self, app=None):
        self.app = app
        self.db = None
        self.Course = None
        self.client = None
        self.model_id = "gemini-2.5-flash"
        self._full_catalog_cache = None

        api_key = os.getenv('GOOGLE_API_KEY')
        if GEMINI_AVAILABLE and api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                logger.info(f"Gemini {self.model_id} online")
            except Exception as e:
                logger.error(f"Failed to init Gemini: {e}")

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        from app.extensions import db
        from app.models import Course
        self.db = db
        self.Course = Course

    # ── Catalog context ───────────────────────────────────────────────────

    def _get_full_catalog(self) -> str:
        if self._full_catalog_cache:
            return self._full_catalog_cache
        if not self.app:
            return "No catalog available."
        try:
            with self.app.app_context():
                all_courses = self.Course.query.all()
                if not all_courses:
                    return "No courses found in database."
                # Keep descriptions short (100 chars) to stay within token limits
                lines = [
                    f"{c.name} | {self._strip_html(c.description)[:100]}"
                    for c in all_courses
                ]
                self._full_catalog_cache = "\n".join(lines)
                logger.info(f"Catalog cached: {len(all_courses)} courses")
                return self._full_catalog_cache
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            return "Catalog loading error."

    @staticmethod
    def _strip_html(text: str) -> str:
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', '', text)
        return re.sub(r'\s+', ' ', clean).strip()

    # ── Public interface ──────────────────────────────────────────────────

    def get_response(self, user_id: str, message: str) -> dict:
        if self.client:
            return self._get_gemini_response(message)
        return self._get_rule_based_response(message)

    def analyze_resume(self, file_storage) -> str:
        if not self.client:
            return "Resume analysis is currently offline."
        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_storage.read()))
            resume_text = "".join(page.extract_text() or "" for page in pdf_reader.pages)

            if len(resume_text.strip()) < 50:
                return "I couldn't find enough text in that file. Please upload a digital PDF."

            full_catalog = self._get_full_catalog()
            prompt = f"""
ACT AS: A supportive Texas State University CS Academic Advisor doing a resume skill audit.

COMPLETE TXST CS COURSE CATALOG:
{full_catalog}

STUDENT RESUME TEXT:
{resume_text}

TASK:
1. Identify what CS skills/topics the student already has based on their resume
2. Identify 3-4 specific SKILL GAPS — areas where they could grow
3. For each gap, recommend 1-2 SPECIFIC courses from the catalog above (use exact course numbers and names)
4. If they're missing foundational courses, flag that first

RULES:
- ONLY recommend courses from the catalog above. Never invent course numbers.
- Be encouraging — start with what they're doing well
- Use plain text only. No markdown bold (**), no italics.
- Use dashes (-) for any lists
- Keep response under 200 words
"""
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text.strip().replace("**", "").replace("__", "")

        except Exception as e:
            logger.error(f"Resume analysis error: {e}")
            return "I encountered an error reading your PDF. Please ensure it's a standard digital file."

    # ── Private helpers ───────────────────────────────────────────────────

    def _get_gemini_response(self, message: str) -> dict:
        try:
            full_catalog = self._get_full_catalog()
            topics = self._extract_topics(message)
            highlighted = ""
            if topics:
                specific = []
                for topic in topics[:3]:
                    matches = self._find_courses_by_topic(topic, limit=5)
                    specific.extend(f"{c.name}: {self._strip_html(c.description)}" for c in matches)
                if specific:
                    highlighted = "\n\nMOST RELEVANT TO THIS QUESTION:\n" + "\n".join(set(specific))

            context = f"COMPLETE TXST CS COURSE CATALOG:\n{full_catalog}{highlighted}"

            response = self.client.models.generate_content(
                model=self.model_id,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                contents=f"{context}\n\n---\nSTUDENT QUESTION: {message}"
            )

            clean_text = response.text.strip().replace("**", "").replace("__", "")

            recommended = []
            if topics:
                for topic in topics[:2]:
                    recommended.extend(self._find_courses_by_topic(topic, limit=3))

            return {
                "message": clean_text,
                "courses": [self._course_to_dict(c) for c in recommended[:5]],
            }

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._get_rule_based_response(message)

    def _extract_topics(self, message: str) -> list:
        keywords = [
            "python", "web", "data", "security", "ai", "software",
            "machine learning", "coding", "java", "c++", "cloud",
            "database", "network", "operating system", "compiler",
            "algorithm", "graphics", "game", "mobile", "linux",
            "cybersecurity", "robot", "vision", "nlp", "deep learning",
        ]
        found = [k for k in keywords if k in message.lower()]
        codes = re.findall(r'CS\s?\d{4}[A-Z]?', message.upper())
        return codes + found

    def _find_courses_by_topic(self, topic: str, limit: int = 3) -> list:
        if not self.app or not topic:
            return []
        with self.app.app_context():
            return self.Course.query.filter(
                (self.Course.name.ilike(f"%{topic}%")) |
                (self.Course.description.ilike(f"%{topic}%"))
            ).limit(limit).all()

    def _course_to_dict(self, course) -> dict:
        return {
            "id":          course.id,
            "name":        course.name,
            "description": (self._strip_html(course.description) or "")[:150] + "...",
            "department":  getattr(course, 'department', 'CS'),
        }

    def _get_rule_based_response(self, message: str) -> dict:
        return {
            "message": (
                "I'm operating in basic mode right now. For CS course planning at Texas State, "
                "the typical starting sequence is CS 1428 → CS 2308 → CS 2318 / CS 3358. "
                "Check the official catalog at mycatalog.txstate.edu for full details."
            ),
            "courses": [],
        }
