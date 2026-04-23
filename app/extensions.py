"""
Extensions — instantiated once here, initialised in create_app().
Importing from here avoids circular imports across the codebase.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],  # No global default — each route opts in explicitly
)
