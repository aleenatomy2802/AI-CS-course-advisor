"""
Application configuration — all settings in one place.
Each environment gets its own class (SRP).
"""

import os


def _get_database_url():
    """Resolve the database URL from environment or fall back to local SQLite."""
    url = os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        # Railway / Render inject postgres://, SQLAlchemy needs postgresql://
        url = url.replace('postgres://', 'postgresql://', 1)
    if not url:
        base = os.path.abspath(os.path.dirname(__file__))
        instance = os.path.join(base, 'instance')
        os.makedirs(instance, exist_ok=True)
        url = f'sqlite:///{os.path.join(instance, "courses.db")}'
    return url


class Config:
    """Base config — shared across all environments."""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,   # Detect dropped connections (Neon idle timeout)
        'pool_recycle': 280,     # Recycle before Neon's 300s timeout
    }

    @classmethod
    def validate(cls):
        if not os.environ.get('SECRET_KEY'):
            raise RuntimeError("SECRET_KEY environment variable is not set.")

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return _get_database_url()

    @property
    def SECRET_KEY(self):
        return os.environ.get('SECRET_KEY')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Map name → class for use in create_app()
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
