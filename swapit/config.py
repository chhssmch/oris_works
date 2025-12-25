import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY = 'your-secret-key-here-please-change-this-in-production'

    DATABASE_HOST = 'localhost'
    DATABASE_USER = 'root'
    DATABASE_PASSWORD = ''
    DATABASE_NAME = 'swapit_db'

    SESSION_COOKIE_NAME = 'swapit_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False 

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024