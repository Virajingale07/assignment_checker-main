import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail  # <--- Ensure this is imported

# Initialize extensions at the top level
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()  # <--- Define mail here


def create_app():
    app = Flask(__name__)

    # 1. Configurations
    app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_fallback')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///assignment_system.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 2. UPDATED SMTP CONFIG FOR BREVO (SSL Version)
    app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'
    app.config['MAIL_PORT'] = 465  # Switched to SSL port
    app.config['MAIL_USE_SSL'] = True  # Enable SSL
    app.config['MAIL_USE_TLS'] = False  # Disable TLS for port 465

    # Credentials from Render Env Variables
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

    # 3. Bind plugins
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)  # <--- Initialize mail with the app

    # 4. Register Blueprints
    with app.app_context():
        from app.routes import routes
        app.register_blueprint(routes)

    return app