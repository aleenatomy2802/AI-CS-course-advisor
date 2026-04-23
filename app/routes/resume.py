import logging
from flask import Blueprint, request, jsonify, current_app
from app.extensions import limiter

logger = logging.getLogger('routes.resume')
bp = Blueprint('resume', __name__)


@bp.route('/api/analyze_resume', methods=['POST'])
@limiter.limit("5 per minute;20 per hour")
def analyze_resume():
    """PDF resume analysis — returns skill gap mapped to TXST courses."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        analysis = current_app.advisor.analyze_resume(file)
        return jsonify({"message": analysis})

    except Exception as e:
        logger.error(f"Resume analysis error: {e}")
        return jsonify({"error": "Failed to analyse document"}), 500
