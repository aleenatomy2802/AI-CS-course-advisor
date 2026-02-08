"""
API Routes for AI Course Advisor
"""

from flask import render_template, request, jsonify, current_app
from models import Course
import logging

logger = logging.getLogger('routes')


def register_routes(app):
    """Register all application routes"""
    
    @app.route('/')
    def home():
        return render_template('index.html')
    @app.route('/api/courses', methods=['GET'])
    def list_courses():
        """List all courses"""
        try:
            courses = Course.query.all()
            return jsonify({
                "count": len(courses),
                "courses": [course.to_dict() for course in courses]
            })
        except Exception as e:
            logger.error(f"Error listing courses: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/career_paths', methods=['GET'])
    def get_career_paths():
        """Get available career paths"""
        try:
            paths = app.advisor.get_career_paths()
            return jsonify(paths)
        except Exception as e:
            logger.error(f"Error getting career paths: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/career_advice/<path:career_path>', methods=['GET'])
    def get_career_advice(career_path):
        """Get advice for a specific career path"""
        try:
            interests = request.args.get('interests')
            advice = app.advisor.get_conversational_advice(career_path, interests)
            return jsonify(advice)
        except Exception as e:
            logger.error(f"Error getting career advice: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/suggest_careers', methods=['POST'])
    def suggest_careers():
        """Suggest careers based on interests"""
        try:
            data = request.get_json()
            interests = data.get('interests', '')
            suggestions = app.advisor.suggest_career_paths_from_interests(interests)
            return jsonify(suggestions)
        except Exception as e:
            logger.error(f"Error suggesting careers: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Handle chat interactions with AI advisor"""
        try:
            data = request.get_json()
            message = data.get('message', '')
            user_id = data.get('user_id', 'default')
            
            if not message:
                return jsonify({"error": "Message is required"}), 400
            
            response = app.advisor.get_response(user_id, message)
            return jsonify(response)
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/journey/graph', methods=['GET'])
    def get_journey_graph():
        """Get course graph data for visualization"""
        try:
            graph_data = app.journey_map.get_course_graph_data()
            return jsonify(graph_data)
        except Exception as e:
            logger.error(f"Error getting journey graph: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/journey/prerequisites/<int:course_id>', methods=['GET'])
    def get_prerequisites(course_id):
        """Get prerequisite chain for a specific course"""
        try:
            chain_data = app.journey_map.get_prerequisite_chain(course_id)
            return jsonify(chain_data)
        except Exception as e:
            logger.error(f"Error getting prerequisites: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/journey/pathways', methods=['GET'])
    def get_career_pathways():
        """Get career pathways data for visualization"""
        try:
            pathways = app.journey_map.get_career_pathways()
            return jsonify(pathways)
        except Exception as e:
            logger.error(f"Error getting pathways: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/recommendations/courses', methods=['GET'])
    def recommend_courses():
        """Get course recommendations based on interests"""
        try:
            interests = request.args.get('interests', '')
            if not interests:
                return jsonify({"error": "Interests parameter is required"}), 400
            
            recommendations = app.recommender.recommend_courses(interests)
            return jsonify(recommendations)
        except Exception as e:
            logger.error(f"Error recommending courses: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/recommendations/similar/<int:course_id>', methods=['GET'])
    def similar_courses(course_id):
        """Get similar courses to a specific course"""
        try:
            similar = app.recommender.recommend_based_on_course(course_id)
            return jsonify(similar)
        except Exception as e:
            logger.error(f"Error finding similar courses: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for deployment"""
        return jsonify({"status": "healthy", "service": "AI Course Advisor"}), 200
