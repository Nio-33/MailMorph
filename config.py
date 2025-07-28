"""
Configuration Management for MailMorph
Handles environment variables and application settings
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration class"""

    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes", "on")

    # File upload settings
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16777216))  # 16MB
    ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "csv,txt").split(","))

    # File management
    CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", 3600))  # 1 hour
    MAX_FILE_AGE = int(os.getenv("MAX_FILE_AGE", 1800))  # 30 minutes
    MAX_ROWS_LIMIT = int(os.getenv("MAX_ROWS_LIMIT", 100000))  # 100k rows

    # Security settings
    DOMAIN_VALIDATION_ENABLED = os.getenv(
        "DOMAIN_VALIDATION_ENABLED", "True"
    ).lower() in ("true", "1", "yes", "on")
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "False").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", 10))

    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = os.getenv("LOG_FILE", "logs/mailmorph.log")
    LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))

    # Performance settings
    ENABLE_GZIP = os.getenv("ENABLE_GZIP", "True").lower() in ("true", "1", "yes", "on")
    CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", 300))  # 5 minutes

    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """
        Validate configuration settings

        Returns:
            Dictionary with validation results and any errors
        """
        errors = []
        warnings = []

        # Validate required settings
        if (
            not cls.SECRET_KEY
            or cls.SECRET_KEY == "dev-secret-key-change-in-production"
        ):
            if not cls.DEBUG:
                errors.append("SECRET_KEY must be set for production use")
            else:
                warnings.append("Using default SECRET_KEY in debug mode")

        # Validate file size limits
        if cls.MAX_CONTENT_LENGTH < 1024:  # Less than 1KB
            warnings.append("MAX_CONTENT_LENGTH is very small (< 1KB)")
        elif cls.MAX_CONTENT_LENGTH > 104857600:  # Greater than 100MB
            warnings.append("MAX_CONTENT_LENGTH is very large (> 100MB)")

        # Validate row limits
        if cls.MAX_ROWS_LIMIT < 1:
            errors.append("MAX_ROWS_LIMIT must be greater than 0")
        elif cls.MAX_ROWS_LIMIT > 1000000:  # 1 million rows
            warnings.append("MAX_ROWS_LIMIT is very large (> 1M rows)")

        # Validate file age settings
        if cls.MAX_FILE_AGE < 60:  # Less than 1 minute
            warnings.append("MAX_FILE_AGE is very short (< 1 minute)")
        elif cls.MAX_FILE_AGE > 86400:  # More than 1 day
            warnings.append("MAX_FILE_AGE is very long (> 1 day)")

        # Validate cleanup interval
        if cls.CLEANUP_INTERVAL < 60:  # Less than 1 minute
            warnings.append("CLEANUP_INTERVAL is very short (< 1 minute)")

        # Validate allowed extensions
        if not cls.ALLOWED_EXTENSIONS:
            errors.append("ALLOWED_EXTENSIONS cannot be empty")

        # Validate upload folder
        if not cls.UPLOAD_FOLDER:
            errors.append("UPLOAD_FOLDER cannot be empty")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """
        Get a summary of current configuration

        Returns:
            Dictionary with configuration summary
        """
        return {
            "flask": {
                "debug": cls.DEBUG,
                "secret_key_set": bool(
                    cls.SECRET_KEY
                    and cls.SECRET_KEY != "dev-secret-key-change-in-production"
                ),
            },
            "file_handling": {
                "upload_folder": cls.UPLOAD_FOLDER,
                "max_file_size": f"{cls.MAX_CONTENT_LENGTH:,} bytes",
                "allowed_extensions": list(cls.ALLOWED_EXTENSIONS),
                "max_rows": f"{cls.MAX_ROWS_LIMIT:,}",
                "file_retention": f"{cls.MAX_FILE_AGE} seconds",
                "cleanup_interval": f"{cls.CLEANUP_INTERVAL} seconds",
            },
            "security": {
                "domain_validation": cls.DOMAIN_VALIDATION_ENABLED,
                "rate_limiting": cls.RATE_LIMIT_ENABLED,
                "max_requests_per_minute": cls.MAX_REQUESTS_PER_MINUTE,
            },
            "logging": {
                "level": cls.LOG_LEVEL,
                "file": cls.LOG_FILE,
                "max_size": f"{cls.LOG_MAX_SIZE:,} bytes",
                "backup_count": cls.LOG_BACKUP_COUNT,
            },
            "performance": {
                "gzip_enabled": cls.ENABLE_GZIP,
                "cache_timeout": f"{cls.CACHE_TIMEOUT} seconds",
            },
        }


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-for-development-only")
    LOG_LEVEL = "DEBUG"

    # More permissive settings for development
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 52428800))  # 50MB
    MAX_ROWS_LIMIT = int(os.getenv("MAX_ROWS_LIMIT", 500000))  # 500k rows


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False

    # More restrictive settings for production
    RATE_LIMIT_ENABLED = True
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", 5))

    # Security headers
    SECURE_HEADERS = True

    @classmethod
    def validate_production_config(cls) -> Dict[str, Any]:
        """
        Additional validation for production environment

        Returns:
            Dictionary with production-specific validation results
        """
        base_validation = cls.validate_config()
        errors = base_validation["errors"][:]
        warnings = base_validation["warnings"][:]

        # Production-specific checks
        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            errors.append("SECRET_KEY must be changed for production")

        if len(cls.SECRET_KEY) < 32:
            warnings.append("SECRET_KEY should be at least 32 characters long")

        if cls.DEBUG:
            errors.append("DEBUG should be False in production")

        if not cls.RATE_LIMIT_ENABLED:
            warnings.append("Rate limiting should be enabled in production")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    DEBUG = True
    SECRET_KEY = "test-secret-key"

    # Use temporary directories for testing
    UPLOAD_FOLDER = "test_uploads"
    LOG_FILE = "test_logs/mailmorph_test.log"

    # Faster cleanup for testing
    MAX_FILE_AGE = 60  # 1 minute
    CLEANUP_INTERVAL = 30  # 30 seconds

    # Smaller limits for faster tests
    MAX_CONTENT_LENGTH = 1048576  # 1MB
    MAX_ROWS_LIMIT = 1000


# Configuration factory
def get_config(config_name: Optional[str] = None) -> Config:
    """
    Get configuration class based on environment

    Args:
        config_name: Configuration name ('development', 'production', 'testing')

    Returns:
        Configuration class instance
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }

    return config_map.get(config_name, DevelopmentConfig)


# Utility functions
def setup_logging(config: Config) -> None:
    """
    Setup logging configuration

    Args:
        config: Configuration object
    """
    import logging
    from logging.handlers import RotatingFileHandler
    import os

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            RotatingFileHandler(
                config.LOG_FILE,
                maxBytes=config.LOG_MAX_SIZE,
                backupCount=config.LOG_BACKUP_COUNT,
            ),
            logging.StreamHandler(),
        ],
    )


def validate_environment() -> Dict[str, Any]:
    """
    Validate the current environment setup

    Returns:
        Dictionary with environment validation results
    """
    config = get_config()
    validation = config.validate_config()

    # Check if required directories exist
    upload_folder_exists = os.path.exists(config.UPLOAD_FOLDER)

    # Check write permissions
    upload_folder_writable = False
    if upload_folder_exists:
        try:
            test_file = os.path.join(config.UPLOAD_FOLDER, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            upload_folder_writable = True
        except Exception:
            pass

    validation.update(
        {
            "upload_folder_exists": upload_folder_exists,
            "upload_folder_writable": upload_folder_writable,
            "config_class": config.__class__.__name__,
        }
    )

    return validation
