import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail

# 1. Initialize extensions globally
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()


def create_app():
    app = Flask(__name__)

    # 2. Configurations
    app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_fallback')

    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///assignment_system.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 3. Brevo/SMTP Configuration
    app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

    # 4. Bind plugins to app
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # 5. Register Blueprints INSIDE app_context
    with app.app_context():
        from app.routes import routes
        app.register_blueprint(routes)

    return app