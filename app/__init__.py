import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize ONLY the extensions we are actually using
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # 1. Basic Config
    app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_fallback')

    # 2. Database Config
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///assignment_system.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 3. SMTP/API Config (We keep these keys for our API call in routes.py)
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

    # 4. Bind plugins
    db.init_app(app)
    migrate.init_app(app, db)

    # 5. Register Blueprints
    with app.app_context():
        from app.routes import routes
        app.register_blueprint(routes)

    return app