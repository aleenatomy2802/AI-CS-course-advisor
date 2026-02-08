#!/bin/bash

# AI Course Advisor - Git Setup Script

echo "🚀 Setting up Git repository for AI Course Advisor"
echo "=================================================="

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing Git repository..."
    git init
    git branch -M main
else
    echo "✅ Git repository already initialized"
fi

# Add all files
echo "📦 Adding files to Git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit - AI Course Advisor

Features:
- Flask REST API with 12+ endpoints
- TF-IDF-based course recommendation engine
- NetworkX graph for prerequisite visualization
- Web scraping pipeline for Texas State CS catalog
- AI-powered academic advisor chatbot
- 123+ courses with prerequisite relationships

Tech stack: Flask, SQLAlchemy, scikit-learn, NetworkX, BeautifulSoup"

echo ""
echo "✅ Git repository initialized!"
echo ""
echo "Next steps:"
echo "1. Create repository on GitHub"
echo "2. Run these commands:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/ai-course-advisor.git"
echo "   git push -u origin main"
echo ""
echo "3. Deploy to Render.com (see DEPLOYMENT.md)"
echo ""
echo "=================================================="
