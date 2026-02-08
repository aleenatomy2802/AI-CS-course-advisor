"""
Test script to verify AI Course Advisor setup
"""

import sys

def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    try:
        import flask
        import flask_sqlalchemy
        import requests
        import bs4
        import sklearn
        import pandas
        import numpy
        import networkx
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database connection"""
    print("\nTesting database...")
    try:
        from app import app, db
        from models import Course
        
        with app.app_context():
            db.create_all()
            count = Course.query.count()
            print(f"✅ Database connected. Found {count} courses")
            
            if count == 0:
                print("⚠️  Database is empty. Run: python course_importer.py")
            return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_api():
    """Test API endpoints"""
    print("\nTesting API endpoints...")
    try:
        from app import app
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
            
            # Test home endpoint
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Home endpoint working")
            else:
                print(f"❌ Home endpoint failed: {response.status_code}")
                return False
            
            # Test chat endpoint
            response = client.post('/api/chat', json={
                'message': 'Hello',
                'user_id': 'test'
            })
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ Chat endpoint working: {data.get('message', '')[:50]}...")
            else:
                print(f"❌ Chat endpoint failed: {response.status_code}")
                return False
            
        return True
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_recommender():
    """Test recommendation engine"""
    print("\nTesting recommender...")
    try:
        from app import app
        
        with app.app_context():
            if app.recommender.vectorizer is None:
                print("⚠️  Recommender not trained. Database may be empty.")
                return True
            
            recommendations = app.recommender.recommend_courses("machine learning")
            if recommendations:
                print(f"✅ Recommender working. Found {len(recommendations)} recommendations")
            else:
                print("⚠️  Recommender returned no results (database may be empty)")
            return True
    except Exception as e:
        print(f"❌ Recommender error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("AI Course Advisor - System Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_database,
        test_api,
        test_recommender
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    print("=" * 60)
    if all(results):
        print("✅ All tests passed! System is ready.")
        print("\nNext steps:")
        print("1. If database is empty, run: python course_importer.py")
        print("2. Start the server: python app.py")
        print("3. Visit: http://localhost:5000")
    else:
        print("❌ Some tests failed. Please fix errors above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
