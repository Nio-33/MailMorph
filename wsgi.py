"""
WSGI Entry Point for MailMorph Production Deployment
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the Flask application after path setup
try:
    from app import app
    from config import get_config, setup_logging, validate_environment
except ImportError as e:
    print(f"Import error: {e}")
    raise

# Get production configuration
config = get_config("production")

# Setup logging for production
setup_logging(config)

# Validate environment on startup
validation = validate_environment()
if not validation["valid"]:
    import logging

    logger = logging.getLogger(__name__)
    logger.error("Environment validation failed:")
    for error in validation["errors"]:
        logger.error(f"  - {error}")
    for warning in validation["warnings"]:
        logger.warning(f"  - {warning}")

# Configure Flask app for production
app.config.from_object(config)

# Ensure upload directory exists
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

if __name__ == "__main__":
    # This is used when running with gunicorn
    # gunicorn --bind 0.0.0.0:5000 wsgi:app
    pass
