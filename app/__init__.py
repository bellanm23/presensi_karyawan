# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail  # Pastikan ini diimpor
from config import Config

# Inisialisasi objek
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()

def create_app():
    app = Flask(__name__)
    mail = Mail(app)  # Inisialisasi Flask-Mail dengan aplikasi
    app.config.from_object(Config)
    

    # Inisialisasi db, migrate, login_manager, bcrypt
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    mail.init_app(app)

    @app.context_processor
    def utility_processor():
        from app.models import AttendanceStatus  # Impor di dalam fungsi
        from app.utils import get_attendance_for_today
        return dict(get_attendance_for_today=get_attendance_for_today, AttendanceStatus=AttendanceStatus)

    # User loader function
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User  # Lazy import untuk menghindari circular import
        return User.query.get(int(user_id))

    # Daftarkan blueprint
    from .routes.employee_routes import home_bp, employee_bp
    app.register_blueprint(home_bp)
    app.register_blueprint(employee_bp, url_prefix='/employee')

    from .routes.user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin_dashboard')

    from .routes.attendance_routes import attendance_bp
    app.register_blueprint(attendance_bp, url_prefix='/attendance')

    return app