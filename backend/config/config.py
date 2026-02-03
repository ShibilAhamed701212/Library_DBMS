"""
config.py
---------
Application configuration management.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Base configuration class."""
    
    # Application settings
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-me-in-production')
    
    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_NAME = os.getenv('DB_NAME', 'library_db')
    DB_USER = os.getenv('DB_USER', 'app_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security settings
    PASSWORD_SALT_ROUNDS = 12
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # File upload settings
    UPLOAD_FOLDER = str(Path(__file__).parent.parent / 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Email settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@library.com')
    
    # AI settings
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    @classmethod
    def get_db_uri(cls) -> str:
        """Get database connection URI."""
        return f"mysql+mysqlconnector://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dictionary, excluding sensitive data."""
        return {
            'DEBUG': cls.DEBUG,
            'TESTING': cls.TESTING,
            'DB_HOST': cls.DB_HOST,
            'DB_PORT': cls.DB_PORT,
            'DB_NAME': cls.DB_NAME,
            'UPLOAD_FOLDER': cls.UPLOAD_FOLDER,
            'LOG_LEVEL': cls.LOG_LEVEL,
        }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DB_NAME = os.getenv('DB_NAME', 'library_dev')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG').upper()


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DB_NAME = os.getenv('TEST_DB_NAME', 'library_test')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DB_NAME = os.getenv('DB_NAME', 'library_prod')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING').upper()


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """Retrieve configuration by name."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    return config.get(config_name.lower(), config['default'])
