# Deployment Guide

## Deploy to Render.com (Free Tier)

### Prerequisites
1. GitHub account
2. Render.com account (sign up at render.com)

### Step-by-Step Deployment

#### 1. Push Code to GitHub

```bash
cd ai-course-advisor
git init
git add .
git commit -m "Initial commit - AI Course Advisor"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-course-advisor.git
git push -u origin main
```

#### 2. Create New Web Service on Render

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name:** `ai-course-advisor`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`

#### 3. Add Environment Variables (Optional)

In Render dashboard → Environment:
```
SECRET_KEY=your-secret-key-here-change-this
```

#### 4. Deploy

Click **"Create Web Service"**

Render will:
- Clone your repo
- Install dependencies
- Start the application
- Provide you with a URL like: `https://ai-course-advisor.onrender.com`

#### 5. Initialize Database

After first deployment, you need to import course data:

**Option A: Via Render Shell**
1. Go to your service dashboard
2. Click **"Shell"** tab
3. Run: `python course_importer.py`

**Option B: Create initialization script**
Add this to your service's **Build Command**:
```bash
pip install -r requirements.txt && python course_importer.py
```

### Testing Your Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-app.onrender.com/health

# List courses
curl https://your-app.onrender.com/api/courses

# Chat with advisor
curl -X POST https://your-app.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about machine learning", "user_id": "test"}'
```

### Important Notes

**Free Tier Limitations:**
- App spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- 750 hours/month free (enough for demo)

**Database Persistence:**
- SQLite database will persist on Render's disk
- Database survives restarts but not redeployments
- For production, consider PostgreSQL upgrade

### Troubleshooting

**App won't start:**
- Check logs in Render dashboard
- Verify all dependencies in requirements.txt
- Ensure gunicorn is installed

**Database errors:**
- Run course_importer.py to populate database
- Check file permissions in instance/ directory

**Slow performance:**
- Free tier has limited resources
- Consider upgrading to Starter plan ($7/month)

### Custom Domain (Optional)

1. Buy domain (e.g., from Namecheap)
2. In Render dashboard → Settings → Custom Domain
3. Add your domain and configure DNS

---

## Alternative: Deploy to Railway.app

1. Sign up at railway.app
2. New Project → Deploy from GitHub
3. Select your repo
4. Railway auto-detects Flask
5. Add start command: `gunicorn app:app`
6. Deploy!

---

## Alternative: Deploy to PythonAnywhere

1. Sign up at pythonanywhere.com (free tier available)
2. Upload code via web interface or git clone
3. Configure WSGI file to point to app.py
4. Run course_importer.py in console
5. Reload web app

---

## Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Import courses
python course_importer.py

# Run locally
python app.py
```

Access at http://localhost:5000
