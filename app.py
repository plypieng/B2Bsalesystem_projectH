# app.py

from flask import Flask, redirect, url_for, render_template
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from models import db, User
from views.auth import auth_bp
from views.sales import sales_bp
from views.b2bc import b2bc_bp
from views.booking import booking_bp
from views.dashboard import dashboard_bp
from views.products import products_bp
from flask_wtf import CSRFProtect  # Import CSRFProtect if implementing later
import os

def create_app():
    app = Flask(__name__)
    
    # Determine environment
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object('config.ProductionConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    db.init_app(app)
    migrate = Migrate(app, db)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # Initialize CSRF Protection (to be implemented later)
    # csrf = CSRFProtect(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(b2bc_bp, url_prefix='/b2bc')
    app.register_blueprint(booking_bp, url_prefix='/bookings')  # Ensure this line exists
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(products_bp, url_prefix='/products')
    
    @app.route('/')
    def home():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.dashboard'))
        else:
            return redirect(url_for('auth.login'))
    
    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
