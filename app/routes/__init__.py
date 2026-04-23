"""
Route registration — every Blueprint is imported and registered here.
Adding a new domain = create a new blueprint file + one line below.
Open/Closed Principle: extend without modifying this file's logic.
"""

from flask import Flask


def register_routes(app: Flask) -> None:
    from app.routes.main    import bp as main_bp
    from app.routes.chat    import bp as chat_bp
    from app.routes.resume  import bp as resume_bp
    from app.routes.courses import bp as courses_bp
    from app.routes.journey import bp as journey_bp
    from app.routes.health  import bp as health_bp
    from app.routes.admin   import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(journey_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)
