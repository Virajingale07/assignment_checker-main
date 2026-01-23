import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail  #

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()  #


def create_app():
    app = Flask(__name__)

    app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_fallback')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///assignment_system.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # BREVO PORT 587 CONFIGURATION
    app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True  # MUST be True for 587
    app.config['MAIL_USE_SSL'] = False  # MUST be False for 587

    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)  #

    with app.app_context():
        from app.routes import routes
        app.register_blueprint(routes)

    return app