"""
MailMorph - Email Domain Replacer Tool
Main Flask Application (Refactored)
"""

import logging
import os

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

# Import our modular components
from config import get_config, setup_logging
from src.processors.csv_validator import CSVValidator
from src.processors.domain_replacer import DomainReplacer
from src.utils.file_handler import FileHandler, is_allowed_file_type
from src.utils.security import SecurityValidator, sanitize_domain_input

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config = get_config()
app.config.from_object(config)

# Setup logging
setup_logging(config)
logger = logging.getLogger(__name__)

# Initialize components
file_handler = FileHandler(
    upload_folder=config.UPLOAD_FOLDER,
    max_file_age=config.MAX_FILE_AGE,
    cleanup_interval=config.CLEANUP_INTERVAL,
)

domain_replacer = DomainReplacer(max_rows_limit=config.MAX_ROWS_LIMIT)
csv_validator = CSVValidator(
    max_rows_limit=config.MAX_ROWS_LIMIT, max_file_size=config.MAX_CONTENT_LENGTH
)
security_validator = SecurityValidator()

logger.info(f"MailMorph application initialized with {config.__class__.__name__}")


@app.route("/")
def index():
    """Main upload page"""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload and domain replacement"""
    try:
        # Check if file was uploaded
        if "file" not in request.files:
            flash("No file selected", "error")
            return redirect(url_for("index"))

        file = request.files["file"]
        old_domain = sanitize_domain_input(request.form.get("old_domain", ""))
        new_domain = sanitize_domain_input(request.form.get("new_domain", ""))

        # Validate inputs
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(url_for("index"))

        if not old_domain or not new_domain:
            flash("Both old and new domains are required", "error")
            return redirect(url_for("index"))

        # Validate domains using security validator
        old_domain_validation = security_validator.validate_domain(old_domain)
        new_domain_validation = security_validator.validate_domain(new_domain)

        if not old_domain_validation["valid"]:
            flash(f'Invalid old domain: {old_domain_validation["error"]}', "error")
            return redirect(url_for("index"))

        if not new_domain_validation["valid"]:
            flash(f'Invalid new domain: {new_domain_validation["error"]}', "error")
            return redirect(url_for("index"))

        if old_domain.lower() == new_domain.lower():
            flash("Old and new domains cannot be the same", "error")
            return redirect(url_for("index"))

        # Check file extension
        if not is_allowed_file_type(file.filename, config.ALLOWED_EXTENSIONS):
            flash("Invalid file type. Only CSV and TXT files are allowed.", "error")
            return redirect(url_for("index"))

        # Validate filename security
        filename_validation = security_validator.validate_filename(file.filename)
        if not filename_validation["valid"]:
            flash(f'Invalid filename: {filename_validation["error"]}', "error")
            return redirect(url_for("index"))

        # Save uploaded file
        save_result = file_handler.save_uploaded_file(file, file.filename)
        if not save_result["success"]:
            flash(save_result["error"], "error")
            return redirect(url_for("index"))

        filepath = save_result["filepath"]
        filename = save_result["filename"]

        try:
            # Validate file structure
            validation_result = csv_validator.validate_file_structure(filepath)
            if not validation_result["valid"]:
                flash(validation_result["error"], "error")
                return redirect(url_for("index"))

            # Check file content security
            security_check = security_validator.check_file_content_safety(
                filepath, config.MAX_CONTENT_LENGTH
            )
            if not security_check["safe"]:
                flash(
                    f'File security check failed: {security_check["reason"]}', "error"
                )
                return redirect(url_for("index"))

            # Analyze email content to verify target domain exists
            email_analysis = csv_validator.analyze_email_content(filepath, old_domain)
            if email_analysis["success"] and not email_analysis["target_domain_found"]:
                flash(
                    f'No emails found with domain "{old_domain}" in the uploaded file',
                    "warning",
                )
                # Continue processing anyway, in case user wants to proceed

            # Process the file
            result = domain_replacer.replace_domains(
                filepath, old_domain, new_domain, config.UPLOAD_FOLDER
            )

            if result["success"]:
                logger.info(
                    f"Successfully processed file: {filename}, "
                    f"replaced {result['changes_made']} occurrences of "
                    f"{old_domain} with {new_domain}"
                )
                return render_template("result.html", result=result)
            else:
                flash(result["error"], "error")
                return redirect(url_for("index"))

        finally:
            # Clean up uploaded file
            file_handler.delete_file(filename)

    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/download/<filename>")
def download_file(filename):
    """Download processed file"""
    try:
        # Validate filename security
        filename_validation = security_validator.validate_filename(filename)
        if not filename_validation["valid"]:
            flash("Invalid filename", "error")
            return redirect(url_for("index"))

        if file_handler.file_exists(filename):
            filepath = os.path.join(config.UPLOAD_FOLDER, filename)
            logger.info(f"File downloaded: {filename}")
            return send_file(filepath, as_attachment=True)
        else:
            flash("File not found or has expired", "error")
            return redirect(url_for("index"))

    except Exception as e:
        logger.error(f"Error in download_file: {str(e)}", exc_info=True)
        flash(f"Error downloading file: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/api/validate", methods=["POST"])
def validate_domains():
    """API endpoint for domain validation"""
    try:
        data = request.get_json()
        old_domain = sanitize_domain_input(data.get("old_domain", ""))
        new_domain = sanitize_domain_input(data.get("new_domain", ""))

        old_validation = security_validator.validate_domain(old_domain)
        new_validation = security_validator.validate_domain(new_domain)

        return jsonify(
            {
                "old_domain_valid": old_validation["valid"],
                "new_domain_valid": new_validation["valid"],
                "domains_different": (
                    old_domain.lower() != new_domain.lower()
                    if old_domain and new_domain
                    else True
                ),
                "old_domain_error": old_validation.get("error"),
                "new_domain_error": new_validation.get("error"),
            }
        )

    except Exception as e:
        logger.error(f"Error in validate_domains: {str(e)}", exc_info=True)
        return jsonify({"error": "Validation failed"}), 500


@app.route("/api/preview", methods=["POST"])
def preview_changes():
    """API endpoint for previewing changes (new feature)"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        old_domain = sanitize_domain_input(request.form.get("old_domain", ""))
        new_domain = sanitize_domain_input(request.form.get("new_domain", ""))

        if not old_domain or not new_domain:
            return jsonify({"success": False, "error": "Both domains required"}), 400

        # Save temporary file
        save_result = file_handler.save_uploaded_file(file, file.filename)
        if not save_result["success"]:
            return jsonify({"success": False, "error": save_result["error"]}), 400

        try:
            # Get preview
            preview_result = domain_replacer.preview_changes(
                save_result["filepath"], old_domain, new_domain
            )
            return jsonify(preview_result)

        finally:
            # Clean up temp file
            file_handler.delete_file(save_result["filename"])

    except Exception as e:
        logger.error(f"Error in preview_changes: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Preview failed"}), 500


@app.route("/api/stats")
def get_stats():
    """API endpoint for application statistics"""
    try:
        stats = file_handler.get_directory_stats()
        stats.update({"config": config.get_summary(), "version": "1.0.0"})
        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}", exc_info=True)
        return jsonify({"error": "Stats unavailable"}), 500


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    max_size_mb = config.MAX_CONTENT_LENGTH // (1024 * 1024)
    flash(f"File is too large. Maximum size is {max_size_mb}MB.", "error")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template("index.html"), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(e)}", exc_info=True)
    flash("An internal server error occurred. Please try again.", "error")
    return redirect(url_for("index"))


# Development server startup
if __name__ == "__main__":
    # Validate configuration on startup
    validation = config.validate_config()
    if not validation["valid"]:
        logger.error("Configuration validation failed:")
        for error in validation["errors"]:
            logger.error(f"  - {error}")
        for warning in validation["warnings"]:
            logger.warning(f"  - {warning}")

    # Log startup info
    logger.info("🚀 Starting MailMorph Development Server...")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    logger.info(f"🐍 Python version: {__import__('sys').version}")
    logger.info("=" * 50)
    logger.info("📧 MailMorph - Email Domain Replacer Tool")
    logger.info("🌐 Access the application at: http://localhost:5001")
    logger.info(f"🔧 Debug mode: {'ON' if config.DEBUG else 'OFF'}")
    logger.info("=" * 50)
    logger.info("Press Ctrl+C to stop the server")

    # Run development server
    app.run(host="0.0.0.0", port=5001, debug=config.DEBUG, use_reloader=config.DEBUG)
