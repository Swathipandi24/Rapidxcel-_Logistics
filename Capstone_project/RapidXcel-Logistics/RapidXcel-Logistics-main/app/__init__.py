# app/__init__.py

from flask import Flask
from app.config import Config
from app.extensions import db, migrate, login_manager, mail
from app.models import User  # Import the User model

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db, directory='migrations')
    login_manager.init_app(app)

    # Set the login view for @login_required
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.routes import auth_bp, inventory_bp, order_bp, courier_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(courier_bp)

    mail.init_app(app)

    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
