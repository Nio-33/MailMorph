"""
Security Utilities
Handles input validation, sanitization, and security checks
"""

import re
import hashlib
import secrets
from typing import Dict, Any, Union
from urllib.parse import urlparse
import bleach


class SecurityValidator:
    """Handles security validation and sanitization"""

    def __init__(self):
        """Initialize security validator with default settings"""
        # Domain validation regex (RFC compliant)
        self.domain_regex = re.compile(
            r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
            r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        )

        # Email validation regex
        self.email_regex = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

        # Allowed HTML tags for sanitization (very restrictive)
        self.allowed_tags = []  # No HTML tags allowed
        self.allowed_attributes = {}

    def validate_domain(self, domain: str) -> Dict[str, Any]:
        """
        Validate domain format and security

        Args:
            domain: Domain string to validate

        Returns:
            Dictionary with validation results
        """
        if not domain:
            return {"valid": False, "error": "Domain cannot be empty"}

        # Remove whitespace
        domain = domain.strip()

        # Check length
        if len(domain) > 253:
            return {"valid": False, "error": "Domain too long (max 253 characters)"}

        if len(domain) < 1:
            return {"valid": False, "error": "Domain too short"}

        # Check for invalid characters
        if not self.domain_regex.match(domain):
            return {"valid": False, "error": "Invalid domain format"}

        # Check for security issues
        security_check = self._check_domain_security(domain)
        if not security_check["safe"]:
            return {"valid": False, "error": security_check["reason"]}

        return {
            "valid": True,
            "domain": domain,
            "tld": domain.split(".")[-1] if "." in domain else None,
            "subdomain_count": (
                len(domain.split(".")) - 2 if domain.count(".") > 1 else 0
            ),
        }

    def validate_email(self, email: str) -> Dict[str, Any]:
        """
        Validate email format

        Args:
            email: Email string to validate

        Returns:
            Dictionary with validation results
        """
        if not email:
            return {"valid": False, "error": "Email cannot be empty"}

        # Remove whitespace
        email = email.strip()

        # Check length
        if len(email) > 254:
            return {"valid": False, "error": "Email too long (max 254 characters)"}

        # Basic format validation
        if not self.email_regex.match(email):
            return {"valid": False, "error": "Invalid email format"}

        # Split into local and domain parts
        try:
            local, domain = email.rsplit("@", 1)
        except ValueError:
            return {"valid": False, "error": "Invalid email format"}

        # Validate domain part
        domain_validation = self.validate_domain(domain)
        if not domain_validation["valid"]:
            return {
                "valid": False,
                "error": f'Invalid domain: {domain_validation["error"]}',
            }

        # Validate local part
        if len(local) > 64:
            return {
                "valid": False,
                "error": "Email local part too long (max 64 characters)",
            }

        return {"valid": True, "email": email, "local": local, "domain": domain}

    def sanitize_input(self, input_text: str, max_length: int = 1000) -> str:
        """
        Sanitize user input by removing potentially dangerous content

        Args:
            input_text: Input text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        if not input_text:
            return ""

        # Convert to string and limit length
        text = str(input_text)[:max_length]

        # Remove HTML tags and dangerous content
        text = bleach.clean(
            text, tags=self.allowed_tags, attributes=self.allowed_attributes
        )

        # Remove null bytes and control characters
        text = "".join(char for char in text if ord(char) >= 32 or char in "\t\n\r")

        # Strip whitespace
        text = text.strip()

        return text

    def validate_filename(self, filename: str) -> Dict[str, Any]:
        """
        Validate uploaded filename for security

        Args:
            filename: Filename to validate

        Returns:
            Dictionary with validation results
        """
        if not filename:
            return {"valid": False, "error": "Filename cannot be empty"}

        # Check for dangerous patterns
        dangerous_patterns = [
            "../",  # Directory traversal
            "..\\",  # Windows directory traversal
            "..",  # Any parent directory reference
            "/",  # Absolute path
            "\\",  # Windows path separator
            ":",  # Windows drive separator
            "|",  # Pipe character
            "<",  # Input redirection
            ">",  # Output redirection
            "*",  # Wildcard
            "?",  # Wildcard
            '"',  # Quote
            "\0",  # Null byte
        ]

        for pattern in dangerous_patterns:
            if pattern in filename:
                return {
                    "valid": False,
                    "error": f"Filename contains dangerous character: {pattern}",
                }

        # Check length
        if len(filename) > 255:
            return {"valid": False, "error": "Filename too long (max 255 characters)"}

        # Check for reserved names (Windows)
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]

        name_without_ext = filename.split(".")[0].upper()
        if name_without_ext in reserved_names:
            return {
                "valid": False,
                "error": f"Filename uses reserved name: {name_without_ext}",
            }

        return {"valid": True, "filename": filename}

    def check_file_content_safety(
        self, filepath: str, max_size: int = 16777216
    ) -> Dict[str, Any]:
        """
        Check file content for potential security issues

        Args:
            filepath: Path to file to check
            max_size: Maximum allowed file size in bytes

        Returns:
            Dictionary with safety check results
        """
        try:
            import os

            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size > max_size:
                return {
                    "safe": False,
                    "reason": (
                        f"File size ({file_size:,} bytes) exceeds maximum "
                        f"({max_size:,} bytes)"
                    ),
                }

            # Check if file is empty
            if file_size == 0:
                return {"safe": False, "reason": "File is empty"}

            # Read first chunk to check for binary content
            with open(filepath, "rb") as f:
                chunk = f.read(1024)

            # Check for null bytes (indicates binary file)
            if b"\x00" in chunk:
                return {
                    "safe": False,
                    "reason": "File appears to be binary (contains null bytes)",
                }

            # Check for suspicious patterns in text files
            try:
                text_content = chunk.decode("utf-8", errors="ignore")
                suspicious_patterns = [
                    "<script",  # JavaScript
                    "<?php",  # PHP code
                    "<%",  # ASP/JSP code
                    "eval(",  # Code evaluation
                    "exec(",  # Code execution
                    "system(",  # System commands
                    "__import__",  # Python imports
                ]

                text_lower = text_content.lower()
                for pattern in suspicious_patterns:
                    if pattern in text_lower:
                        return {
                            "safe": False,
                            "reason": f"File contains suspicious pattern: {pattern}",
                        }

            except UnicodeDecodeError:
                # If we can't decode as UTF-8, it might be binary
                return {"safe": False, "reason": "File encoding is not UTF-8"}

            return {"safe": True, "file_size": file_size, "content_type": "text"}

        except Exception as e:
            return {"safe": False, "reason": f"Error checking file: {str(e)}"}

    def _check_domain_security(self, domain: str) -> Dict[str, Any]:
        """
        Check domain for security issues

        Args:
            domain: Domain to check

        Returns:
            Dictionary with security check results
        """
        domain_lower = domain.lower()

        # Check for suspicious patterns
        suspicious_patterns = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "192.168.",
            "10.",
            "172.16.",
            "example.com",
            "test.com",
            ".local",
            "xn--",  # Punycode (internationalized domains)
        ]

        for pattern in suspicious_patterns:
            if pattern in domain_lower:
                return {
                    "safe": False,
                    "reason": f"Domain contains suspicious pattern: {pattern}",
                }

        # Check for excessive subdomains (potential DGA)
        if domain.count(".") > 5:
            return {
                "safe": False,
                "reason": "Domain has too many subdomains (possible DGA)",
            }

        # Check for suspicious TLDs
        suspicious_tlds = [
            ".tk",
            ".ml",
            ".ga",
            ".cf",  # Free TLDs often used for malicious purposes
        ]

        for tld in suspicious_tlds:
            if domain_lower.endswith(tld):
                return {"safe": False, "reason": f"Domain uses suspicious TLD: {tld}"}

        return {"safe": True}

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure random token

        Args:
            length: Length of token in bytes

        Returns:
            Hex-encoded secure token
        """
        return secrets.token_hex(length)

    def hash_content(self, content: Union[str, bytes]) -> str:
        """
        Generate SHA-256 hash of content

        Args:
            content: Content to hash

        Returns:
            Hex-encoded hash
        """
        if isinstance(content, str):
            content = content.encode("utf-8")

        return hashlib.sha256(content).hexdigest()

    def rate_limit_check(
        self, identifier: str, max_requests: int = 10, time_window: int = 60
    ) -> Dict[str, Any]:
        """
        Simple in-memory rate limiting check

        Args:
            identifier: Unique identifier (IP, user, etc.)
            max_requests: Maximum requests allowed
            time_window: Time window in seconds

        Returns:
            Dictionary with rate limit results
        """
        # This is a simple implementation - in production, use Redis or similar
        import time

        if not hasattr(self, "_rate_limit_store"):
            self._rate_limit_store = {}

        current_time = time.time()

        if identifier not in self._rate_limit_store:
            self._rate_limit_store[identifier] = []

        # Clean old entries
        self._rate_limit_store[identifier] = [
            timestamp
            for timestamp in self._rate_limit_store[identifier]
            if current_time - timestamp < time_window
        ]

        # Check if limit exceeded
        if len(self._rate_limit_store[identifier]) >= max_requests:
            return {
                "allowed": False,
                "requests_made": len(self._rate_limit_store[identifier]),
                "max_requests": max_requests,
                "reset_time": min(self._rate_limit_store[identifier]) + time_window,
            }

        # Add current request
        self._rate_limit_store[identifier].append(current_time)

        return {
            "allowed": True,
            "requests_made": len(self._rate_limit_store[identifier]),
            "max_requests": max_requests,
            "remaining": max_requests - len(self._rate_limit_store[identifier]),
        }


# Utility functions
def validate_csv_content_security(filepath: str) -> Dict[str, Any]:
    """
    Validate CSV file content for security issues

    Args:
        filepath: Path to CSV file

    Returns:
        Dictionary with validation results
    """
    validator = SecurityValidator()
    return validator.check_file_content_safety(filepath)


def sanitize_domain_input(domain: str) -> str:
    """
    Sanitize domain input

    Args:
        domain: Domain string to sanitize

    Returns:
        Sanitized domain string
    """
    if not domain:
        return ""

    # Remove whitespace and convert to lowercase
    domain = domain.strip().lower()

    # Remove protocol if present
    if domain.startswith(("http://", "https://")):
        domain = urlparse(f"http://{domain}").netloc

    # Remove www. prefix if present
    if domain.startswith("www."):
        domain = domain[4:]

    return domain
