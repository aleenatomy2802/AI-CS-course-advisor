"""
API Routes for AI Course Advisor
Grounded in Texas State University CS Data
"""

from flask import render_template, request, jsonify, current_app
from models import Course
import logging

logger = logging.getLogger('routes')

def register_routes(app):
    """Register all application routes"""
    
    @app.route('/')
    def home():
        """Render the main dashboard"""
        return render_template('index.html')

    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Handle RAG-powered chat with Gemini 2.5"""
        try:
            data = request.get_json()
            message = data.get('message', '')
            user_id = data.get('user_id', 'default')
            
            if not message:
                return jsonify({"error": "Message is required"}), 400
            
            # This calls your RAG logic in ai_advisor.py
            response = app.advisor.get_response(user_id, message)
            return jsonify(response)
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return jsonify({"error": "I'm having trouble connecting to the advisor."}), 500

    @app.route('/api/analyze_resume', methods=['POST'])
    def analyze_resume():
        """Real endpoint for PDF resume analysis"""
        try:
            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No selected file"}), 400

            # Ensure you have the analyze_resume method in your AIAdvisor class
            analysis = app.advisor.analyze_resume(file)
            return jsonify({"message": analysis})
            
        except Exception as e:
            logger.error(f"Resume analysis error: {e}")
            return jsonify({"error": "Failed to analyze document"}), 500

    @app.route('/api/courses', methods=['GET'])
    def list_courses():
        """Fetch all indexed Texas State CS courses"""
        try:
            courses = Course.query.all()
            return jsonify({
                "count": len(courses),
                "courses": [course.to_dict() for course in courses]
            })
        except Exception as e:
            logger.error(f"Error listing courses: {e}")
            return jsonify({"error": "Database error"}), 500

    @app.route('/api/journey/graph', methods=['GET'])
    def get_journey_graph():
        """Data for D3.js prerequisite visualization"""
        try:
            graph_data = app.journey_map.get_course_graph_data()
            return jsonify(graph_data)
        except Exception as e:
            logger.error(f"Error getting graph: {e}")
            return jsonify({"error": "Failed to load map"}), 500

    @app.route('/api/journey/prerequisites/<int:course_id>', methods=['GET'])
    def get_prerequisites(course_id):
        """Fetch specific prerequisite chains"""
        try:
            chain_data = app.journey_map.get_prerequisite_chain(course_id)
            return jsonify(chain_data)
        except Exception as e:
            logger.error(f"Error getting prerequisites: {e}")
            return jsonify({"error": "Failed to load prerequisites"}), 500

    @app.route('/api/recommendations/courses', methods=['GET'])
    def recommend_courses():
        """TF-IDF interest matching"""
        try:
            interests = request.args.get('interests', '')
            if not interests:
                return jsonify({"error": "Interests required"}), 400
            
            recommendations = app.recommender.recommend_courses(interests)
            return jsonify(recommendations)
        except Exception as e:
            logger.error(f"Error recommending: {e}")
            return jsonify({"error": "Recommender error"}), 500

    @app.route('/health', methods=['GET'])
    def health_check():
        """Deployment status check"""
        return jsonify({"status": "healthy", "university": "Texas State"}), 200