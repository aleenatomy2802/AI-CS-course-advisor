# 🎓 AI Course Advisor: Texas State University CS
### *Intelligent Academic Guidance via Retrieval-Augmented Generation (RAG)*

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-Flask-red.svg)](https://flask.palletsprojects.com/)
[![Gemini 2.5 Flash](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)

## 📖 Project Overview
The **AI Course Advisor** is a next-generation academic planning tool designed for Computer Science students at Texas State University. Unlike traditional static portals, this system leverages **Google Gemini 2.5 Flash** and a custom **RAG (Retrieval-Augmented Generation)** pipeline to provide factually grounded, real-time advising.

By indexing the official Texas State CS course catalog, the advisor can interpret complex student queries—ranging from prerequisite chains to interest-based matching—ensuring all recommendations are strictly based on actual university data.



## ✨ Core Features

### 1. **RAG-Powered AI Advisor (Gemini 2.5)**
* **Contextual Grounding**: The system performs a search of the SQL database *before* the AI responds, ensuring course numbers and descriptions are 100% accurate.
* **Natural Language Understanding**: Handles conversational queries about prerequisites, course difficulty, and academic interest matching.
* **Plain-Text Clarity**: Custom system instructions ensure the AI avoids technical jargon or messy Markdown formatting for a clean user experience.

### 2. **Interactive Prerequisite Journey Map**
* **Graph-Based Planning**: Uses **NetworkX** to model the CS curriculum as a Directed Acyclic Graph (DAG).
* **Dependency Visualization**: Students can visualize "bottleneck" courses and understand long-term degree progression.
* **Prerequisite Chain Discovery**: Automatically identifies every course required to reach advanced senior-level electives.

### 3. **Smart Course Recommendation Engine**
* **Hybrid Matching**: Combines **TF-IDF vectorization** with LLM reasoning to suggest courses that align with a student's specific interests.
* **Content Similarity**: Calculates cosine similarity between student queries and the internal course index to find relevant electives.

## 🛠️ Technical Architecture

### **The "Intelligence" Stack**
* **LLM**: Google Gemini 2.5 Flash (via `google-genai` SDK).
* **Backend**: Flask (Python 3.12) with SQLAlchemy ORM.
* **Data Processing**: BeautifulSoup4 for automated scraping of the TxST Catalog.
* **Graph Logic**: NetworkX for topological sorting and prerequisite mapping.

### **Project Structure**
```text
├── app.py                 # Flask Application Factory
├── extensions.py          # Database & Extension Init
├── models.py              # Schema for Courses & Prerequisites
├── ai_advisor.py          # RAG Logic & Gemini Integration
├── recommender.py         # TF-IDF & Cosine Similarity Engine
├── journey_map.py         # NetworkX Graph Logic
└── course_importer.py     # TxST Catalog Web Scraper