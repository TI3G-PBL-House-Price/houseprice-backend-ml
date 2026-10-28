import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-secret-key-32-chars-min")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-dev-jwt-secret-key-min-32")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_DAYS", 7)))

    DB_USER = os.getenv("DB_USER", "houseprice_admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "houseprice_secret_pass")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "houseprice_db")

    # Gunakan postgresql+psycopg2://
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MODEL_PATH = os.getenv("MODEL_PATH", "models_artefacts/model.pkl")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")