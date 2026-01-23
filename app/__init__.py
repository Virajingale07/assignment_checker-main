import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail  # <--- Ensure this import is here

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail() # <--- 1. DEFINE MAIL HERE (Top level)

def create_app():
    app = Flask(__name__)

    # 1. Secret Key
    app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_fallback')

    # 2. Database Config
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assignment_system.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # SMTP Configuration for Brevo
    app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # Your Brevo Login Email
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # Your generated SMTP Key
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

    mail.init_app(app)
    
    # 5. Register Blueprints
    from app.routes import routes
    app.register_blueprint(routes)

    return app