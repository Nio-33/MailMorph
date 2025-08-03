"""
File Handling Utilities
Manages file operations, cleanup, and secure file handling
"""

import os
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from werkzeug.utils import secure_filename


class FileHandler:
    """Handles file operations and cleanup for MailMorph"""

    def __init__(
        self, upload_folder: str, max_file_age: int = 1800, cleanup_interval: int = 3600
    ):
        """
        Initialize the file handler

        Args:
            upload_folder: Directory for file uploads
            max_file_age: Maximum age of files in seconds (default: 30 minutes)
            cleanup_interval: Cleanup check interval in seconds (default: 1 hour)
        """
        self.upload_folder = upload_folder
        self.max_file_age = max_file_age
        self.cleanup_interval = cleanup_interval
        self._cleanup_thread = None
        self._stop_cleanup = False

        # Ensure upload directory exists
        self.ensure_upload_directory()

        # Start cleanup thread
        self.start_cleanup_thread()

    def ensure_upload_directory(self) -> None:
        """Ensure upload directory exists and is writable"""
        try:
            os.makedirs(self.upload_folder, exist_ok=True)

            # Test write permissions
            test_file = os.path.join(self.upload_folder, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)

        except Exception as e:
            raise RuntimeError(
                f"Cannot create or write to upload directory "
                f"{self.upload_folder}: {str(e)}"
            )

    def generate_secure_filename(self, original_filename: str) -> str:
        """
        Generate a secure, unique filename

        Args:
            original_filename: Original filename from upload

        Returns:
            Secure, unique filename
        """
        # Secure the filename
        safe_filename = secure_filename(original_filename)

        # Add UUID to prevent conflicts
        name, ext = os.path.splitext(safe_filename)
        unique_filename = f"{uuid.uuid4()}_{name}{ext}"

        return unique_filename

    def save_uploaded_file(self, file_obj, original_filename: str) -> Dict[str, Any]:
        """
        Save uploaded file with secure filename

        Args:
            file_obj: File object from request
            original_filename: Original filename

        Returns:
            Dictionary with file information
        """
        try:
            secure_name = self.generate_secure_filename(original_filename)
            filepath = os.path.join(self.upload_folder, secure_name)

            # Save the file
            file_obj.save(filepath)

            # Get file info
            file_size = os.path.getsize(filepath)
            created_time = datetime.now()

            return {
                "success": True,
                "filename": secure_name,
                "filepath": filepath,
                "original_name": original_filename,
                "size": file_size,
                "created_at": created_time,
            }

        except Exception as e:
            return {"success": False, "error": f"Error saving file: {str(e)}"}

    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from the upload directory

        Args:
            filename: Name of file to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = os.path.join(self.upload_folder, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception:
            return False

    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists in the upload directory

        Args:
            filename: Name of file to check

        Returns:
            True if file exists, False otherwise
        """
        filepath = os.path.join(self.upload_folder, filename)
        return os.path.exists(filepath)

    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file

        Args:
            filename: Name of file

        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        try:
            filepath = os.path.join(self.upload_folder, filename)
            if not os.path.exists(filepath):
                return None

            stat = os.stat(filepath)
            return {
                "filename": filename,
                "filepath": filepath,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "age_seconds": time.time() - stat.st_ctime,
            }

        except Exception:
            return None

    def list_files(self, include_hidden: bool = False) -> List[Dict[str, Any]]:
        """
        List all files in the upload directory

        Args:
            include_hidden: Include hidden files (starting with .)

        Returns:
            List of file information dictionaries
        """
        files = []
        try:
            for filename in os.listdir(self.upload_folder):
                if not include_hidden and filename.startswith("."):
                    continue

                file_info = self.get_file_info(filename)
                if file_info:
                    files.append(file_info)

            # Sort by creation time (newest first)
            files.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception:
            pass

        return files

    def cleanup_old_files(self) -> Dict[str, Any]:
        """
        Clean up files older than max_file_age

        Returns:
            Dictionary with cleanup statistics
        """
        deleted_count = 0
        deleted_size = 0
        errors = []

        try:
            current_time = time.time()
            cutoff_time = current_time - self.max_file_age

            for filename in os.listdir(self.upload_folder):
                filepath = os.path.join(self.upload_folder, filename)

                try:
                    # Skip directories and hidden files
                    if os.path.isdir(filepath) or filename.startswith("."):
                        continue

                    # Check file age
                    file_stat = os.stat(filepath)
                    if file_stat.st_ctime < cutoff_time:
                        file_size = file_stat.st_size
                        os.remove(filepath)
                        deleted_count += 1
                        deleted_size += file_size

                except Exception as e:
                    errors.append(f"Error deleting {filename}: {str(e)}")

            return {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_size": deleted_size,
                "errors": errors,
                "cleanup_time": datetime.now(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Cleanup failed: {str(e)}",
                "deleted_count": deleted_count,
                "deleted_size": deleted_size,
            }

    def get_directory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the upload directory

        Returns:
            Dictionary with directory statistics
        """
        try:
            files = self.list_files(include_hidden=True)
            total_size = sum(f["size"] for f in files)

            # Age categories
            now = datetime.now()
            recent_files = len(
                [f for f in files if (now - f["created_at"]).seconds < 3600]
            )  # < 1 hour
            old_files = len(
                [
                    f
                    for f in files
                    if (now - f["created_at"]).seconds > self.max_file_age
                ]
            )

            return {
                "total_files": len(files),
                "total_size": total_size,
                "recent_files": recent_files,
                "old_files": old_files,
                "directory_path": self.upload_folder,
                "max_file_age": self.max_file_age,
            }

        except Exception as e:
            return {"error": f"Error getting directory stats: {str(e)}"}

    def start_cleanup_thread(self) -> None:
        """Start the background cleanup thread"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        self._stop_cleanup = False
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker, daemon=True
        )
        self._cleanup_thread.start()

    def stop_cleanup_thread(self) -> None:
        """Stop the background cleanup thread"""
        self._stop_cleanup = True
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

    def _cleanup_worker(self) -> None:
        """Background worker for periodic cleanup"""
        while not self._stop_cleanup:
            try:
                self.cleanup_old_files()
                time.sleep(self.cleanup_interval)
            except Exception:
                # Continue running even if cleanup fails
                time.sleep(self.cleanup_interval)

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_cleanup_thread()


# Utility functions for file operations
def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()


def is_allowed_file_type(filename: str, allowed_extensions: set) -> bool:
    """Check if file type is allowed"""
    ext = get_file_extension(filename)
    return ext.lstrip(".") in allowed_extensions


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math

    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"
