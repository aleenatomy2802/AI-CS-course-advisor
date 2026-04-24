# AI CS Course Advisor — Texas State University

An AI-powered academic advising tool for TXST Computer Science students, built with a RAG (Retrieval-Augmented Generation) pipeline on top of Google Gemini 2.5 Flash.

**Live:** https://cs-course-advisor.up.railway.app/
**GitHub:** https://github.com/aleenatomy2802/AI-CS-course-advisor

> Independent student project — not affiliated with or endorsed by Texas State University.

---

## Background

Built as a solution to a real problem: as a first-generation transfer student, navigating prerequisites, elective choices, and course sequencing was genuinely difficult. Advisor appointments take weeks. The catalog is a wall of text.

Started at **Texas A&M's Tidal Hackathon**, then rebuilt with a full RAG pipeline. Presented at **Harvard WeCode 2026**.

---

## How the RAG Pipeline Works

RAG grounds a language model in factual, up-to-date data by retrieving real information before generating a response. This prevents hallucination and keeps answers accurate.

This project implements RAG in three stages:

### Stage 1 — Retrieval (Data Ingestion)

At startup, a web scraper (`app/services/importer.py`) fetches the live TXST CS course catalog from `mycatalog.txstate.edu` using `requests` and `BeautifulSoup4`. It extracts:

- Course name and number
- Full course description
- Prerequisites (parsed via regex from catalog HTML)

130 courses and their prerequisite relationships are stored in PostgreSQL via SQLAlchemy. This becomes the **ground truth** the AI is grounded in.

### Stage 2 — Augmentation (Context Injection)

On every chat request (`app/services/advisor.py`), before calling the language model:

1. The full course catalog is loaded from the database and formatted as a structured text block (cached in memory after first load)
2. The student's question is parsed for course codes and topic keywords
3. The most relevant courses are highlighted and appended as additional context
4. Everything is assembled into a single prompt:

```
SYSTEM: [advisor behavior instructions — role, rules, formatting]

COMPLETE TXST CS COURSE CATALOG:
CS 1428 Foundations of Computer Science I | ...
CS 2308 Foundations of Computer Science II | ...
...

MOST RELEVANT TO THIS QUESTION:
CS 3358 Data Structures and Algorithms: ...

STUDENT QUESTION: What are the prerequisites for CS 3358?
```

The system prompt (`prompts/advisor_system.txt`) defines the advisor's persona, degree requirements, bottleneck courses, and formatting rules — all without the model needing to know this from training data.

### Stage 3 — Generation

The augmented prompt is sent to **Google Gemini 2.5 Flash** via the `google-genai` SDK. Because the full catalog is in the context window, the model answers using only verified TXST course data. It cannot invent course numbers or prerequisites — they are either in the context or they are not.

```python
response = self.client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    contents=f"{catalog_context}\n\nSTUDENT QUESTION: {message}"
)
```

This is the core RAG loop: **Retrieve** from the database → **Augment** the prompt → **Generate** a grounded response.

---

## Features

| Feature | Description |
|---|---|
| AI Chat Advisor | Natural language Q&A grounded in the real TXST catalog |
| Prerequisite Visual Map | Interactive D3.js graph of the full CS curriculum as a directed acyclic graph |
| Resume Gap Analysis | Upload a PDF resume — Gemini identifies skill gaps and recommends specific courses |
| Course Recommendations | TF-IDF cosine similarity matches stated interests to relevant electives |
| Final Exam Schedule | Direct link to the TXST registrar's exam schedule |

---

## Architecture

```
ai-course-advisor/
├── app/
│   ├── __init__.py          # Application factory (create_app)
│   ├── extensions.py        # SQLAlchemy, Flask-Limiter
│   ├── models/
│   │   ├── course.py        # Course, CoursePrerequisite models
│   │   └── chat_log.py      # Chat analytics logging
│   ├── routes/
│   │   ├── chat.py          # POST /api/chat
│   │   ├── resume.py        # POST /api/analyze_resume
│   │   ├── courses.py       # GET /api/courses, /api/recommendations
│   │   ├── journey.py       # GET /api/journey/graph, /prerequisites
│   │   ├── admin.py         # GET /admin/logs, /admin/patch-prereqs
│   │   └── health.py        # GET /health
│   ├── services/
│   │   ├── advisor.py       # RAG pipeline + Gemini integration
│   │   ├── importer.py      # Catalog scraper (BeautifulSoup4)
│   │   ├── journey_map.py   # NetworkX prerequisite graph
│   │   └── recommender.py   # TF-IDF course recommender
│   └── templates/
│       └── index.html       # Single-page frontend (D3.js, vanilla JS)
├── prompts/
│   └── advisor_system.txt   # Gemini system prompt
├── config.py                # Environment-aware configuration
├── wsgi.py                  # Gunicorn entry point + auto-seed logic
├── Dockerfile
└── Procfile
```

**Design principles:** SOLID architecture with Flask Blueprints. Each route file handles one domain. Services contain all business logic. Models contain only data shape.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language Model | Google Gemini 2.5 Flash |
| Backend | Python 3.11, Flask 3.0 |
| Database | PostgreSQL (Neon) via SQLAlchemy |
| Graph Engine | NetworkX (DAG traversal) |
| Recommendations | scikit-learn TF-IDF + cosine similarity |
| Scraping | requests + BeautifulSoup4 |
| Frontend | HTML/CSS/JS + D3.js |
| Deployment | Docker + Railway |
| Monitoring | Google Analytics, Sentry, custom admin dashboard |

---

## Local Development

### 1. Clone and set up environment

```bash
git clone https://github.com/aleenatomy2802/AI-CS-course-advisor.git
cd AI-CS-course-advisor
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the root directory:

```
SECRET_KEY=any-random-string-for-local-dev
GOOGLE_API_KEY=your_gemini_api_key_here
ADMIN_SECRET=your_chosen_admin_password
```

No `DATABASE_URL` needed locally — the app falls back to SQLite automatically.

### 3. Run the app

```bash
python wsgi.py
```

The app auto-seeds the database with TXST course data on first run. Visit `http://127.0.0.1:5000`.



---

## Deployment

Deployed on Railway using Docker. 

---

## Planned Improvements

- Expand to other TXST departments (Biology, Business, etc.) — the importer only needs a new catalog URL
- Semester drag-and-drop planner — build your 4-year plan visually
- Student progress tracking — mark completed courses and get personalized next-step recommendations
- MATH prerequisite integration — currently only CS-to-CS prerequisite links are shown
- Rate limiting with Redis for multi-instance deployments
