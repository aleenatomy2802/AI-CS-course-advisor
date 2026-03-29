"""
AI Course Advisor - Flask Application
A web-based academic advisor for CS students at Texas State University
"""

from flask import Flask
from extensions import db
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')


def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Configure the Flask app
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Use DATABASE_URL from environment (set by Render) or fall back to local SQLite
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render injects postgres:// but SQLAlchemy requires postgresql://
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    else:
        instance_path = os.path.join(basedir, 'instance')
        os.makedirs(instance_path, exist_ok=True)
        database_url = f'sqlite:///{os.path.join(instance_path, "courses.db")}'

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is not set.")
    app.config['SECRET_KEY'] = secret_key
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize app context and create tables
    with app.app_context():
        # Import models (after db initialized)
        from models import Course, CoursePrerequisite
        
        # Create database tables
        db.create_all()
        logger.info("Database tables created")
        
        # Import and initialize components
        from ai_advisor import AIAdvisor
        app.advisor = AIAdvisor()
        app.advisor.init_app(app)
        logger.info("AI Advisor initialized")
        
        from journey_map import JourneyMap
        app.journey_map = JourneyMap()
        app.journey_map.init_app(app)
        logger.info("Journey Map initialized")
        
        from recommender import CourseRecommender
        app.recommender = CourseRecommender()
        app.recommender.init_app(app)
        logger.info("Course Recommender initialized")
        
        # Initialize recommender model
        model_dir = os.path.join(basedir, 'model')
        os.makedirs(model_dir, exist_ok=True)
        recommender_model_path = os.path.join(model_dir, 'recommender_model.pkl')
        
        if not os.path.exists(recommender_model_path):
            logger.info("Training recommender model...")
            courses = Course.query.all()
            if courses:
                app.recommender.train(courses)
                logger.info(f"Recommender trained with {len(courses)} courses")
            else:
                logger.warning("No courses found - run data import first")
        else:
            app.recommender.load_model()
            logger.info("Loaded existing recommender model")
        
        # Register routes (after components initialized)
        from routes import register_routes, limiter
        limiter.init_app(app)
        register_routes(app)
        logger.info("Routes registered")
        
    return app


# Create the application instance
app = create_app()

@app.cli.command("seed-db")
def seed_db():
    """Import courses from the TXST catalog and train the recommender model."""
    from course_importer import import_courses_from_website
    from recommender import CourseRecommender
    from models import Course

    print("Importing courses...")
    result = import_courses_from_website()

    if result.get("success"):
        print(f"Imported {result['course_count']} courses. Training recommender...")
        all_courses = Course.query.all()
        rec = CourseRecommender(app)
        rec.train(all_courses)
        print("Done.")
    else:
        print(f"FAILED: {result.get('error')}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
