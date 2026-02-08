# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/ai-course-advisor.git
cd ai-course-advisor
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Import Course Data
```bash
python course_importer.py
```

Expected output:
```
INFO - Found 123 course blocks
INFO - Processed: CS 1428
...
✅ Imported 123 courses, 45 prerequisites
```

### 3. Run the App
```bash
python app.py
```

App runs at: `http://localhost:5000`

### 4. Test It Works
```bash
python test_system.py
```

All tests should pass ✅

### 5. Try the API

**Chat with advisor:**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to learn machine learning", "user_id": "test"}'
```

**Get course recommendations:**
```bash
curl "http://localhost:5000/api/recommendations/courses?interests=data science"
```

**View all courses:**
```bash
curl http://localhost:5000/api/courses
```

## 📝 For Your Resume

Add this to your resume:
```
AI Course Advisor - Texas A&M TIDAL Hackathon                    Mar 2025
• Developed Flask REST API serving ML-powered course recommendations using 
  TF-IDF and cosine similarity (Live Demo: [URL] | GitHub: [URL])
• Implemented web scraping pipeline with BeautifulSoup to extract 123+ courses 
  and prerequisite relationships from Texas State CS catalog
• Built NetworkX graph visualization for course dependency mapping and prerequisite 
  chain analysis
```

## 🌐 Deploy to Internet

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

**Fastest deployment:**
1. Push to GitHub
2. Go to render.com
3. New Web Service → Connect repo
4. Deploy!

Your live URL: `https://ai-course-advisor.onrender.com`

## 📚 Prepare for Interviews

Read [INTERVIEW_PREP.md](INTERVIEW_PREP.md) for:
- Technical deep-dive questions & answers
- Architecture explanations
- Code walkthrough talking points
- Common interview questions

## 🐛 Troubleshooting

**Issue:** `ModuleNotFoundError: No module named 'flask'`
**Fix:** Activate virtual environment and install requirements

**Issue:** Database empty / no courses
**Fix:** Run `python course_importer.py`

**Issue:** Recommender not working
**Fix:** Ensure database has courses, model will auto-train

## 📖 Project Structure

```
ai-course-advisor/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── routes.py              # API endpoints
├── ai_advisor.py          # Chat advisor logic
├── recommender.py         # TF-IDF recommendation engine
├── journey_map.py         # NetworkX graph generation
├── course_importer.py     # Web scraping script
├── test_system.py         # Test suite
├── requirements.txt       # Python dependencies
├── README.md              # Full documentation
├── DEPLOYMENT.md          # Deployment guide
├── INTERVIEW_PREP.md      # Interview preparation
└── QUICKSTART.md          # This file
```

## ✅ Verification Checklist

Before showing to recruiters:

- [ ] All tests pass (`python test_system.py`)
- [ ] Database populated (123+ courses)
- [ ] App runs locally without errors
- [ ] Deployed to internet (Render/Railway)
- [ ] GitHub repo is public
- [ ] README has live demo URL
- [ ] Can explain how TF-IDF works
- [ ] Can explain Flask architecture
- [ ] Can explain NetworkX usage

## 🎯 Next Steps

1. **Deploy it** - Get a live URL to share
2. **Add to resume** - Use provided text above
3. **Practice demo** - Show API in action during interviews
4. **Read interview prep** - Be ready for technical questions

---

**You built something real. Now show it off!** 🚀
