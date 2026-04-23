# AI Course Advisor: Texas State University Computer Science
Intelligent Academic Guidance via Retrieval-Augmented Generation

**Live Demo:** https://cs-course-advisor.up.railway.app/


## The Advising Gap
Navigating a university degree plan is a complex and often overwhelming undertaking. For many students—particularly those who are the first in their families to attend college—understanding prerequisite chains, elective requirements, and optimal course sequencing can be a significant barrier to timely graduation. Academic advisors provide critical support, but they are frequently strained by high student-to-advisor ratios. This often leaves students to decipher dense, static course catalogs on their own. 

This project was built to bridge that gap. The AI Course Advisor is designed to democratize access to academic information, ensuring that every Computer Science student at Texas State University has continuous, instant access to accurate degree planning resources.

## Project Overview
The AI Course Advisor is a next-generation academic planning tool. Unlike traditional university portals, this system leverages Google's Gemini 2.5 Flash model and a custom Retrieval-Augmented Generation (RAG) pipeline to provide factually grounded, real-time advising. 

By systematically indexing the official Texas State Computer Science course catalog, the advisor can interpret complex student queries. From mapping out prerequisite chains to matching electives with a student's specific career interests, the system ensures that all recommendations are strictly based on actual, verified university data rather than model hallucination.

## Core Capabilities

### 1. Contextual Academic Advising (RAG Pipeline)
The system performs a semantic search of the SQL database before the AI generates a response. This grounds the language model in factual reality, ensuring course numbers, descriptions, and prerequisites are completely accurate. It handles natural language queries about course difficulty, requirements, and academic pathways.

### 2. Automated Resume Analysis
Students can upload their professional resumes in PDF format. The system extracts the text, conducts a critical audit of their current technical skills, and cross-references those skills with the university catalog to recommend specific courses that will fill their knowledge gaps.

### 3. Curriculum Dependency Visualization
Understanding how one course unlocks another is critical for graduation planning. The application utilizes NetworkX and D3.js to model the entire Computer Science curriculum as an interactive Directed Acyclic Graph. This allows students to visually identify bottleneck courses and discover the exact prerequisite chains required to reach advanced senior-level electives.

### 4. Interest-Based Course Recommendation
The application features a hybrid matching engine that combines TF-IDF vectorization with large language model reasoning. By calculating the cosine similarity between a student's stated interests and the internal course index, the system surfaces highly relevant electives tailored to their specific career goals.

## Technical Architecture

* **Language Model:** Google Gemini 2.5 Flash via the google-genai SDK.
* **Backend Framework:** Python and Flask.
* **Database:** SQLite managed via SQLAlchemy ORM.
* **Data Ingestion:** Automated web scraping of the Texas State University catalog using BeautifulSoup4.
* **Graph Logic:** NetworkX for topological sorting and prerequisite dependency mapping.
* **Frontend:** HTML, CSS, JavaScript, and D3.js.

---


## Local Development Instructions

Follow these steps to run the AI Course Advisor on a local machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/aleenatomy2802/AI-CS-course-advisor.git](https://github.com/aleenatomy2802/AI-CS-course-advisor.git)
cd AI-CS-course-advisor
```

### 2. Initialize a Virtual Environment
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a file named `.env` in the root directory and add your required API keys:
```text
GOOGLE_API_KEY="your_gemini_api_key_here"
```

### 5. Execute the Application
```bash
python app.py
```

Open a web browser and navigate to `http://127.0.0.1:5000`. 
*(Note: To populate the local database with official course data, visit the `/api/seed-database-secret-url` endpoint in your browser while the local server is running).*
