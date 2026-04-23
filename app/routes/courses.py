import logging
from flask import Blueprint, request, jsonify, current_app
from app.models import Course

logger = logging.getLogger('routes.courses')
bp = Blueprint('courses', __name__)


@bp.route('/api/courses', methods=['GET'])
def list_courses():
    """Return all indexed courses."""
    try:
        courses = Course.query.all()
        return jsonify({"count": len(courses), "courses": [c.to_dict() for c in courses]})
    except Exception as e:
        logger.error(f"Error listing courses: {e}")
        return jsonify({"error": "Database error"}), 500


@bp.route('/api/recommendations/courses', methods=['GET'])
def recommend_courses():
    """TF-IDF interest-based course recommendations."""
    try:
        interests = request.args.get('interests', '').strip()
        if not interests:
            return jsonify({"error": "interests query param is required"}), 400
        results = current_app.recommender.recommend_courses(interests)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Recommender error: {e}")
        return jsonify({"error": "Recommender error"}), 500
