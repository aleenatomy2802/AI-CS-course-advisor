import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
import logging

logger = logging.getLogger('recommender')

class CourseRecommender:
    """TF-IDF based course recommendation system"""
    
    def __init__(self, app=None):
        self.app = app
        self.similarity_matrix = None
        self.vectorizer = None
        self.courses_df = None
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app

    def train(self, courses):
        """Train the recommender model on course data"""
        try:
            data = []
            for course in courses:
                data.append({
                    'id': course.id,
                    'name': course.name,
                    'description': course.description or '',
                    'department': course.department or '',
                    'level': str(course.level or '')
                })
            
            self.courses_df = pd.DataFrame(data)
            self.courses_df['content'] = (
                self.courses_df['name'] + ' ' + 
                self.courses_df['description'] + ' ' + 
                self.courses_df['department']
            )
            
            self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf_matrix = self.vectorizer.fit_transform(self.courses_df['content'])
            self.similarity_matrix = cosine_similarity(tfidf_matrix)
            
            model_dir = os.path.join(os.path.dirname(__file__), 'model')
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, 'recommender_model.pkl')
            
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'vectorizer': self.vectorizer,
                    'similarity_matrix': self.similarity_matrix,
                    'courses_df': self.courses_df
                }, f)
            
            logger.info("Recommender model trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training recommender: {e}")
            return False
    
    def load_model(self):
        """Load trained model from file"""
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'model', 'recommender_model.pkl')
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.vectorizer = model_data['vectorizer']
                self.similarity_matrix = model_data['similarity_matrix']
                self.courses_df = model_data['courses_df']
            logger.info("Recommender model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def recommend_courses(self, interests, num_recommendations=5):
        """Recommend courses based on user interests"""
        try:
            if self.vectorizer is None or self.courses_df is None:
                return []
            
            interest_vector = self.vectorizer.transform([interests])
            similarity_scores = cosine_similarity(
                interest_vector, 
                self.vectorizer.transform(self.courses_df['content'])
            )
            
            course_indices = similarity_scores[0].argsort()[::-1][:num_recommendations]
            recommendations = []
            
            for idx in course_indices:
                course = self.courses_df.iloc[idx]
                recommendations.append({
                    'course_id': int(course['id']),
                    'course': course['name'],
                    'recommendation_score': float(similarity_scores[0][idx])
                })
            
            return recommendations
        except Exception as e:
            logger.error(f"Error recommending courses: {e}")
            return []
    
    def recommend_based_on_course(self, course_id, num_recommendations=5):
        """Recommend similar courses"""
        try:
            if self.similarity_matrix is None or self.courses_df is None:
                return []
            
            course_idx = self.courses_df[self.courses_df['id'] == course_id].index
            if len(course_idx) == 0:
                return []
            
            course_idx = course_idx[0]
            similarity_scores = self.similarity_matrix[course_idx]
            similar_indices = similarity_scores.argsort()[::-1][1:num_recommendations+1]
            
            recommendations = []
            for idx in similar_indices:
                course = self.courses_df.iloc[idx]
                recommendations.append({
                    'course_id': int(course['id']),
                    'course': course['name'],
                    'similarity_score': float(similarity_scores[idx])
                })
            
            return recommendations
        except Exception as e:
            logger.error(f"Error finding similar courses: {e}")
            return []
