import logging
import re
import os
import io
import pypdf
from flask import current_app
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


# ============================================================
# SYSTEM PROMPT — This is what makes the advisor actually useful
# ============================================================
SYSTEM_PROMPT = """You are the AI Academic Advisor for the Texas State University Computer Science Department.

YOUR KNOWLEDGE: You have the COMPLETE Texas State CS course catalog provided below. This is your ground truth.

========================================
BS COMPUTER SCIENCE DEGREE REQUIREMENTS
========================================

REQUIRED CS COURSES (students MUST take ALL of these):
- CS 1428 Foundations of Computer Science I (Freshman Fall) — prereq: MATH 1315+ or test scores
- CS 2308 Foundations of Computer Science II (Freshman Spring) — prereq: CS 1428
- CS 2315 Computer Ethics (Sophomore) — prereq: CS 1428, COMM 1310 or COMM 2338, ENG 1310/1320/1321/3303, PHIL 1305 or 1320
- CS 2318 Assembly Language (Sophomore) — prereq: CS 2308, MATH 2358
- CS 3339 Computer Architecture (Sophomore/Junior) — prereq: CS 2308, CS 2318
- CS 3354 Object-Oriented Design and Programming (Junior) — prereq: CS 3358
- CS 3358 Data Structures and Algorithms (Sophomore Fall) — prereq: CS 2308, MATH 2358
- CS 3360 Computing Systems Fundamentals (Junior) — prereq: CS 2318, CS 3358
- CS 3398 Software Engineering (Junior/Senior) — prereq: CS 3354, CS 3358, CS 2315
- CS 4371 Computer System Security (Senior) — prereq: CS 3358

REQUIRED MATH COURSES:
- MATH 2358 Discrete Mathematics I (Freshman) — take early, gates CS 2318 and CS 3358
- MATH 3398 Discrete Mathematics II
- MATH 2471 Calculus I
- MATH 2472 Calculus II
- MATH 3305 Intro to Probability and Statistics

REQUIRED NON-CS COURSES:
- ENG 1310 College Writing I
- COMM 1310 Fundamentals of Human Communication (or COMM 2338)
- PHIL 1305 Critical Thinking or PHIL 1320 Ethics and Society
- ENG 3313 or ENG 3303 (Technical Writing — upper division)
- 12 hours of lab science from approved list

4 CS ADVANCED ELECTIVES (students choose 4 based on interests):
- CS 4310 Computer Networks — prereq: CS 3360
- CS 4315 Data Mining and Information Retrieval — prereq: CS 3358
- CS 4318 Compiler Construction — prereq: CS 3358
- CS 4326 Human Factors of Computer Systems — prereq: CS 3358
- CS 4328 Operating Systems — prereq: CS 3339, CS 3360
- CS 4332 Introduction to Database Systems — prereq: CS 3358
- CS 4337 Computer Vision — prereq: CS 3358
- CS 4346 Introduction to Artificial Intelligence — prereq: CS 3358
- CS 4347 Introduction to Machine Learning — prereq: CS 3358, MATH 3305
- CS 4350 Unix Systems Programming — prereq: CS 3358
- CS 4353 Graphical User Interfaces — prereq: CS 3358
- CS 4355 Algorithms and Analysis — prereq: CS 3358
- CS 4372 Digital Multimedia — prereq: CS 3358
- CS 4379D Blockchain — prereq: CS 3358
- CS 4379E Network Science — prereq: CS 3358
- CS 4379F Distributed Data Processing — prereq: CS 3354, CS 3358
- CS 4379G Data Analysis and Visualization — prereq: CS 2308
- CS 4379H Cryptography — prereq: CS 3358
- CS 4379K Autonomous Robotics — prereq: CS 3358
- CS 4379Q Recommender Systems — prereq: CS 3358
- CS 4380 Parallel Programming — prereq: CS 3339, CS 3360
- CS 4381 Practical Game Development — prereq: CS 3398
- CS 4388 Computer Graphics — prereq: CS 3358, MATH 1317/2321/2417/2471/2472

1 PROJECT COURSE (students choose 1):
- CS 4318 Compiler Construction (can double as elective)
- CS 4326 Human Factors (can double as elective)
- CS 4380 Parallel Programming (can double as elective)
- CS 4398 Software Engineering Project — prereq: CS 3398

BOTTLENECK COURSES (students should take these early — they gate many upper-level courses):
- CS 3358 Data Structures: gates 20+ electives. Take ASAP after CS 2308.
- CS 2318 Assembly Language: gates CS 3339 and CS 3360. Take with or right after CS 2308.
- MATH 2358 Discrete Math: gates CS 2318 and CS 3358. Take in Freshman year.
- CS 3360 Computing Systems: gates CS 4310, CS 4328, CS 4380. Don't delay this.

RECOMMENDED SEMESTER SEQUENCE:
Freshman Fall: CS 1428, MATH 2358, ENG 1310, COMM 1310, PHIL 1305/1320
Freshman Spring: CS 2308, MATH 2471, science, general ed
Sophomore Fall: CS 3358, CS 2318, MATH 2472, CS 2315 (if prereqs met)
Sophomore Spring: CS 3339, CS 3354, CS 3360, MATH 3398
Junior Fall: CS 3398, MATH 3305, advanced elective, ENG 3313/3303
Junior Spring: CS 4371, advanced elective, advanced elective, project course
Senior Fall: advanced elective, minor/elective courses
Senior Spring: remaining courses

========================================

YOUR JOB:
- Give SPECIFIC, ACTIONABLE advice using REAL course numbers
- When planning semesters, clearly label each course as (required), (elective), or (project)
- When students ask about interests (AI, security, web, etc.), recommend specific ELECTIVES
- When students ask about prerequisites, list ONLY the direct prerequisites for that course (one level deep). Do not trace the full chain unless the student explicitly asks for it.
- When freshmen ask about getting started: CS 1428 + MATH 2358 first semester, always
- Warn students about bottleneck courses they haven't taken yet
- Suggest realistic 4-5 course loads per semester respecting prerequisite order

FORMATTING RULES:
1. Structure responses clearly with line breaks between sections
2. For semester plans use:
   Semester Name:
   - CS XXXX Course Name (required/elective/project)
   - CS XXXX Course Name (required/elective/project)
3. No markdown bold (**) or italics. Use plain dashes (-) for lists.
4. Use blank lines between semesters or sections for readability

OTHER RULES:
1. ONLY recommend courses from the PROVIDED CATALOG. Never invent course numbers.
2. If asked about a course NOT in your catalog, say so honestly.
3. Be direct and specific. NEVER say "consult the catalog" as your primary answer — YOU are the advisor.
4. Keep responses under 300 words but be thorough enough to actually help.
5. Be encouraging but honest about workload and realistic timelines.
6. Always label electives as "(elective)" so students know they have choices.
7. If a student's plan is unrealistic or missing prerequisites, warn them clearly."""


class AIAdvisor:
    def __init__(self, app=None):
        self.app = app
        self.db = None
        self.Course = None
        self.client = None
        self.model_id = "gemini-2.5-flash"
        self._full_catalog_cache = None  # Cache the full catalog string
        
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

    # ============================================================
    # BUILD FULL CATALOG CONTEXT (cached after first call)
    # ============================================================
    def _get_full_catalog(self):
        """Load ALL courses from DB and format as context string. Cached after first call."""
        if self._full_catalog_cache:
            return self._full_catalog_cache

        if not self.app:
            return "No catalog available."

        try:
            with self.app.app_context():
                all_courses = self.Course.query.all()
                
                if not all_courses:
                    return "No courses found in database."

                lines = []
                for c in all_courses:
                    # Strip HTML from description
                    desc = self._strip_html(c.description) if c.description else "No description."
                    lines.append(f"{c.name} | {desc}")

                self._full_catalog_cache = "\n".join(lines)
                logger.info(f"📚 Catalog cached: {len(all_courses)} courses loaded for AI context")
                return self._full_catalog_cache

        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            return "Catalog loading error."

    def _strip_html(self, text):
        """Remove HTML tags from description text"""
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    # ============================================================
    # CHAT — Main advisor interface
    # ============================================================
    def get_response(self, user_id, message):
        """Main advisor interface for chat"""
        if self.client:
            return self._get_gemini_response(message)
        return self._get_rule_based_response(message)

    def _get_gemini_response(self, message):
        try:
            # Get the FULL catalog — not just 8 keyword matches
            full_catalog = self._get_full_catalog()

            # Also find specifically mentioned courses for extra emphasis
            topics = self._extract_topics(message)
            highlighted = ""
            if topics:
                specific_courses = []
                for topic in topics[:3]:
                    matches = self._find_course_by_topic(topic, limit=5)
                    specific_courses.extend([f"{c.name}: {self._strip_html(c.description)}" for c in matches])
                if specific_courses:
                    highlighted = "\n\nMOST RELEVANT TO THIS QUESTION:\n" + "\n".join(list(set(specific_courses)))

            # Build the full context
            context = f"COMPLETE TXST CS COURSE CATALOG:\n{full_catalog}{highlighted}"

            response = self.client.models.generate_content(
                model=self.model_id,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                contents=f"{context}\n\n---\nSTUDENT QUESTION: {message}"
            )
            
            clean_text = response.text.strip().replace("**", "").replace("__", "")
            
            # Find recommended courses to return as structured data
            recommended = []
            if topics:
                for topic in topics[:2]:
                    recommended.extend(self._find_course_by_topic(topic, limit=3))
            
            return {
                "message": clean_text,
                "courses": [self._get_course_details(c) for c in recommended[:5]]
            }

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._get_rule_based_response(message)

    # ============================================================
    # RESUME ANALYSIS
    # ============================================================
    def analyze_resume(self, file_storage):
        """RAG-powered resume audit grounded in the FULL course catalog"""
        if not self.client:
            return "Resume analysis is currently offline."

        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_storage.read()))
            resume_text = ""
            for page in pdf_reader.pages:
                resume_text += page.extract_text() or ""

            if len(resume_text.strip()) < 50:
                return "I couldn't find enough text in that file. Please upload a digital PDF."

            # Use FULL catalog for resume analysis too
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
            logger.error(f"Resume RAG error: {e}")
            return "I encountered an error reading your PDF. Please ensure it's a standard digital file."

    # ============================================================
    # HELPERS
    # ============================================================
    def _extract_topics(self, message):
        """Extract course codes and keywords from user message"""
        keywords = [
            "python", "web", "data", "security", "ai", "software", 
            "machine learning", "coding", "java", "c++", "cloud",
            "database", "network", "operating system", "compiler",
            "algorithm", "graphics", "game", "mobile", "linux",
            "cybersecurity", "robot", "vision", "nlp", "deep learning"
        ]
        found = [k for k in keywords if k in message.lower()]
        codes = re.findall(r'CS\s?\d{4}[A-Z]?', message.upper())
        return codes + found

    def _find_course_by_topic(self, topic, limit=3):
        if not self.app or not topic:
            return []
        with self.app.app_context():
            return self.Course.query.filter(
                (self.Course.name.ilike(f"%{topic}%")) | 
                (self.Course.description.ilike(f"%{topic}%"))
            ).limit(limit).all()

    def _get_course_details(self, course):
        return {
            "id": course.id,
            "name": course.name,
            "description": (self._strip_html(course.description) or "")[:150] + "...",
            "department": getattr(course, 'department', 'CS')
        }

    def _get_rule_based_response(self, message):
        return {
            "message": "I'm operating in basic mode right now. For CS course planning at Texas State, the typical starting sequence is CS 1428 (Foundations of CS) then CS 2308 (Foundations of CS II) then CS 2318 (Discrete Structures). Check the official catalog at mycatalog.txstate.edu for full details.",
            "courses": []
        }


def init_advisor(app):
    return AIAdvisor(app)

# import logging
# import re
# import os
# import io
# import pypdf
# from flask import current_app
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# logging.basicConfig(level=logging.INFO, 
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger('ai_advisor')

# try:
#     from google import genai
#     from google.genai import types
#     GEMINI_AVAILABLE = True
# except ImportError:
#     GEMINI_AVAILABLE = False
#     logger.warning("Google GenAI not installed. Run: pip install google-genai")

# class AIAdvisor:
#     def __init__(self, app=None):
#         self.app = app
#         self.db = None
#         self.Course = None
#         self.client = None
#         self.model_id = "gemini-2.5-flash" 
        
#         api_key = os.getenv('GOOGLE_API_KEY')
#         if GEMINI_AVAILABLE and api_key:
#             try:
#                 self.client = genai.Client(api_key=api_key)
#                 logger.info(f"🚀 Gemini {self.model_id} online")
#             except Exception as e:
#                 logger.error(f"Failed to init Gemini: {e}")
#                 self.client = None

#         if app is not None:
#             self.init_app(app)

#     def init_app(self, app):
#         self.app = app
#         from extensions import db
#         from models import Course
#         self.db = db
#         self.Course = Course

#     def analyze_resume(self, file_storage):
#         """RAG-powered resume audit grounded in the local course database"""
#         if not self.client:
#             return "Resume analysis is currently offline."

#         try:
#             # 1. Extract text from the PDF
#             pdf_reader = pypdf.PdfReader(io.BytesIO(file_storage.read()))
#             resume_text = ""
#             for page in pdf_reader.pages:
#                 resume_text += page.extract_text() or ""

#             if len(resume_text.strip()) < 50:
#                 return "I couldn't find enough text in that file. Please upload a digital PDF."

#             # 2. RETRIEVAL: Find REAL TXST courses based on resume content
#             # We search the database for courses related to what's in the resume
#             resume_topics = self._extract_topics(resume_text)
#             relevant_db_courses = []
#             if resume_topics:
#                 # Search for keywords from the resume to find relevant TXST courses
#                 for topic in resume_topics[:5]:
#                     matches = self._find_course_by_topic(topic, limit=2)
#                     relevant_db_courses.extend([f"{c.name}: {c.description}" for c in matches])
            
#             # Format the "Truth" context for the AI
#             valid_course_context = "\n".join(list(set(relevant_db_courses))) if relevant_db_courses else "Consult the TXST CS catalog."

#             # 3. GROUNDED PROMPT (Persona: Encouraging Advisor)
#             prompt = f"""
#             ACT AS: A supportive and encouraging Texas State University CS Academic Advisor.
#             TASK: Provide a constructive audit of the student's resume and recommend REAL courses.
            
#             ---
#             VALID TEXAS STATE COURSES (ONLY RECOMMEND FROM THIS LIST):
#             {valid_course_context}
#             ---
#             STUDENT RESUME TEXT:
#             {resume_text}
#             ---
#             STRICT RULES:
#             1. NEVER make up a course number. ONLY recommend courses from the 'VALID TEXAS STATE COURSES' list above.
#             2. If the document is NOT a resume, politely explain what a professional CS resume should include.
#             3. Tone: Be positive, encouraging, and helpful. Start with a compliment about their existing skills.
#             4. Identify 2 specific technical areas for growth and recommend 2 courses from the provided list to help.
#             5. FORMAT: Use plain text only. NO bolding (**), NO italics, NO markdown.
#             6. Keep the response under 150 words.
#             """

#             response = self.client.models.generate_content(
#                 model=self.model_id,
#                 contents=prompt
#             )
            
#             # Clean up any residual markdown formatting
#             return response.text.strip().replace("**", "").replace("__", "")

#         except Exception as e:
#             logger.error(f"Resume RAG error: {e}")
#             return "I encountered an error reading your PDF. Please ensure it's a standard digital file."

#     def get_response(self, user_id, message):
#         """Main advisor interface for chat"""
#         if self.client:
#             return self._get_gemini_response(message)
#         return self._get_rule_based_response(message)

#     def _get_gemini_response(self, message):
#         try:
#             topics = self._extract_topics(message)
#             context_courses = []
#             if topics:
#                 db_results = self._find_course_by_topic(topics[0], limit=8)
#                 context_courses = [f"{c.name}: {c.description}" for c in db_results]
            
#             course_text = "\n".join(context_courses) if context_courses else "Refer to general TxST CS guidelines."

#             system_instruction = """You are the Texas State University Computer Science Advisor.
#             RULES:
#             1. ONLY recommend courses listed in the 'PROVIDED CONTEXT'. 
#             2. If a course isn't there, say you don't have its specific details and suggest the official catalog.
#             3. NEVER use Markdown bolding (no **) or italics. Use plain text only.
#             4. Keep responses under 120 words.
#             5. Be encouraging but factually strict."""

#             response = self.client.models.generate_content(
#                 model=self.model_id,
#                 config=types.GenerateContentConfig(system_instruction=system_instruction),
#                 contents=f"PROVIDED CONTEXT:\n{course_text}\n\nSTUDENT QUESTION: {message}"
#             )
            
#             clean_text = response.text.strip().replace("**", "").replace("__", "")
#             recommended = self._find_course_by_topic(topics[0] if topics else "", limit=3)
            
#             return {
#                 "message": clean_text,
#                 "courses": [self._get_course_details(c) for c in recommended]
#             }

#         except Exception as e:
#             logger.error(f"Gemini error: {e}")
#             return self._get_rule_based_response(message)

#     def _extract_topics(self, message):
#         keywords = ["python", "web", "data", "security", "ai", "software", "machine learning", "coding", "java", "c++", "cloud"]
#         found = [k for k in keywords if k in message.lower()]
#         codes = re.findall(r'CS\s?\d{4}', message.upper())
#         return codes + found

#     def _find_course_by_topic(self, topic, limit=3):
#         if not self.app or not topic: return []
#         with self.app.app_context():
#             return self.Course.query.filter(
#                 (self.Course.name.ilike(f"%{topic}%")) | 
#                 (self.Course.description.ilike(f"%{topic}%"))
#             ).limit(limit).all()

#     def _get_course_details(self, course):
#         return {
#             "id": course.id,
#             "name": course.name,
#             "description": course.description[:150] + "...",
#             "department": getattr(course, 'department', 'CS')
#         }

#     def _get_rule_based_response(self, message):
#         return {
#             "message": "I'm operating in basic mode. Please check the Texas State CS catalog for specific course numbers like CS 1428 or CS 2308.",
#             "courses": []
#         }

# def init_advisor(app):
#     return AIAdvisor(app)