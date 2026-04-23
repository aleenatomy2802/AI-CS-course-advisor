import logging
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger('routes.journey')
bp = Blueprint('journey', __name__)


@bp.route('/api/journey/graph', methods=['GET'])
def get_journey_graph():
    """Full prerequisite graph for D3.js visualisation."""
    try:
        return jsonify(current_app.journey_map.get_course_graph_data())
    except Exception as e:
        logger.error(f"Graph error: {e}")
        return jsonify({"error": "Failed to load map"}), 500


@bp.route('/api/journey/prerequisites/<int:course_id>', methods=['GET'])
def get_prerequisites(course_id):
    """Prerequisite chain for a single course."""
    try:
        return jsonify(current_app.journey_map.get_prerequisite_chain(course_id))
    except Exception as e:
        logger.error(f"Prerequisite error: {e}")
        return jsonify({"error": "Failed to load prerequisites"}), 500
