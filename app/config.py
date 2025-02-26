import os
from datetime import timedelta

from flask import current_app


class Config:
    # Flask設定
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-for-development')

    # SQLAlchemy設定
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 會話設定
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # 上傳設定
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 其他應用設定
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    TESTING = False



class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False