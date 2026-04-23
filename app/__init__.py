"""
Application factory — the only place Flask is instantiated.
"""

import os
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

# ── Sentry error tracking (only active when SENTRY_DSN is set) ────────────────
_sentry_dsn = os.environ.get('SENTRY_DSN')
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.2,   # capture 20% of requests for performance
        send_default_pii=False,   # don't send personal info
    )
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')


def create_app(env: str = None) -> Flask:
    """
    Create and configure the Flask application.
    All wiring happens here — extensions, services, routes.
    """
    app = Flask(__name__, template_folder='templates')

    # ── Config ────────────────────────────────────────────────
    from config import config_map, ProductionConfig
    env = env or os.environ.get('FLASK_ENV', 'production')
    cfg = config_map.get(env, ProductionConfig)()
    cfg.validate()
    app.config.from_object(cfg)

    # ── Extensions ────────────────────────────────────────────
    from app.extensions import db, limiter
    db.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        # ── Database ──────────────────────────────────────────
        from app.models import Course, CoursePrerequisite, ChatLog  # noqa: F401
        db.create_all()
        logger.info("Database tables ready")

        # ── Services ──────────────────────────────────────────
        from app.services.advisor import AIAdvisor
        app.advisor = AIAdvisor()
        app.advisor.init_app(app)
        logger.info("AI Advisor initialised")

        from app.services.journey_map import JourneyMap
        app.journey_map = JourneyMap()
        app.journey_map.init_app(app)
        logger.info("Journey Map initialised")

        from app.services.recommender import CourseRecommender
        app.recommender = CourseRecommender()
        app.recommender.init_app(app)

        courses = Course.query.all()
        if courses:
            app.recommender.train(courses)
            logger.info(f"Recommender trained — {len(courses)} courses")
        else:
            logger.warning("No courses in DB — recommender not trained")

        # ── Routes (Blueprints) ───────────────────────────────
        from app.routes import register_routes
        register_routes(app)
        logger.info("Routes registered")

    return app
