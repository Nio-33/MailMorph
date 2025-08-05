"""
CSV Validation Processor
Handles validation of CSV files and their content
"""

import re
from typing import Any, Dict, List

import pandas as pd


class CSVValidator:
    """Handles CSV file validation and content analysis"""

    def __init__(self, max_rows_limit: int = 100000, max_file_size: int = 16777216):
        """
        Initialize the CSV validator

        Args:
            max_rows_limit: Maximum number of rows allowed
            max_file_size: Maximum file size in bytes
        """
        self.max_rows_limit = max_rows_limit
        self.max_file_size = max_file_size

    def validate_file_structure(self, filepath: str) -> Dict[str, Any]:
        """
        Validate the basic structure and format of a CSV file

        Args:
            filepath: Path to the CSV file

        Returns:
            Dictionary containing validation results
        """
        try:
            # Check file size
            import os

            file_size = os.path.getsize(filepath)
            if file_size > self.max_file_size:
                return {
                    "valid": False,
                    "error": (
                        f"File size ({file_size:,} bytes) exceeds maximum "
                        f"allowed size ({self.max_file_size:,} bytes)"
                    ),
                }

            # Try to read the CSV file
            df = pd.read_csv(filepath)

            # Check if file is empty
            if df.empty:
                return {"valid": False, "error": "CSV file is empty"}

            # Check row count
            if len(df) > self.max_rows_limit:
                return {
                    "valid": False,
                    "error": (
                        f"File contains {len(df):,} rows, exceeding the maximum "
                        f"limit of {self.max_rows_limit:,} rows"
                    ),
                }

            # Check if there are any columns
            if len(df.columns) == 0:
                return {"valid": False, "error": "CSV file has no columns"}

            # Basic structure validation passed
            return {
                "valid": True,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "file_size": file_size,
            }

        except pd.errors.EmptyDataError:
            return {"valid": False, "error": "CSV file is empty or has no data"}
        except pd.errors.ParserError as e:
            return {
                "valid": False, 
                "error": "Invalid file format. Please ensure your file is a properly formatted CSV with consistent columns and data structure."
            }
        except Exception as e:
            return {"valid": False, "error": "Unable to validate file. Please ensure it's a properly formatted CSV or TXT file and try again."}

    def analyze_email_content(
        self, filepath: str, domain: str = None
    ) -> Dict[str, Any]:
        """
        Analyze email content in the CSV file

        Args:
            filepath: Path to the CSV file
            domain: Specific domain to search for (optional)

        Returns:
            Dictionary containing email analysis results
        """
        try:
            df = pd.read_csv(filepath)

            if df.empty:
                return {"success": False, "error": "CSV file is empty"}

            email_columns = []
            email_stats = {
                "total_emails": 0,
                "unique_emails": 0,
                "domains_found": set(),
                "target_domain_count": 0,
            }

            # Email regex pattern
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

            # Domain-specific pattern if provided
            domain_pattern = None
            if domain:
                domain_pattern = rf"\b[A-Za-z0-9._%+-]+@{re.escape(domain)}\b"

            # Analyze each column
            for col in df.columns:
                if df[col].dtype == "object":  # Only process string columns
                    col_data = df[col].astype(str)

                    # Find emails in this column
                    email_matches = col_data.str.extractall(
                        email_pattern, flags=re.IGNORECASE
                    )

                    if not email_matches.empty:
                        emails_in_col = col_data.str.findall(
                            email_pattern, flags=re.IGNORECASE
                        )
                        all_emails = [
                            email for sublist in emails_in_col for email in sublist
                        ]

                        if all_emails:
                            email_columns.append(
                                {
                                    "column": col,
                                    "email_count": len(all_emails),
                                    "unique_emails": len(set(all_emails)),
                                    "sample_emails": list(set(all_emails))[
                                        :5
                                    ],  # First 5 unique emails as sample
                                }
                            )

                            email_stats["total_emails"] += len(all_emails)
                            email_stats["unique_emails"] += len(set(all_emails))

                            # Extract domains
                            for email in all_emails:
                                domain_part = email.split("@")[1].lower()
                                email_stats["domains_found"].add(domain_part)

                            # Count target domain matches if specified
                            if domain_pattern:
                                target_matches = col_data.str.findall(
                                    domain_pattern, flags=re.IGNORECASE
                                )
                                target_count = sum(
                                    len(matches) for matches in target_matches
                                )
                                email_stats["target_domain_count"] += target_count

            # Convert set to list for JSON serialization
            email_stats["domains_found"] = sorted(list(email_stats["domains_found"]))

            return {
                "success": True,
                "email_columns": email_columns,
                "email_stats": email_stats,
                "has_emails": len(email_columns) > 0,
                "target_domain": domain,
                "target_domain_found": (
                    email_stats["target_domain_count"] > 0 if domain else None
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "error": "Unable to analyze email content. Please verify the file contains valid data.",
            }

    def validate_csv_headers(
        self, filepath: str, required_headers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Validate CSV headers against required headers

        Args:
            filepath: Path to the CSV file
            required_headers: List of required header names (optional)

        Returns:
            Dictionary containing header validation results
        """
        try:
            df = pd.read_csv(filepath, nrows=0)  # Read only headers
            headers = list(df.columns)

            result = {"valid": True, "headers": headers, "header_count": len(headers)}

            if required_headers:
                missing_headers = [h for h in required_headers if h not in headers]
                extra_headers = [h for h in headers if h not in required_headers]

                result.update(
                    {
                        "required_headers": required_headers,
                        "missing_headers": missing_headers,
                        "extra_headers": extra_headers,
                        "has_required_headers": len(missing_headers) == 0,
                    }
                )

                if missing_headers:
                    result["valid"] = False
                    result["error"] = (
                        f'Missing required headers: {", ".join(missing_headers)}'
                    )

            return result

        except Exception as e:
            return {"valid": False, "error": "Unable to validate file headers. Please ensure the CSV has proper column headers."}

    def detect_delimiter(self, filepath: str) -> Dict[str, Any]:
        """
        Detect the delimiter used in the CSV file

        Args:
            filepath: Path to the CSV file

        Returns:
            Dictionary containing delimiter detection results
        """
        try:
            import csv

            with open(filepath, "r", encoding="utf-8") as file:
                # Read first few lines
                sample = file.read(1024)
                file.seek(0)

                # Detect delimiter
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                # Verify by trying to read with detected delimiter
                test_df = pd.read_csv(filepath, delimiter=delimiter, nrows=5)

                return {
                    "success": True,
                    "delimiter": delimiter,
                    "delimiter_name": {
                        ",": "comma",
                        ";": "semicolon",
                        "\t": "tab",
                        "|": "pipe",
                    }.get(delimiter, "unknown"),
                    "sample_rows": len(test_df),
                    "sample_columns": len(test_df.columns),
                }

        except Exception as e:
            return {"success": False, "error": "Unable to detect file format. Please ensure the file uses standard CSV formatting."}
