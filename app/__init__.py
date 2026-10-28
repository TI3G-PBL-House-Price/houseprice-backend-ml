from flask import Flask
from app.config import Config
from app.extensions import db, bcrypt, migrate, cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inisialisasi Ekstensi
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("ALLOWED_ORIGINS", "*")}})

    # Impor Model Basis Data (agar terdaftar di metadata SQLAlchemy & Flask-Migrate)
    with app.app_context():
        from . import models

    # Registrasi Blueprint
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.predict.routes import predict_bp
    from app.blueprints.notifications.routes import notifications_bp
    from app.blueprints.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(predict_bp, url_prefix="/api/v1/predict")
    app.register_blueprint(notifications_bp, url_prefix="/api/v1/notifications")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "ok", "message": "HousePrice API is healthy"}, 200

    return app