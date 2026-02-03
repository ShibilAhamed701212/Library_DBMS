"""
db.py
------
Database connection management with connection pooling and environment validation.

Features:
- Connection pooling for better performance
- Environment variable validation
- Secure defaults
- Comprehensive error handling
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Environment variables we expect (used for warnings only)
REQUIRED_ENV_VARS = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_PORT']

# Database connection pool
_connection_pool: Optional[pooling.MySQLConnectionPool] = None

def validate_environment() -> None:
    """Warn if some environment variables are missing; do not raise."""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        logger.warning("Missing DB env vars: %s. Falling back to defaults where possible.", ", ".join(missing_vars))

def get_connection_config() -> Dict[str, Any]:
    """Get database configuration from environment variables."""
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "user": os.getenv("DB_USER", "app_user"),
        # WARNING: Default password is for development only. 
        # Always set DB_PASSWORD in production via environment variables.
        "password": os.getenv("DB_PASSWORD", "App@123"),
        "database": os.getenv("DB_NAME", "library_db"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "charset": "utf8mb4",
        "use_unicode": True,
        "connect_timeout": 10,
        "auth_plugin": os.getenv("DB_AUTH_PLUGIN", "mysql_native_password"),
        # Pool configuration (extracted below)
        "pool_name": "library_pool",
        "pool_size": int(os.getenv("DB_POOL_SIZE", 5)),
        "pool_reset_session": True,
    }

def init_connection_pool() -> None:
    """Initialize the database connection pool."""
    global _connection_pool
    if _connection_pool is None:
        try:
            validate_environment()
            config = get_connection_config()
            
            # Extract pool-specific config
            pool_config = {
                'pool_name': config.pop('pool_name'),
                'pool_size': config.pop('pool_size'),
                'pool_reset_session': config.pop('pool_reset_session'),
            }
            
            _connection_pool = pooling.MySQLConnectionPool(
                **pool_config,
                **config
            )
            logger.info("Database connection pool initialized successfully")
            
        except Error as e:
            logger.error(f"Error initializing database connection pool: {e}")
            raise

def get_connection():
    """
    Get a database connection from the connection pool.
    
    Returns:
        MySQLConnection: A database connection object.
        
    Raises:
        RuntimeError: If connection pool is not initialized or connection fails.
    """
    global _connection_pool
    
    if _connection_pool is None:
        init_connection_pool()
    
    try:
        return _connection_pool.get_connection()
    except Error as e:
        logger.error(f"Error getting database connection: {e}")
        raise RuntimeError("Failed to get database connection") from e

# Do not initialize at import time; initialize lazily on first use
