"""
WSGI entry point — used by Gunicorn in production.
Keeps app.py clean by handling startup side-effects here.
"""

import logging
import os
from app import create_app

logger = logging.getLogger('wsgi')

app = create_app()


# ── Auto-seed on first deploy or when FORCE_RESEED=true ───────────────────────
with app.app_context():
    from app.models import Course, CoursePrerequisite

    force_reseed = os.environ.get('FORCE_RESEED', '').lower() == 'true'

    if Course.query.count() == 0 or force_reseed:
        logger.info("Auto-seeding database...")
        try:
            from app.services.importer import import_courses_from_website
            result = import_courses_from_website()
            if result.get("success"):
                logger.info(f"Auto-seed complete: {result['course_count']} courses")
                courses = Course.query.all()
                if courses:
                    app.recommender.train(courses)
                    logger.info("Recommender trained after seed")
            else:
                logger.warning(f"Auto-seed failed: {result.get('error')}")
        except Exception as e:
            logger.error(f"Auto-seed error: {e}")


# ── CLI commands ───────────────────────────────────────────────────────────────
@app.cli.command("seed-db")
def seed_db():
    """Manually import courses and retrain the recommender."""
    from app.services.importer import import_courses_from_website
    from app.models import Course

    print("Importing courses from TXST catalog...")
    result = import_courses_from_website()

    if result.get("success"):
        print(f"Imported {result['course_count']} courses. Training recommender...")
        app.recommender.train(Course.query.all())
        print("Done.")
    else:
        print(f"FAILED: {result.get('error')}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
