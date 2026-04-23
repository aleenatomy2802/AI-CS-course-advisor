"""
Course recommender service — TF-IDF + cosine similarity.
Single Responsibility: course recommendation only.
"""

import os
import pickle
import logging

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger('recommender')

# Model is written to /model/ at project root (gitignored, rebuilt on deploy)
_MODEL_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')),
    'model', 'recommender_model.pkl'
)


class CourseRecommender:
    def __init__(self, app=None):
        self.app = app
        self.similarity_matrix = None
        self.vectorizer = None
        self.courses_df = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

    # ── Training ──────────────────────────────────────────────

    def train(self, courses) -> bool:
        try:
            data = [
                {
                    'id':          c.id,
                    'name':        c.name,
                    'description': c.description or '',
                    'department':  c.department or '',
                    'level':       str(c.level or ''),
                }
                for c in courses
            ]

            self.courses_df = pd.DataFrame(data)
            self.courses_df['content'] = (
                self.courses_df['name'] + ' ' +
                self.courses_df['description'] + ' ' +
                self.courses_df['department']
            )

            self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf_matrix = self.vectorizer.fit_transform(self.courses_df['content'])
            self.similarity_matrix = cosine_similarity(tfidf_matrix)

            os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
            with open(_MODEL_PATH, 'wb') as f:
                pickle.dump({
                    'vectorizer':       self.vectorizer,
                    'similarity_matrix': self.similarity_matrix,
                    'courses_df':       self.courses_df,
                }, f)

            logger.info("Recommender model trained successfully")
            return True

        except Exception as e:
            logger.error(f"Error training recommender: {e}")
            return False

    # ── Recommendations ───────────────────────────────────────

    def recommend_courses(self, interests: str, num: int = 5) -> list:
        try:
            if self.vectorizer is None or self.courses_df is None:
                return []
            interest_vec = self.vectorizer.transform([interests])
            scores = cosine_similarity(
                interest_vec,
                self.vectorizer.transform(self.courses_df['content'])
            )
            indices = scores[0].argsort()[::-1][:num]
            return [
                {
                    'course_id':           int(self.courses_df.iloc[i]['id']),
                    'course':              self.courses_df.iloc[i]['name'],
                    'recommendation_score': float(scores[0][i]),
                }
                for i in indices
            ]
        except Exception as e:
            logger.error(f"Error recommending courses: {e}")
            return []
